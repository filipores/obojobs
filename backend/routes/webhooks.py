"""Stripe webhook handler -- public endpoint (no JWT), verifies Stripe signatures."""

import logging
from typing import Any

import stripe
from flask import Blueprint, Response, jsonify, request

from services import webhook_service
from services.stripe_service import StripeService

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint("webhooks", __name__)


def _handle_checkout_completed(session: dict[str, Any]) -> None:
    """Handle checkout.session.completed: grant credits for one-time purchase."""
    customer_id = session.get("customer")
    payment_status = session.get("payment_status")

    if not customer_id:
        logger.warning("Checkout session missing customer ID")
        return

    if payment_status != "paid":
        logger.info(f"Checkout payment_status is {payment_status}, skipping credit grant")
        return

    user = webhook_service.get_user_by_stripe_customer(customer_id)
    if not user:
        logger.error(f"No user found for Stripe customer {customer_id}")
        return

    # Get credits from session metadata
    metadata = session.get("metadata", {})
    plan = metadata.get("plan")
    credits = int(metadata.get("credits", 0)) if metadata.get("credits") else 0

    # Fall back to plan-based credit lookup
    if not credits and plan:
        credits = webhook_service.get_credits_for_plan(plan)

    if credits > 0:
        webhook_service.add_credits_to_user(user, credits)
        logger.info(f"Granted {credits} credits to user {user.id} (plan={plan})")
    else:
        logger.warning(f"No credits to grant for checkout session (plan={plan}, metadata={metadata})")


def _handle_subscription_created(subscription_data: dict[str, Any]) -> None:
    """Handle customer.subscription.created event."""
    customer_id = subscription_data.get("customer")
    subscription_id = subscription_data.get("id")

    if not customer_id:
        logger.warning("Subscription event missing customer ID")
        return

    user = webhook_service.get_user_by_stripe_customer(customer_id)
    if not user:
        logger.warning(f"No user found for Stripe customer {customer_id}")
        return

    webhook_service.upsert_subscription(user, customer_id, subscription_id, subscription_data)


def _handle_subscription_updated(subscription_data: dict[str, Any]) -> None:
    """Handle customer.subscription.updated: sync status, plan, billing period, and cancellation fields."""
    subscription_id = subscription_data.get("id")
    customer_id = subscription_data.get("customer")

    if not subscription_id:
        logger.warning("Subscription update missing subscription ID")
        return

    subscription = webhook_service.get_subscription_by_stripe_id(subscription_id)

    # Fallback: find by customer_id if subscription not found by stripe ID
    if not subscription and customer_id:
        user = webhook_service.get_user_by_stripe_customer(customer_id)
        if user:
            subscription = webhook_service.get_subscription_by_user(user.id)

    if not subscription:
        logger.warning(f"No subscription found for Stripe subscription {subscription_id}")
        return

    webhook_service.update_subscription_from_stripe(subscription, subscription_data)
    logger.info(
        f"Subscription {subscription_id} updated: status={subscription.status.value}, plan={subscription.plan.value}"
    )


def _handle_subscription_deleted(subscription_data: dict[str, Any]) -> None:
    """Handle customer.subscription.deleted: cancel and reset to free plan."""
    subscription_id = subscription_data.get("id")

    if not subscription_id:
        logger.warning("Subscription deletion missing subscription ID")
        return

    subscription = webhook_service.get_subscription_by_stripe_id(subscription_id)

    if not subscription:
        logger.warning(f"No subscription found for deleted Stripe subscription {subscription_id}")
        return

    webhook_service.cancel_subscription(subscription)
    logger.info(f"Subscription {subscription_id} deleted, user reset to free plan")


def _handle_invoice_payment_failed(invoice_data: dict[str, Any]) -> None:
    """Handle invoice.payment_failed: set subscription status to past_due."""
    subscription_id = invoice_data.get("subscription")

    if not subscription_id:
        logger.warning("Invoice payment_failed missing subscription ID")
        return

    subscription = webhook_service.get_subscription_by_stripe_id(subscription_id)

    if not subscription:
        logger.warning(f"No subscription found for invoice subscription {subscription_id}")
        return

    webhook_service.mark_subscription_past_due(subscription)
    logger.info(f"Subscription {subscription_id} marked as past_due due to payment failure")


def _handle_invoice_payment_succeeded(invoice_data: dict[str, Any]) -> None:
    """Handle invoice.payment_succeeded: confirm active status and update billing period."""
    subscription_id = invoice_data.get("subscription")

    if not subscription_id:
        logger.info("Invoice payment_succeeded without subscription (one-off invoice)")
        return

    subscription = webhook_service.get_subscription_by_stripe_id(subscription_id)

    if not subscription:
        logger.warning(f"No subscription found for invoice subscription {subscription_id}")
        return

    webhook_service.confirm_subscription_active(subscription, invoice_data)
    logger.info(f"Subscription {subscription_id} confirmed active after payment success")


@webhooks_bp.route("/stripe", methods=["POST"])
def stripe_webhook() -> tuple[Response, int]:
    """Verify signature, check idempotency, and dispatch Stripe webhook events."""
    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature")

    if not sig_header:
        logger.warning("Webhook request missing Stripe-Signature header")
        return jsonify({"success": False, "error": "Missing signature"}), 400

    try:
        stripe_service = StripeService()
        event = stripe_service.construct_webhook_event(payload, sig_header)
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {e}")
        return jsonify({"success": False, "error": "Invalid signature"}), 400
    except Exception as e:
        logger.error(f"Failed to construct webhook event: {e}")
        return jsonify({"success": False, "error": "Invalid payload"}), 400

    event_id = event.get("id", "")
    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})

    logger.info(f"Received Stripe webhook event: {event_type} ({event_id})")

    # Idempotency check: skip if already processed
    if event_id and webhook_service.check_idempotency(event_id):
        logger.info(f"Skipping already processed event {event_id}")
        return jsonify({"success": True, "received": True, "duplicate": True}), 200

    try:
        if event_type == "checkout.session.completed":
            _handle_checkout_completed(event_data)
        elif event_type == "customer.subscription.created":
            _handle_subscription_created(event_data)
        elif event_type == "customer.subscription.updated":
            _handle_subscription_updated(event_data)
        elif event_type == "customer.subscription.deleted":
            _handle_subscription_deleted(event_data)
        elif event_type == "invoice.payment_failed":
            _handle_invoice_payment_failed(event_data)
        elif event_type == "invoice.payment_succeeded":
            _handle_invoice_payment_succeeded(event_data)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")

        # Record successful processing
        if event_id:
            webhook_service.record_event(event_id, event_type, status="success")

        return jsonify({"success": True, "received": True}), 200

    except Exception as e:
        logger.error(f"Error processing webhook event {event_type}: {e}")
        webhook_service.rollback()

        # Record failed processing
        if event_id:
            try:
                webhook_service.record_event(event_id, event_type, status="failed", error_message=str(e))
            except Exception:
                logger.error(f"Failed to record webhook event error for {event_id}")

        return jsonify({"success": False, "error": "Processing failed"}), 500

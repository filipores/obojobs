"""Stripe webhook handler -- public endpoint (no JWT), verifies Stripe signatures."""

import logging
from datetime import datetime

import stripe
from flask import Blueprint, jsonify, request

from models import Subscription, SubscriptionPlan, SubscriptionStatus, User, WebhookEvent, db
from services.stripe_service import StripeService

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint("webhooks", __name__)


def _get_plan_from_price_id(price_id: str) -> SubscriptionPlan:
    """Map Stripe price ID to subscription plan."""
    from config import config

    price_to_plan = {
        config.STRIPE_PRICE_BASIC: SubscriptionPlan.basic,
        config.STRIPE_PRICE_PRO: SubscriptionPlan.pro,
    }
    return price_to_plan.get(price_id, SubscriptionPlan.free)


_STRIPE_STATUS_MAP = {
    "active": SubscriptionStatus.active,
    "canceled": SubscriptionStatus.canceled,
    "past_due": SubscriptionStatus.past_due,
    "trialing": SubscriptionStatus.trialing,
    "incomplete": SubscriptionStatus.past_due,
    "incomplete_expired": SubscriptionStatus.canceled,
    "unpaid": SubscriptionStatus.past_due,
}


def _map_stripe_status(stripe_status: str) -> SubscriptionStatus:
    """Map Stripe subscription status string to SubscriptionStatus enum."""
    return _STRIPE_STATUS_MAP.get(stripe_status, SubscriptionStatus.active)


def _check_idempotency(event_id: str) -> bool:
    """Return True if this webhook event has already been processed."""
    return WebhookEvent.query.filter_by(stripe_event_id=event_id).first() is not None


def _record_event(event_id: str, event_type: str, status: str = "success", error_message: str = None) -> None:
    """Record a webhook event for idempotency tracking."""
    event_record = WebhookEvent(
        stripe_event_id=event_id,
        event_type=event_type,
        status=status,
        error_message=error_message,
    )
    db.session.add(event_record)
    db.session.commit()


def _extract_price_id(data: dict) -> str | None:
    """Extract the first price ID from Stripe subscription item data."""
    items = data.get("items", {})
    item_list = items.get("data") if isinstance(items, dict) else None
    if item_list:
        return item_list[0].get("price", {}).get("id")
    return None


def _upsert_subscription(user: User, customer_id: str, subscription_id: str, subscription_data: dict) -> None:
    """Create or update a subscription record from Stripe subscription data."""
    price_id = _extract_price_id(subscription_data)
    plan = _get_plan_from_price_id(price_id) if price_id else SubscriptionPlan.basic
    status = _map_stripe_status(subscription_data.get("status", "active"))
    period_start = datetime.fromtimestamp(subscription_data.get("current_period_start", 0))
    period_end = datetime.fromtimestamp(subscription_data.get("current_period_end", 0))

    subscription = Subscription.query.filter_by(user_id=user.id).first()

    if subscription:
        subscription.stripe_subscription_id = subscription_id
        subscription.stripe_customer_id = customer_id
        subscription.plan = plan
        subscription.status = status
        subscription.current_period_start = period_start
        subscription.current_period_end = period_end
    else:
        subscription = Subscription(
            user_id=user.id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            plan=plan,
            status=status,
            current_period_start=period_start,
            current_period_end=period_end,
        )
        db.session.add(subscription)

    db.session.commit()
    logger.info(f"Subscription upserted for user {user.id}, plan={plan.value}")


def _handle_checkout_completed(session: dict) -> None:
    """Handle checkout.session.completed: create/update subscription after checkout."""
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")

    if not customer_id or not subscription_id:
        logger.warning("Checkout session missing customer or subscription ID")
        return

    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if not user:
        logger.error(f"No user found for Stripe customer {customer_id}")
        return

    stripe_service = StripeService()
    stripe_subscription = stripe_service.get_subscription(subscription_id)
    _upsert_subscription(user, customer_id, subscription_id, stripe_subscription)


def _handle_subscription_created(subscription_data: dict) -> None:
    """Handle customer.subscription.created event."""
    customer_id = subscription_data.get("customer")
    subscription_id = subscription_data.get("id")

    if not customer_id:
        logger.warning("Subscription event missing customer ID")
        return

    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if not user:
        logger.warning(f"No user found for Stripe customer {customer_id}")
        return

    _upsert_subscription(user, customer_id, subscription_id, subscription_data)


def _handle_subscription_updated(subscription_data: dict) -> None:
    """Handle customer.subscription.updated: sync status, plan, billing period, and cancellation fields."""
    subscription_id = subscription_data.get("id")
    customer_id = subscription_data.get("customer")

    if not subscription_id:
        logger.warning("Subscription update missing subscription ID")
        return

    subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()

    # Fallback: find by customer_id if subscription not found by stripe ID
    if not subscription and customer_id:
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            subscription = Subscription.query.filter_by(user_id=user.id).first()

    if not subscription:
        logger.warning(f"No subscription found for Stripe subscription {subscription_id}")
        return

    price_id = _extract_price_id(subscription_data)
    if price_id:
        subscription.plan = _get_plan_from_price_id(price_id)

    subscription.status = _map_stripe_status(subscription_data.get("status", "active"))
    subscription.current_period_start = datetime.fromtimestamp(subscription_data.get("current_period_start", 0))
    subscription.current_period_end = datetime.fromtimestamp(subscription_data.get("current_period_end", 0))
    subscription.cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)

    canceled_at_ts = subscription_data.get("canceled_at")
    subscription.canceled_at = datetime.fromtimestamp(canceled_at_ts) if canceled_at_ts else None

    trial_end_ts = subscription_data.get("trial_end")
    subscription.trial_end = datetime.fromtimestamp(trial_end_ts) if trial_end_ts else None

    db.session.commit()
    logger.info(
        f"Subscription {subscription_id} updated: status={subscription.status.value}, plan={subscription.plan.value}"
    )


def _handle_subscription_deleted(subscription_data: dict) -> None:
    """Handle customer.subscription.deleted: cancel and reset to free plan."""
    subscription_id = subscription_data.get("id")

    if not subscription_id:
        logger.warning("Subscription deletion missing subscription ID")
        return

    subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()

    if not subscription:
        logger.warning(f"No subscription found for deleted Stripe subscription {subscription_id}")
        return

    # Mark as canceled and reset to free plan
    subscription.status = SubscriptionStatus.canceled
    subscription.plan = SubscriptionPlan.free
    subscription.stripe_subscription_id = None
    subscription.cancel_at_period_end = False
    subscription.canceled_at = datetime.utcnow()

    db.session.commit()
    logger.info(f"Subscription {subscription_id} deleted, user reset to free plan")


def _handle_invoice_payment_failed(invoice_data: dict) -> None:
    """Handle invoice.payment_failed: set subscription status to past_due."""
    subscription_id = invoice_data.get("subscription")

    if not subscription_id:
        logger.warning("Invoice payment_failed missing subscription ID")
        return

    subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()

    if not subscription:
        logger.warning(f"No subscription found for invoice subscription {subscription_id}")
        return

    subscription.status = SubscriptionStatus.past_due

    db.session.commit()
    logger.info(f"Subscription {subscription_id} marked as past_due due to payment failure")


def _handle_invoice_payment_succeeded(invoice_data: dict) -> None:
    """Handle invoice.payment_succeeded: confirm active status and update billing period."""
    subscription_id = invoice_data.get("subscription")

    if not subscription_id:
        logger.info("Invoice payment_succeeded without subscription (one-off invoice)")
        return

    subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()

    if not subscription:
        logger.warning(f"No subscription found for invoice subscription {subscription_id}")
        return

    subscription.status = SubscriptionStatus.active

    # Update billing period from invoice lines
    lines = invoice_data.get("lines", {}).get("data", [])
    if lines:
        period = lines[0].get("period", {})
        if period.get("start"):
            subscription.current_period_start = datetime.fromtimestamp(period["start"])
        if period.get("end"):
            subscription.current_period_end = datetime.fromtimestamp(period["end"])

    db.session.commit()
    logger.info(f"Subscription {subscription_id} confirmed active after payment success")


@webhooks_bp.route("/stripe", methods=["POST"])
def stripe_webhook():
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
    if event_id and _check_idempotency(event_id):
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
            _record_event(event_id, event_type, status="success")

        return jsonify({"success": True, "received": True}), 200

    except Exception as e:
        logger.error(f"Error processing webhook event {event_type}: {e}")
        db.session.rollback()

        # Record failed processing
        if event_id:
            try:
                _record_event(event_id, event_type, status="failed", error_message=str(e))
            except Exception:
                logger.error(f"Failed to record webhook event error for {event_id}")

        return jsonify({"success": False, "error": "Processing failed"}), 500

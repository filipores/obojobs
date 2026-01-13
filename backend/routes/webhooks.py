"""
Stripe Webhook Handler

Handles incoming webhooks from Stripe for subscription events.
This endpoint must be public (no JWT auth) as Stripe sends requests directly.
"""

import logging
from datetime import datetime

import stripe
from flask import Blueprint, jsonify, request

from models import Subscription, SubscriptionPlan, SubscriptionStatus, User, db
from services.stripe_service import StripeService

logger = logging.getLogger(__name__)

webhooks_bp = Blueprint("webhooks", __name__)


def _get_plan_from_price_id(price_id: str) -> SubscriptionPlan:
    """
    Map Stripe price ID to subscription plan.

    Args:
        price_id: Stripe price ID

    Returns:
        SubscriptionPlan enum value
    """
    from config import config

    if price_id == config.STRIPE_PRICE_BASIC:
        return SubscriptionPlan.basic
    elif price_id == config.STRIPE_PRICE_PRO:
        return SubscriptionPlan.pro
    else:
        return SubscriptionPlan.free


def _map_stripe_status(stripe_status: str) -> SubscriptionStatus:
    """
    Map Stripe subscription status to our SubscriptionStatus enum.

    Args:
        stripe_status: Stripe subscription status string

    Returns:
        SubscriptionStatus enum value
    """
    status_map = {
        "active": SubscriptionStatus.active,
        "canceled": SubscriptionStatus.canceled,
        "past_due": SubscriptionStatus.past_due,
        "trialing": SubscriptionStatus.trialing,
        "incomplete": SubscriptionStatus.past_due,  # Treat incomplete as past_due
        "incomplete_expired": SubscriptionStatus.canceled,
        "unpaid": SubscriptionStatus.past_due,
    }
    return status_map.get(stripe_status, SubscriptionStatus.active)


def _handle_checkout_completed(session: dict) -> None:
    """
    Handle checkout.session.completed event.

    Creates or updates subscription after successful checkout.

    Args:
        session: Stripe checkout session object
    """
    customer_id = session.get("customer")
    subscription_id = session.get("subscription")

    if not customer_id or not subscription_id:
        logger.warning("Checkout session missing customer or subscription ID")
        return

    # Find user by stripe_customer_id
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if not user:
        logger.error(f"No user found for Stripe customer {customer_id}")
        return

    # Retrieve subscription details from Stripe
    stripe_service = StripeService()
    stripe_subscription = stripe_service.get_subscription(subscription_id)

    # Get the price ID to determine the plan
    price_id = None
    if stripe_subscription.get("items") and stripe_subscription["items"].get("data"):
        price_id = stripe_subscription["items"]["data"][0].get("price", {}).get("id")

    plan = _get_plan_from_price_id(price_id) if price_id else SubscriptionPlan.basic

    # Check if subscription already exists for this user
    subscription = Subscription.query.filter_by(user_id=user.id).first()

    if subscription:
        # Update existing subscription
        subscription.stripe_subscription_id = subscription_id
        subscription.stripe_customer_id = customer_id
        subscription.plan = plan
        subscription.status = _map_stripe_status(stripe_subscription.get("status", "active"))
        subscription.current_period_start = datetime.fromtimestamp(
            stripe_subscription.get("current_period_start", 0)
        )
        subscription.current_period_end = datetime.fromtimestamp(
            stripe_subscription.get("current_period_end", 0)
        )
        logger.info(f"Updated subscription for user {user.id} to plan {plan.value}")
    else:
        # Create new subscription
        subscription = Subscription(
            user_id=user.id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            plan=plan,
            status=_map_stripe_status(stripe_subscription.get("status", "active")),
            current_period_start=datetime.fromtimestamp(
                stripe_subscription.get("current_period_start", 0)
            ),
            current_period_end=datetime.fromtimestamp(
                stripe_subscription.get("current_period_end", 0)
            ),
        )
        db.session.add(subscription)
        logger.info(f"Created subscription for user {user.id} with plan {plan.value}")

    db.session.commit()


def _handle_subscription_created(subscription_data: dict) -> None:
    """
    Handle customer.subscription.created event.

    Args:
        subscription_data: Stripe subscription object
    """
    customer_id = subscription_data.get("customer")
    subscription_id = subscription_data.get("id")

    if not customer_id:
        logger.warning("Subscription event missing customer ID")
        return

    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if not user:
        logger.warning(f"No user found for Stripe customer {customer_id}")
        return

    # Get the price ID to determine the plan
    price_id = None
    if subscription_data.get("items") and subscription_data["items"].get("data"):
        price_id = subscription_data["items"]["data"][0].get("price", {}).get("id")

    plan = _get_plan_from_price_id(price_id) if price_id else SubscriptionPlan.basic

    # Check if subscription already exists
    subscription = Subscription.query.filter_by(user_id=user.id).first()

    if subscription:
        subscription.stripe_subscription_id = subscription_id
        subscription.plan = plan
        subscription.status = _map_stripe_status(subscription_data.get("status", "active"))
        subscription.current_period_start = datetime.fromtimestamp(
            subscription_data.get("current_period_start", 0)
        )
        subscription.current_period_end = datetime.fromtimestamp(
            subscription_data.get("current_period_end", 0)
        )
    else:
        subscription = Subscription(
            user_id=user.id,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            plan=plan,
            status=_map_stripe_status(subscription_data.get("status", "active")),
            current_period_start=datetime.fromtimestamp(
                subscription_data.get("current_period_start", 0)
            ),
            current_period_end=datetime.fromtimestamp(
                subscription_data.get("current_period_end", 0)
            ),
        )
        db.session.add(subscription)

    db.session.commit()
    logger.info(f"Subscription created/updated for user {user.id}")


def _handle_subscription_updated(subscription_data: dict) -> None:
    """
    Handle customer.subscription.updated event.

    Updates subscription status, plan changes, and billing period.

    Args:
        subscription_data: Stripe subscription object
    """
    subscription_id = subscription_data.get("id")
    customer_id = subscription_data.get("customer")

    if not subscription_id:
        logger.warning("Subscription update missing subscription ID")
        return

    # Find subscription by stripe_subscription_id
    subscription = Subscription.query.filter_by(stripe_subscription_id=subscription_id).first()

    if not subscription:
        # Try to find by customer_id if subscription not found
        if customer_id:
            user = User.query.filter_by(stripe_customer_id=customer_id).first()
            if user:
                subscription = Subscription.query.filter_by(user_id=user.id).first()

    if not subscription:
        logger.warning(f"No subscription found for Stripe subscription {subscription_id}")
        return

    # Get the price ID to determine the plan
    price_id = None
    if subscription_data.get("items") and subscription_data["items"].get("data"):
        price_id = subscription_data["items"]["data"][0].get("price", {}).get("id")

    if price_id:
        subscription.plan = _get_plan_from_price_id(price_id)

    subscription.status = _map_stripe_status(subscription_data.get("status", "active"))
    subscription.current_period_start = datetime.fromtimestamp(
        subscription_data.get("current_period_start", 0)
    )
    subscription.current_period_end = datetime.fromtimestamp(
        subscription_data.get("current_period_end", 0)
    )

    db.session.commit()
    logger.info(
        f"Subscription {subscription_id} updated: status={subscription.status.value}, "
        f"plan={subscription.plan.value}"
    )


def _handle_subscription_deleted(subscription_data: dict) -> None:
    """
    Handle customer.subscription.deleted event.

    Marks subscription as canceled and resets user to free plan.

    Args:
        subscription_data: Stripe subscription object
    """
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

    db.session.commit()
    logger.info(f"Subscription {subscription_id} deleted, user reset to free plan")


@webhooks_bp.route("/stripe", methods=["POST"])
def stripe_webhook():
    """
    Handle Stripe webhook events.

    This endpoint receives events from Stripe when subscription status changes.
    It verifies the webhook signature and processes the event accordingly.

    Supported events:
        - checkout.session.completed: New subscription created via checkout
        - customer.subscription.created: Subscription created
        - customer.subscription.updated: Subscription status/plan changed
        - customer.subscription.deleted: Subscription canceled

    Returns:
        200 OK on successful processing
        400 Bad Request if signature verification fails
        500 Internal Server Error on processing failure
    """
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

    event_type = event.get("type")
    event_data = event.get("data", {}).get("object", {})

    logger.info(f"Received Stripe webhook event: {event_type}")

    try:
        if event_type == "checkout.session.completed":
            _handle_checkout_completed(event_data)
        elif event_type == "customer.subscription.created":
            _handle_subscription_created(event_data)
        elif event_type == "customer.subscription.updated":
            _handle_subscription_updated(event_data)
        elif event_type == "customer.subscription.deleted":
            _handle_subscription_deleted(event_data)
        else:
            logger.info(f"Unhandled webhook event type: {event_type}")

        return jsonify({"success": True, "received": True}), 200

    except Exception as e:
        logger.error(f"Error processing webhook event {event_type}: {e}")
        return jsonify({"success": False, "error": "Processing failed"}), 500

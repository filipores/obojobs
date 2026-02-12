"""Service layer for Stripe webhook data access."""

from datetime import datetime
from typing import Any

from models import Subscription, SubscriptionPlan, SubscriptionStatus, User, WebhookEvent, db


def check_idempotency(event_id: str) -> bool:
    """Return True if this webhook event has already been processed."""
    return WebhookEvent.query.filter_by(stripe_event_id=event_id).first() is not None


def record_event(event_id: str, event_type: str, status: str = "success", error_message: str | None = None) -> None:
    """Record a webhook event for idempotency tracking."""
    event_record = WebhookEvent(
        stripe_event_id=event_id,
        event_type=event_type,
        status=status,
        error_message=error_message,
    )
    db.session.add(event_record)
    db.session.commit()


def get_user_by_stripe_customer(customer_id: str) -> User | None:
    """Return a user by their Stripe customer ID, or None."""
    return User.query.filter_by(stripe_customer_id=customer_id).first()


def get_subscription_by_user(user_id: int) -> Subscription | None:
    """Return a subscription by user ID, or None."""
    return Subscription.query.filter_by(user_id=user_id).first()


def get_subscription_by_stripe_id(stripe_subscription_id: str) -> Subscription | None:
    """Return a subscription by Stripe subscription ID, or None."""
    return Subscription.query.filter_by(stripe_subscription_id=stripe_subscription_id).first()


def get_plan_from_price_id(price_id: str) -> SubscriptionPlan:
    """Map Stripe price ID to subscription plan."""
    from config import config

    price_to_plan = {
        config.STRIPE_PRICE_BASIC: SubscriptionPlan.basic,
        config.STRIPE_PRICE_PRO: SubscriptionPlan.pro,
    }
    return price_to_plan.get(price_id, SubscriptionPlan.free)


def map_stripe_status(stripe_status: str) -> SubscriptionStatus:
    """Map Stripe subscription status string to SubscriptionStatus enum."""
    status_map = {
        "active": SubscriptionStatus.active,
        "canceled": SubscriptionStatus.canceled,
        "past_due": SubscriptionStatus.past_due,
        "trialing": SubscriptionStatus.trialing,
        "incomplete": SubscriptionStatus.past_due,
        "incomplete_expired": SubscriptionStatus.canceled,
        "unpaid": SubscriptionStatus.past_due,
    }
    return status_map.get(stripe_status, SubscriptionStatus.active)


def upsert_subscription(
    user: User, customer_id: str, subscription_id: str, subscription_data: dict[str, Any]
) -> Subscription:
    """Create or update a subscription record from Stripe subscription data."""
    price_id = _extract_price_id(subscription_data)
    plan = get_plan_from_price_id(price_id) if price_id else SubscriptionPlan.basic
    status = map_stripe_status(subscription_data.get("status", "active"))
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
    return subscription


def update_subscription_from_stripe(subscription: Subscription, subscription_data: dict[str, Any]) -> None:
    """Update an existing subscription with data from Stripe."""
    price_id = _extract_price_id(subscription_data)
    if price_id:
        subscription.plan = get_plan_from_price_id(price_id)

    subscription.status = map_stripe_status(subscription_data.get("status", "active"))
    subscription.current_period_start = datetime.fromtimestamp(subscription_data.get("current_period_start", 0))
    subscription.current_period_end = datetime.fromtimestamp(subscription_data.get("current_period_end", 0))
    subscription.cancel_at_period_end = subscription_data.get("cancel_at_period_end", False)

    canceled_at_ts = subscription_data.get("canceled_at")
    subscription.canceled_at = datetime.fromtimestamp(canceled_at_ts) if canceled_at_ts else None

    trial_end_ts = subscription_data.get("trial_end")
    subscription.trial_end = datetime.fromtimestamp(trial_end_ts) if trial_end_ts else None

    db.session.commit()


def cancel_subscription(subscription: Subscription) -> None:
    """Mark a subscription as canceled and reset to free plan."""
    subscription.status = SubscriptionStatus.canceled
    subscription.plan = SubscriptionPlan.free
    subscription.stripe_subscription_id = None
    subscription.cancel_at_period_end = False
    subscription.canceled_at = datetime.utcnow()
    db.session.commit()


def mark_subscription_past_due(subscription: Subscription) -> None:
    """Set subscription status to past_due."""
    subscription.status = SubscriptionStatus.past_due
    db.session.commit()


def confirm_subscription_active(subscription: Subscription, invoice_data: dict[str, Any]) -> None:
    """Confirm active status and update billing period from invoice data."""
    subscription.status = SubscriptionStatus.active

    lines = invoice_data.get("lines", {}).get("data", [])
    if lines:
        period = lines[0].get("period", {})
        if period.get("start"):
            subscription.current_period_start = datetime.fromtimestamp(period["start"])
        if period.get("end"):
            subscription.current_period_end = datetime.fromtimestamp(period["end"])

    db.session.commit()


def rollback() -> None:
    """Rollback the current database session."""
    db.session.rollback()


def _extract_price_id(data: dict[str, Any]) -> str | None:
    """Extract the first price ID from Stripe subscription item data."""
    items = data.get("items", {})
    item_list = items.get("data") if isinstance(items, dict) else None
    if item_list:
        return item_list[0].get("price", {}).get("id")
    return None

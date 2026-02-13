"""Service layer for subscription data access in subscription routes."""

from datetime import datetime

from models import Subscription, User, db


def get_user(user_id: int) -> User | None:
    """Return a user by ID, or None."""
    return User.query.get(int(user_id))


def get_subscription_by_user(user_id: int) -> Subscription | None:
    """Return the subscription for a user, or None."""
    return Subscription.query.filter_by(user_id=user_id).first()


def save_stripe_customer_id(user: User, customer_id: str) -> None:
    """Save a Stripe customer ID to a user record."""
    user.stripe_customer_id = customer_id
    db.session.commit()


def mark_subscription_canceled(subscription: Subscription) -> None:
    """Mark a subscription as canceled at period end."""
    subscription.cancel_at_period_end = True
    subscription.canceled_at = datetime.utcnow()
    db.session.commit()

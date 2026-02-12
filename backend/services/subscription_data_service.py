"""Service layer for subscription data access in subscription routes."""

from models import Subscription, User, db


def get_user(user_id):
    """Return a user by ID, or None."""
    return User.query.get(int(user_id))


def get_subscription_by_user(user_id):
    """Return the subscription for a user, or None."""
    return Subscription.query.filter_by(user_id=user_id).first()


def save_stripe_customer_id(user, customer_id):
    """Save a Stripe customer ID to a user record."""
    user.stripe_customer_id = customer_id
    db.session.commit()

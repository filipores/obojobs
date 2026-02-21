"""Tests for credit-based subscription limit middleware."""

from middleware.subscription_limit import (
    add_credits,
    decrement_application_count,
    get_subscription_usage,
    increment_application_count,
    try_increment_application_count,
    FREE_CREDITS,
)
from models import User, db


class TestGetSubscriptionUsage:
    def test_free_user_usage(self, app, test_user):
        """New user gets FREE_CREDITS (10) credits."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            usage = get_subscription_usage(user)
            assert usage["plan"] == "free"
            assert usage["limit"] == FREE_CREDITS
            assert usage["used"] == 0
            assert usage["remaining"] == FREE_CREDITS
            assert usage["unlimited"] is False
            assert usage["credits_remaining"] == FREE_CREDITS

    def test_user_with_purchased_credits(self, app, test_user):
        """User who bought a starter pack has 50 extra credits."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            add_credits(user, 50)
            usage = get_subscription_usage(user)
            assert usage["credits_remaining"] == FREE_CREDITS + 50
            assert usage["remaining"] == FREE_CREDITS + 50


class TestIncrementApplicationCount:
    """Tests for the legacy increment_application_count wrapper."""

    def test_increment(self, app, test_user):
        """Each call consumes one credit."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            assert user.credits_remaining == FREE_CREDITS
            increment_application_count(user)
            assert user.credits_remaining == FREE_CREDITS - 1
            increment_application_count(user)
            assert user.credits_remaining == FREE_CREDITS - 2


class TestTryIncrementApplicationCount:
    """Tests for the atomic try_increment_application_count function."""

    def test_increment_within_limit(self, app, test_user):
        """Consuming a credit succeeds when balance > 0."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            assert user.credits_remaining == FREE_CREDITS
            result = try_increment_application_count(user, 0)
            assert result is True
            assert user.credits_remaining == FREE_CREDITS - 1

    def test_increment_at_zero_fails(self, app, test_user):
        """Consuming a credit fails when balance is 0."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            user.credits_remaining = 0
            db.session.commit()

            result = try_increment_application_count(user, 0)
            assert result is False
            assert user.credits_remaining == 0

    def test_increment_with_high_credits(self, app, test_user):
        """Users with many credits can still consume one."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            user.credits_remaining = 999
            db.session.commit()

            result = try_increment_application_count(user, 0)
            assert result is True
            assert user.credits_remaining == 998

    def test_increment_multiple_until_exhausted(self, app, test_user):
        """Exhaust a small credit balance and verify the last attempt fails."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            user.credits_remaining = 3
            db.session.commit()

            assert try_increment_application_count(user, 0) is True
            assert user.credits_remaining == 2

            assert try_increment_application_count(user, 0) is True
            assert user.credits_remaining == 1

            assert try_increment_application_count(user, 0) is True
            assert user.credits_remaining == 0

            # Fourth attempt should fail
            assert try_increment_application_count(user, 0) is False
            assert user.credits_remaining == 0


class TestDecrementApplicationCount:
    """Tests for the decrement_application_count refund function."""

    def test_decrement(self, app, test_user):
        """Refunding adds one credit back."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            user.credits_remaining = 5
            db.session.commit()

            decrement_application_count(user)
            assert user.credits_remaining == 6

    def test_decrement_from_zero(self, app, test_user):
        """Refunding from zero still adds one credit (no floor enforced)."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            user.credits_remaining = 0
            db.session.commit()

            decrement_application_count(user)
            assert user.credits_remaining == 1


class TestAddCredits:
    """Tests for add_credits (purchase flow)."""

    def test_add_starter_credits(self, app, test_user):
        with app.app_context():
            user = User.query.get(test_user["id"])
            add_credits(user, 50)
            assert user.credits_remaining == FREE_CREDITS + 50

    def test_add_pro_credits(self, app, test_user):
        with app.app_context():
            user = User.query.get(test_user["id"])
            add_credits(user, 150)
            assert user.credits_remaining == FREE_CREDITS + 150

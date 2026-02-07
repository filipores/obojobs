"""Tests for subscription limit middleware."""

from datetime import datetime

from middleware.subscription_limit import (
    decrement_application_count,
    get_subscription_usage,
    increment_application_count,
    try_increment_application_count,
)
from models import Subscription, SubscriptionPlan, SubscriptionStatus, User, db


def _set_month_reset(user):
    """Set month_reset_at to current month so the counter is not auto-reset."""
    now = datetime.utcnow()
    user.month_reset_at = datetime(now.year, now.month, 1)
    db.session.commit()


class TestGetSubscriptionUsage:
    def test_free_user_usage(self, app, test_user):
        with app.app_context():
            user = User.query.get(test_user["id"])
            usage = get_subscription_usage(user)
            assert usage["plan"] == "free"
            assert usage["limit"] == 3
            assert usage["used"] == 0
            assert usage["remaining"] == 3

    def test_pro_user_unlimited(self, app, test_user):
        with app.app_context():
            user = User.query.get(test_user["id"])
            sub = Subscription(
                user_id=user.id,
                plan=SubscriptionPlan.pro,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

            usage = get_subscription_usage(user)
            assert usage["unlimited"] is True
            assert usage["remaining"] == -1


class TestIncrementApplicationCount:
    """Tests for the legacy increment_application_count function."""

    def test_increment(self, app, test_user):
        with app.app_context():
            user = User.query.get(test_user["id"])
            assert user.applications_this_month == 0
            increment_application_count(user)
            assert user.applications_this_month == 1
            increment_application_count(user)
            assert user.applications_this_month == 2


class TestTryIncrementApplicationCount:
    """Tests for the atomic try_increment_application_count function."""

    def test_increment_within_limit(self, app, test_user):
        with app.app_context():
            user = User.query.get(test_user["id"])
            assert user.applications_this_month == 0
            result = try_increment_application_count(user, 3)
            assert result is True
            assert user.applications_this_month == 1

    def test_increment_at_limit_fails(self, app, test_user):
        with app.app_context():
            user = User.query.get(test_user["id"])
            user.applications_this_month = 3
            _set_month_reset(user)

            result = try_increment_application_count(user, 3)
            assert result is False
            assert user.applications_this_month == 3

    def test_increment_unlimited(self, app, test_user):
        with app.app_context():
            user = User.query.get(test_user["id"])
            user.applications_this_month = 999
            _set_month_reset(user)

            result = try_increment_application_count(user, -1)
            assert result is True
            # Counter is not changed for unlimited plans
            assert user.applications_this_month == 999

    def test_increment_multiple_until_limit(self, app, test_user):
        with app.app_context():
            user = User.query.get(test_user["id"])
            assert user.applications_this_month == 0

            assert try_increment_application_count(user, 3) is True
            assert user.applications_this_month == 1

            assert try_increment_application_count(user, 3) is True
            assert user.applications_this_month == 2

            assert try_increment_application_count(user, 3) is True
            assert user.applications_this_month == 3

            # Fourth attempt should fail
            assert try_increment_application_count(user, 3) is False
            assert user.applications_this_month == 3


class TestDecrementApplicationCount:
    """Tests for the decrement_application_count rollback function."""

    def test_decrement(self, app, test_user):
        with app.app_context():
            user = User.query.get(test_user["id"])
            user.applications_this_month = 2
            _set_month_reset(user)

            decrement_application_count(user)
            assert user.applications_this_month == 1

    def test_decrement_does_not_go_below_zero(self, app, test_user):
        with app.app_context():
            user = User.query.get(test_user["id"])
            assert user.applications_this_month == 0

            decrement_application_count(user)
            assert user.applications_this_month == 0

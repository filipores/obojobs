"""Tests for subscription limit middleware."""

from middleware.subscription_limit import get_subscription_usage, increment_application_count
from models import Subscription, SubscriptionPlan, SubscriptionStatus, User, db


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
    def test_increment(self, app, test_user):
        with app.app_context():
            user = User.query.get(test_user["id"])
            assert user.applications_this_month == 0
            increment_application_count(user)
            assert user.applications_this_month == 1
            increment_application_count(user)
            assert user.applications_this_month == 2

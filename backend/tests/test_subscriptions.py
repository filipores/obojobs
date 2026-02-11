"""Tests for subscription routes."""

from unittest.mock import MagicMock, patch

import pytest

from models import Subscription, SubscriptionPlan, SubscriptionStatus, User, db


@pytest.fixture(autouse=True)
def _stripe_enabled():
    """Enable Stripe for all tests so validation checks are reached."""
    with patch("routes.subscriptions.config.is_stripe_enabled", return_value=True):
        yield


class TestGetPlans:
    """Test GET /api/subscriptions/plans (public endpoint)"""

    def test_returns_three_plans(self, client):
        response = client.get("/api/subscriptions/plans")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert len(data["data"]) == 3
        plan_ids = [p["plan_id"] for p in data["data"]]
        assert plan_ids == ["free", "basic", "pro"]

    def test_free_plan_details(self, client):
        response = client.get("/api/subscriptions/plans")
        plans = response.get_json()["data"]
        free = plans[0]
        assert free["price"] == 0
        assert free["limits"]["applications_per_month"] == 3
        assert free["stripe_price_id"] is None

    def test_pro_plan_unlimited(self, client):
        response = client.get("/api/subscriptions/plans")
        plans = response.get_json()["data"]
        pro = plans[2]
        assert pro["limits"]["applications_per_month"] == -1


class TestCreateCheckout:
    """Test POST /api/subscriptions/create-checkout"""

    def test_missing_plan(self, client, auth_headers):
        response = client.post(
            "/api/subscriptions/create-checkout",
            json={
                "success_url": "http://localhost/success",
                "cancel_url": "http://localhost/cancel",
            },
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_invalid_plan(self, client, auth_headers):
        response = client.post(
            "/api/subscriptions/create-checkout",
            json={"plan": "invalid", "success_url": "http://x", "cancel_url": "http://x"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_stripe_disabled_returns_503(self, client, auth_headers):
        """When Stripe is not configured, create-checkout should return 503"""
        with patch("routes.subscriptions.config") as mock_config:
            mock_config.is_stripe_enabled.return_value = False
            response = client.post(
                "/api/subscriptions/create-checkout",
                json={"plan": "basic", "success_url": "http://x", "cancel_url": "http://x"},
                headers=auth_headers,
            )
            assert response.status_code == 503
            data = response.get_json()
            assert data["payments_available"] is False

    def test_missing_urls(self, client, auth_headers):
        response = client.post(
            "/api/subscriptions/create-checkout",
            json={"plan": "basic"},
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestPortalSession:
    """Test POST /api/subscriptions/portal"""

    def test_no_stripe_customer(self, client, auth_headers):
        response = client.post(
            "/api/subscriptions/portal",
            json={"return_url": "http://localhost"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_missing_return_url(self, client, auth_headers):
        response = client.post(
            "/api/subscriptions/portal",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 400


class TestCurrentSubscription:
    """Test GET /api/subscriptions/current"""

    def test_free_user(self, client, auth_headers):
        response = client.get("/api/subscriptions/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["plan"] == "free"
        assert data["usage"]["limit"] == 3

    def test_basic_user(self, client, auth_headers, app, test_user):
        with app.app_context():
            user = User.query.get(test_user["id"])
            sub = Subscription(
                user_id=user.id,
                stripe_customer_id="cus_test",
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

        response = client.get("/api/subscriptions/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["plan"] == "basic"
        assert data["usage"]["limit"] == 20

    def test_returns_cancel_at_period_end(self, client, auth_headers, app, test_user):
        """Current subscription endpoint should return cancel_at_period_end."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            sub = Subscription(
                user_id=user.id,
                stripe_customer_id="cus_test",
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.active,
                cancel_at_period_end=True,
            )
            db.session.add(sub)
            db.session.commit()

        response = client.get("/api/subscriptions/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["cancel_at_period_end"] is True


class TestChangePlan:
    """Test POST /api/subscriptions/change-plan"""

    def test_no_subscription_returns_400(self, client, auth_headers):
        """Users without an active subscription cannot change plan."""
        response = client.post(
            "/api/subscriptions/change-plan",
            json={"plan": "pro"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_invalid_plan_returns_400(self, client, auth_headers):
        """Invalid plan name should return 400."""
        response = client.post(
            "/api/subscriptions/change-plan",
            json={"plan": "enterprise"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_same_plan_returns_400(self, client, auth_headers, app, test_user):
        """Changing to the same plan should return 400."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            sub = Subscription(
                user_id=user.id,
                stripe_customer_id="cus_test_change",
                stripe_subscription_id="sub_test_change",
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

        response = client.post(
            "/api/subscriptions/change-plan",
            json={"plan": "basic"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("routes.subscriptions.StripeService")
    def test_upgrade_basic_to_pro(self, mock_service_class, client, auth_headers, app, test_user):
        """Upgrading from basic to pro should use always_invoice proration."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            sub = Subscription(
                user_id=user.id,
                stripe_customer_id="cus_test_upgrade",
                stripe_subscription_id="sub_test_upgrade",
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/subscriptions/change-plan",
            json={"plan": "pro"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["previous_plan"] == "basic"
        assert data["data"]["new_plan"] == "pro"
        assert data["data"]["is_upgrade"] is True

        # Verify proration behavior
        mock_service.modify_subscription.assert_called_once()
        call_kwargs = mock_service.modify_subscription.call_args
        assert (
            call_kwargs.kwargs.get("proration_behavior") == "always_invoice"
            or (len(call_kwargs.args) >= 3 and call_kwargs.args[2] == "always_invoice")
            or call_kwargs[1].get("proration_behavior") == "always_invoice"
        )

    @patch("routes.subscriptions.StripeService")
    def test_downgrade_pro_to_basic(self, mock_service_class, client, auth_headers, app, test_user):
        """Downgrading from pro to basic should use create_prorations proration."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            sub = Subscription(
                user_id=user.id,
                stripe_customer_id="cus_test_downgrade",
                stripe_subscription_id="sub_test_downgrade",
                plan=SubscriptionPlan.pro,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/subscriptions/change-plan",
            json={"plan": "basic"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["data"]["previous_plan"] == "pro"
        assert data["data"]["new_plan"] == "basic"
        assert data["data"]["is_upgrade"] is False

    def test_stripe_disabled_returns_503(self, client, auth_headers):
        """When Stripe is not configured, change-plan should return 503."""
        with patch("routes.subscriptions.config") as mock_config:
            mock_config.is_stripe_enabled.return_value = False
            response = client.post(
                "/api/subscriptions/change-plan",
                json={"plan": "pro"},
                headers=auth_headers,
            )
            assert response.status_code == 503


class TestSubscriptionModelFields:
    """Test that new subscription model fields work correctly."""

    def test_default_cancel_at_period_end(self, app):
        """cancel_at_period_end should default to False."""
        with app.app_context():
            sub = Subscription(
                user_id=1,
                plan=SubscriptionPlan.free,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

            fetched = Subscription.query.first()
            assert fetched.cancel_at_period_end is False
            assert fetched.canceled_at is None
            assert fetched.trial_end is None

    def test_to_dict_includes_new_fields(self, app):
        """to_dict() should include cancel_at_period_end, canceled_at, trial_end."""
        with app.app_context():
            sub = Subscription(
                user_id=1,
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

            result = sub.to_dict()
            assert "cancel_at_period_end" in result
            assert "canceled_at" in result
            assert "trial_end" in result
            assert result["cancel_at_period_end"] is False
            assert result["canceled_at"] is None
            assert result["trial_end"] is None

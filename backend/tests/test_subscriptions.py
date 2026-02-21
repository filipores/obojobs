"""Tests for subscription routes (credit-based pricing model)."""

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
        assert plan_ids == ["free", "starter", "pro"]

    def test_free_plan_details(self, client):
        response = client.get("/api/subscriptions/plans")
        plans = response.get_json()["data"]
        free = plans[0]
        assert free["price"] == 0
        assert free["credits"] == 10
        assert free["stripe_price_id"] is None

    def test_pro_plan_credits(self, client):
        """Pro plan should offer 150 credits."""
        response = client.get("/api/subscriptions/plans")
        plans = response.get_json()["data"]
        pro = plans[2]
        assert pro["credits"] == 150
        assert pro["plan_id"] == "pro"

    def test_starter_plan_credits(self, client):
        """Starter plan should offer 50 credits."""
        response = client.get("/api/subscriptions/plans")
        plans = response.get_json()["data"]
        starter = plans[1]
        assert starter["credits"] == 50
        assert starter["plan_id"] == "starter"

    def test_plans_include_features(self, client):
        """Each plan should have a features list."""
        response = client.get("/api/subscriptions/plans")
        plans = response.get_json()["data"]
        for plan in plans:
            assert "features" in plan
            assert isinstance(plan["features"], list)
            assert len(plan["features"]) > 0

    def test_payments_available_in_response(self, client):
        """Response should include payments_available flag."""
        response = client.get("/api/subscriptions/plans")
        data = response.get_json()
        assert "payments_available" in data


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

    def test_free_plan_rejected(self, client, auth_headers):
        """Free plan should not be purchasable via checkout."""
        response = client.post(
            "/api/subscriptions/create-checkout",
            json={"plan": "free", "success_url": "http://x", "cancel_url": "http://x"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    def test_stripe_disabled_returns_503(self, client, auth_headers):
        """When Stripe is not configured, create-checkout should return 503"""
        with patch("routes.subscriptions.config") as mock_config:
            mock_config.is_stripe_enabled.return_value = False
            response = client.post(
                "/api/subscriptions/create-checkout",
                json={"plan": "starter", "success_url": "http://x", "cancel_url": "http://x"},
                headers=auth_headers,
            )
            assert response.status_code == 503
            data = response.get_json()
            assert data["payments_available"] is False

    def test_missing_urls(self, client, auth_headers):
        response = client.post(
            "/api/subscriptions/create-checkout",
            json={"plan": "starter"},
            headers=auth_headers,
        )
        assert response.status_code == 400

    @patch("routes.subscriptions.StripeService")
    def test_successful_checkout_starter(self, mock_service_class, client, auth_headers, app, test_user):
        """Successful checkout for starter plan creates a Stripe session."""
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service
        mock_service.create_customer.return_value = "cus_new_123"
        mock_session = MagicMock()
        mock_session.url = "https://checkout.stripe.com/session_123"
        mock_session.id = "cs_test_123"
        mock_service.create_checkout_session.return_value = mock_session

        with patch("routes.subscriptions.config") as mock_config:
            mock_config.is_stripe_enabled.return_value = True
            mock_config.STRIPE_PRICE_STARTER = "price_starter_test"
            mock_config.STRIPE_PRICE_PRO = "price_pro_test"

            # Re-import to pick up patched config in SUBSCRIPTION_PLANS
            # Instead, patch the plan data directly
            with patch(
                "routes.subscriptions.SUBSCRIPTION_PLANS",
                {
                    "starter": {
                        "plan_id": "starter",
                        "name": "Starter",
                        "price": 9.90,
                        "credits": 50,
                        "stripe_price_id": "price_starter_test",
                    },
                    "pro": {
                        "plan_id": "pro",
                        "name": "Pro",
                        "price": 19.90,
                        "credits": 150,
                        "stripe_price_id": "price_pro_test",
                    },
                    "free": {
                        "plan_id": "free",
                        "name": "Free",
                        "price": 0,
                        "credits": 10,
                        "stripe_price_id": None,
                    },
                },
            ):
                response = client.post(
                    "/api/subscriptions/create-checkout",
                    json={
                        "plan": "starter",
                        "success_url": "http://localhost/success",
                        "cancel_url": "http://localhost/cancel",
                    },
                    headers=auth_headers,
                )

        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "checkout_url" in data["data"]
        assert "session_id" in data["data"]


class TestCurrentSubscription:
    """Test GET /api/subscriptions/current"""

    def test_free_user(self, client, auth_headers):
        """Free user should have 10 credits (default)."""
        response = client.get("/api/subscriptions/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["plan"] == "free"
        assert data["credits_remaining"] == 10
        assert data["usage"]["limit"] == 10
        assert data["usage"]["remaining"] == 10

    def test_credits_remaining_matches_user(self, client, auth_headers, app, test_user):
        """Credits remaining should reflect the user's actual credit balance."""
        with app.app_context():
            user = db.session.get(User, test_user["id"])
            user.credits_remaining = 75
            db.session.commit()

        response = client.get("/api/subscriptions/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["credits_remaining"] == 75
        assert data["usage"]["remaining"] == 75

    def test_zero_credits_remaining(self, client, auth_headers, app, test_user):
        """User with zero credits should see zero remaining."""
        with app.app_context():
            user = db.session.get(User, test_user["id"])
            user.credits_remaining = 0
            db.session.commit()

        response = client.get("/api/subscriptions/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["credits_remaining"] == 0
        assert data["usage"]["remaining"] == 0

    def test_response_includes_plan_details(self, client, auth_headers):
        """Current subscription response should include plan details."""
        response = client.get("/api/subscriptions/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert "plan_details" in data
        assert data["plan_details"]["plan_id"] == "free"

    def test_response_includes_payments_available(self, client, auth_headers):
        """Current subscription response should include payments_available."""
        response = client.get("/api/subscriptions/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert "payments_available" in data

    def test_has_stripe_customer_flag(self, client, auth_headers, app, test_user):
        """Should return has_stripe_customer based on user's stripe_customer_id."""
        # Default user has no stripe customer
        response = client.get("/api/subscriptions/current", headers=auth_headers)
        data = response.get_json()["data"]
        assert data["has_stripe_customer"] is False

        # Set stripe customer id
        with app.app_context():
            user = db.session.get(User, test_user["id"])
            user.stripe_customer_id = "cus_test_123"
            db.session.commit()

        response = client.get("/api/subscriptions/current", headers=auth_headers)
        data = response.get_json()["data"]
        assert data["has_stripe_customer"] is True


class TestPaymentStatus:
    """Test GET /api/subscriptions/status (public endpoint)"""

    def test_returns_status(self, client):
        """Status endpoint should return payments_available flag."""
        response = client.get("/api/subscriptions/status")
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert "payments_available" in data["data"]

    def test_stripe_disabled(self, client):
        """When Stripe is disabled, payments_available should be False."""
        with patch("routes.subscriptions.config.is_stripe_enabled", return_value=False):
            response = client.get("/api/subscriptions/status")
            assert response.status_code == 200
            data = response.get_json()
            assert data["data"]["payments_available"] is False


class TestSubscriptionModelFields:
    """Test that subscription model fields work correctly."""

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
                plan=SubscriptionPlan.starter,
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

    def test_subscription_plan_enum_values(self, app):
        """SubscriptionPlan should have free, starter, pro values."""
        assert SubscriptionPlan.free.value == "free"
        assert SubscriptionPlan.starter.value == "starter"
        assert SubscriptionPlan.pro.value == "pro"

    def test_to_dict_plan_value(self, app):
        """to_dict() should return the plan enum value as string."""
        with app.app_context():
            sub = Subscription(
                user_id=1,
                plan=SubscriptionPlan.pro,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

            result = sub.to_dict()
            assert result["plan"] == "pro"
            assert result["status"] == "active"

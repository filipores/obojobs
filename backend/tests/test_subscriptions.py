"""Tests for subscription routes."""

from unittest.mock import patch

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

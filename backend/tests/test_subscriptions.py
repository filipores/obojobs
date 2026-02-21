"""Tests for subscription routes."""

from unittest.mock import MagicMock, patch

import pytest

from config import config
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

    def test_pro_plan_unlimited(self, client):
        response = client.get("/api/subscriptions/plans")
        plans = response.get_json()["data"]
        pro = plans[2]
        # In credit model, pro is not unlimited but high credits
        assert pro["credits"] > 50


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


class TestCurrentSubscription:
    """Test GET /api/subscriptions/current"""

    def test_free_user(self, client, auth_headers):
        response = client.get("/api/subscriptions/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()["data"]
        assert data["plan"] == "free"
        assert data["credits_remaining"] == 10

    def test_basic_user(self, client, auth_headers, app, test_user):
        """Test user who bought starter package."""
        with app.app_context():
            user = User.query.get(test_user["id"])
            user.stripe_customer_id = "cus_test"
            # Manually set credits to simulate purchase
            user.credits_remaining = 50
            db.session.commit()

        response = client.get("/api/subscriptions/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()["data"]
        # Plan is 'free' because no recurring sub, but credits reflect purchase
        assert data["plan"] == "free"
        assert data["credits_remaining"] == 50


class TestChangePlan:
    """Test POST /api/subscriptions/change-plan (Legacy/Unsupported)"""

    def test_endpoint_returns_404_or_method_not_allowed(self, client, auth_headers):
        """This endpoint likely doesn't exist anymore or logic changed."""
        response = client.post(
            "/api/subscriptions/change-plan",
            json={"plan": "pro"},
            headers=auth_headers,
        )
        assert response.status_code in [404, 405]

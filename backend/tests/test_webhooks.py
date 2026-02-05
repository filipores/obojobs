"""Tests for Stripe webhook handling."""

from unittest.mock import MagicMock, patch

import pytest
import stripe

from models import Subscription, SubscriptionPlan, SubscriptionStatus, User, db


@pytest.fixture
def user_with_stripe(app, test_user):
    """Create a user with stripe_customer_id"""
    with app.app_context():
        user = User.query.get(test_user["id"])
        user.stripe_customer_id = "cus_test_123"
        db.session.commit()
        return {**test_user, "stripe_customer_id": "cus_test_123"}


class TestWebhookSignature:
    def test_missing_signature(self, client):
        response = client.post(
            "/api/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
        )
        assert response.status_code == 400

    @patch("routes.webhooks.StripeService")
    def test_invalid_signature(self, mock_service_class, client):
        mock_service = MagicMock()
        mock_service.construct_webhook_event.side_effect = stripe.error.SignatureVerificationError("bad sig", "header")
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            headers={"Stripe-Signature": "bad_sig"},
        )
        assert response.status_code == 400


class TestCheckoutCompleted:
    @patch("routes.webhooks.StripeService")
    def test_creates_subscription(self, mock_service_class, client, user_with_stripe, app):
        mock_service = MagicMock()
        mock_service.construct_webhook_event.return_value = {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "customer": "cus_test_123",
                    "subscription": "sub_test_123",
                }
            },
        }
        mock_service.get_subscription.return_value = {
            "status": "active",
            "current_period_start": 1700000000,
            "current_period_end": 1702600000,
            "items": {"data": [{"price": {"id": "price_dev_basic_mock"}}]},
        }
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            headers={"Stripe-Signature": "valid"},
        )
        assert response.status_code == 200

        with app.app_context():
            sub = Subscription.query.filter_by(user_id=user_with_stripe["id"]).first()
            assert sub is not None
            assert sub.stripe_subscription_id == "sub_test_123"


class TestSubscriptionDeleted:
    @patch("routes.webhooks.StripeService")
    def test_resets_to_free(self, mock_service_class, client, user_with_stripe, app):
        # First create a subscription
        with app.app_context():
            sub = Subscription(
                user_id=user_with_stripe["id"],
                stripe_customer_id="cus_test_123",
                stripe_subscription_id="sub_test_456",
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

        mock_service = MagicMock()
        mock_service.construct_webhook_event.return_value = {
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_test_456", "customer": "cus_test_123"}},
        }
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            headers={"Stripe-Signature": "valid"},
        )
        assert response.status_code == 200

        with app.app_context():
            sub = Subscription.query.filter_by(user_id=user_with_stripe["id"]).first()
            assert sub.plan == SubscriptionPlan.free
            assert sub.status == SubscriptionStatus.canceled

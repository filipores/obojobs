"""Tests for Stripe webhook handling."""

from unittest.mock import MagicMock, patch

import pytest
import stripe

from models import Subscription, SubscriptionPlan, SubscriptionStatus, User, WebhookEvent, db


@pytest.fixture
def user_with_stripe(app, test_user):
    """Create a user with stripe_customer_id"""
    with app.app_context():
        user = User.query.get(test_user["id"])
        user.stripe_customer_id = "cus_test_123"
        db.session.commit()
        return {**test_user, "stripe_customer_id": "cus_test_123"}


def _make_webhook_event(event_type, event_data, event_id="evt_test_001"):
    """Helper to build a mock webhook event dict."""
    return {
        "id": event_id,
        "type": event_type,
        "data": {"object": event_data},
    }


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
        mock_service.construct_webhook_event.return_value = _make_webhook_event(
            "checkout.session.completed",
            {
                "customer": "cus_test_123",
                "subscription": "sub_test_123",
            },
        )
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
        mock_service.construct_webhook_event.return_value = _make_webhook_event(
            "customer.subscription.deleted",
            {"id": "sub_test_456", "customer": "cus_test_123"},
        )
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


class TestWebhookIdempotency:
    """Test that duplicate webhook events are safely skipped."""

    @patch("routes.webhooks.StripeService")
    def test_duplicate_event_skipped(self, mock_service_class, client, user_with_stripe, app):
        """Sending the same event twice should skip the second one."""
        mock_service = MagicMock()
        mock_service.construct_webhook_event.return_value = _make_webhook_event(
            "customer.subscription.deleted",
            {"id": "sub_test_dup", "customer": "cus_test_123"},
            event_id="evt_duplicate_001",
        )
        mock_service_class.return_value = mock_service

        # Create subscription to be deleted
        with app.app_context():
            sub = Subscription(
                user_id=user_with_stripe["id"],
                stripe_customer_id="cus_test_123",
                stripe_subscription_id="sub_test_dup",
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

        # First call: processes normally
        response1 = client.post(
            "/api/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            headers={"Stripe-Signature": "valid"},
        )
        assert response1.status_code == 200
        data1 = response1.get_json()
        assert data1.get("duplicate") is None or data1.get("duplicate") is not True

        # Second call: should be skipped as duplicate
        response2 = client.post(
            "/api/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            headers={"Stripe-Signature": "valid"},
        )
        assert response2.status_code == 200
        data2 = response2.get_json()
        assert data2.get("duplicate") is True

    @patch("routes.webhooks.StripeService")
    def test_event_recorded_in_db(self, mock_service_class, client, user_with_stripe, app):
        """Processed events should be recorded in the webhook_events table."""
        mock_service = MagicMock()
        mock_service.construct_webhook_event.return_value = _make_webhook_event(
            "customer.subscription.updated",
            {
                "id": "sub_test_record",
                "customer": "cus_test_123",
                "status": "active",
                "current_period_start": 1700000000,
                "current_period_end": 1702600000,
                "items": {"data": [{"price": {"id": "price_dev_basic_mock"}}]},
            },
            event_id="evt_record_001",
        )
        mock_service_class.return_value = mock_service

        with app.app_context():
            sub = Subscription(
                user_id=user_with_stripe["id"],
                stripe_customer_id="cus_test_123",
                stripe_subscription_id="sub_test_record",
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

        client.post(
            "/api/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            headers={"Stripe-Signature": "valid"},
        )

        with app.app_context():
            event = WebhookEvent.query.filter_by(stripe_event_id="evt_record_001").first()
            assert event is not None
            assert event.event_type == "customer.subscription.updated"
            assert event.status == "success"


class TestInvoicePaymentFailed:
    """Test invoice.payment_failed webhook handler."""

    @patch("routes.webhooks.StripeService")
    def test_sets_status_to_past_due(self, mock_service_class, client, user_with_stripe, app):
        with app.app_context():
            sub = Subscription(
                user_id=user_with_stripe["id"],
                stripe_customer_id="cus_test_123",
                stripe_subscription_id="sub_test_fail",
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

        mock_service = MagicMock()
        mock_service.construct_webhook_event.return_value = _make_webhook_event(
            "invoice.payment_failed",
            {"subscription": "sub_test_fail"},
            event_id="evt_fail_001",
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            headers={"Stripe-Signature": "valid"},
        )
        assert response.status_code == 200

        with app.app_context():
            sub = Subscription.query.filter_by(stripe_subscription_id="sub_test_fail").first()
            assert sub.status == SubscriptionStatus.past_due


class TestInvoicePaymentSucceeded:
    """Test invoice.payment_succeeded webhook handler."""

    @patch("routes.webhooks.StripeService")
    def test_confirms_active_and_updates_period(self, mock_service_class, client, user_with_stripe, app):
        with app.app_context():
            sub = Subscription(
                user_id=user_with_stripe["id"],
                stripe_customer_id="cus_test_123",
                stripe_subscription_id="sub_test_success",
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.past_due,
            )
            db.session.add(sub)
            db.session.commit()

        mock_service = MagicMock()
        mock_service.construct_webhook_event.return_value = _make_webhook_event(
            "invoice.payment_succeeded",
            {
                "subscription": "sub_test_success",
                "lines": {
                    "data": [
                        {
                            "period": {
                                "start": 1702600000,
                                "end": 1705200000,
                            }
                        }
                    ]
                },
            },
            event_id="evt_success_001",
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            headers={"Stripe-Signature": "valid"},
        )
        assert response.status_code == 200

        with app.app_context():
            sub = Subscription.query.filter_by(stripe_subscription_id="sub_test_success").first()
            assert sub.status == SubscriptionStatus.active
            assert sub.current_period_start is not None
            assert sub.current_period_end is not None


class TestSubscriptionUpdatedTracking:
    """Test that subscription.updated tracks cancellation and trial fields."""

    @patch("routes.webhooks.StripeService")
    def test_tracks_cancel_at_period_end(self, mock_service_class, client, user_with_stripe, app):
        with app.app_context():
            sub = Subscription(
                user_id=user_with_stripe["id"],
                stripe_customer_id="cus_test_123",
                stripe_subscription_id="sub_test_cancel",
                plan=SubscriptionPlan.basic,
                status=SubscriptionStatus.active,
            )
            db.session.add(sub)
            db.session.commit()

        mock_service = MagicMock()
        mock_service.construct_webhook_event.return_value = _make_webhook_event(
            "customer.subscription.updated",
            {
                "id": "sub_test_cancel",
                "customer": "cus_test_123",
                "status": "active",
                "cancel_at_period_end": True,
                "canceled_at": 1702500000,
                "trial_end": None,
                "current_period_start": 1700000000,
                "current_period_end": 1702600000,
                "items": {"data": [{"price": {"id": "price_dev_basic_mock"}}]},
            },
            event_id="evt_cancel_track_001",
        )
        mock_service_class.return_value = mock_service

        response = client.post(
            "/api/webhooks/stripe",
            data=b"{}",
            content_type="application/json",
            headers={"Stripe-Signature": "valid"},
        )
        assert response.status_code == 200

        with app.app_context():
            sub = Subscription.query.filter_by(stripe_subscription_id="sub_test_cancel").first()
            assert sub.cancel_at_period_end is True
            assert sub.canceled_at is not None

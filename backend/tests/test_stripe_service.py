"""Tests for StripeService (services/stripe_service.py)."""

from unittest.mock import MagicMock, patch

import pytest


class TestStripeServiceInit:
    """Tests for StripeService initialization."""

    @patch("services.stripe_service.config")
    def test_init_without_key_raises(self, mock_config):
        mock_config.STRIPE_SECRET_KEY = None
        from services.stripe_service import StripeService

        with pytest.raises(ValueError, match="STRIPE_SECRET_KEY"):
            StripeService()

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.config")
    def test_init_sets_api_key(self, mock_config, mock_stripe):
        mock_config.STRIPE_SECRET_KEY = "sk_test_123"
        from services.stripe_service import StripeService

        StripeService()
        assert mock_stripe.api_key == "sk_test_123"


class TestStripeServiceMethods:
    """Tests for StripeService methods with stripe fully mocked."""

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.config")
    def test_create_customer(self, mock_config, mock_stripe):
        mock_config.STRIPE_SECRET_KEY = "sk_test_123"
        mock_stripe.Customer.create.return_value = MagicMock(id="cus_123")
        from services.stripe_service import StripeService

        service = StripeService()
        result = service.create_customer("test@example.com", name="Test User")
        assert result == "cus_123"

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.config")
    def test_create_customer_with_metadata(self, mock_config, mock_stripe):
        mock_config.STRIPE_SECRET_KEY = "sk_test_123"
        mock_stripe.Customer.create.return_value = MagicMock(id="cus_123")
        from services.stripe_service import StripeService

        service = StripeService()
        service.create_customer("test@example.com", metadata={"user_id": "1"})
        call_kwargs = mock_stripe.Customer.create.call_args
        assert call_kwargs.kwargs["metadata"] == {"user_id": "1"}

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.config")
    def test_get_customer(self, mock_config, mock_stripe):
        mock_config.STRIPE_SECRET_KEY = "sk_test_123"
        from services.stripe_service import StripeService

        service = StripeService()
        service.get_customer("cus_123")
        mock_stripe.Customer.retrieve.assert_called_once_with("cus_123")

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.config")
    def test_create_checkout_session(self, mock_config, mock_stripe):
        mock_config.STRIPE_SECRET_KEY = "sk_test_123"
        mock_stripe.checkout.Session.create.return_value = MagicMock()
        from services.stripe_service import StripeService

        service = StripeService()
        service.create_checkout_session("cus_123", "price_basic", "http://ok", "http://cancel")
        call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        assert call_kwargs["customer"] == "cus_123"
        assert call_kwargs["mode"] == "subscription"

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.config")
    def test_create_checkout_session_with_metadata(self, mock_config, mock_stripe):
        mock_config.STRIPE_SECRET_KEY = "sk_test_123"
        mock_stripe.checkout.Session.create.return_value = MagicMock()
        from services.stripe_service import StripeService

        service = StripeService()
        service.create_checkout_session(
            "cus_123", "price_basic", "http://ok", "http://cancel", metadata={"plan": "basic"}
        )
        call_kwargs = mock_stripe.checkout.Session.create.call_args.kwargs
        assert call_kwargs["metadata"] == {"plan": "basic"}

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.config")
    def test_create_portal_session(self, mock_config, mock_stripe):
        mock_config.STRIPE_SECRET_KEY = "sk_test_123"
        from services.stripe_service import StripeService

        service = StripeService()
        service.create_portal_session("cus_123", "http://localhost")
        mock_stripe.billing_portal.Session.create.assert_called_once_with(
            customer="cus_123", return_url="http://localhost"
        )

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.config")
    def test_get_subscription(self, mock_config, mock_stripe):
        mock_config.STRIPE_SECRET_KEY = "sk_test_123"
        from services.stripe_service import StripeService

        service = StripeService()
        service.get_subscription("sub_123")
        mock_stripe.Subscription.retrieve.assert_called_once_with("sub_123")

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.config")
    def test_modify_subscription(self, mock_config, mock_stripe):
        mock_config.STRIPE_SECRET_KEY = "sk_test_123"
        mock_sub = MagicMock()
        mock_sub.__getitem__ = lambda s, key: {"data": [{"id": "si_123"}]}
        mock_stripe.Subscription.retrieve.return_value = mock_sub
        from services.stripe_service import StripeService

        service = StripeService()
        service.modify_subscription("sub_123", "price_pro", proration_behavior="always_invoice")
        mock_stripe.Subscription.modify.assert_called_once()

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.config")
    def test_cancel_subscription(self, mock_config, mock_stripe):
        mock_config.STRIPE_SECRET_KEY = "sk_test_123"
        from services.stripe_service import StripeService

        service = StripeService()
        service.cancel_subscription("sub_123")
        mock_stripe.Subscription.modify.assert_called_once_with("sub_123", cancel_at_period_end=True)

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.config")
    def test_construct_webhook_event(self, mock_config, mock_stripe):
        mock_config.STRIPE_SECRET_KEY = "sk_test_123"
        mock_config.STRIPE_WEBHOOK_SECRET = "whsec_test"
        mock_stripe.Webhook.construct_event.return_value = MagicMock(type="checkout.session.completed")
        from services.stripe_service import StripeService

        service = StripeService()
        service.construct_webhook_event(b"payload", "sig_header")
        mock_stripe.Webhook.construct_event.assert_called_once()

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.config")
    def test_list_prices(self, mock_config, mock_stripe):
        mock_config.STRIPE_SECRET_KEY = "sk_test_123"
        mock_stripe.Price.list.return_value = MagicMock(data=[MagicMock(id="price_1")])
        from services.stripe_service import StripeService

        service = StripeService()
        service.list_prices()
        mock_stripe.Price.list.assert_called_once_with(active=True)

    @patch("services.stripe_service.stripe")
    @patch("services.stripe_service.config")
    def test_get_price(self, mock_config, mock_stripe):
        mock_config.STRIPE_SECRET_KEY = "sk_test_123"
        from services.stripe_service import StripeService

        service = StripeService()
        service.get_price("price_1")
        mock_stripe.Price.retrieve.assert_called_once_with("price_1", expand=["product"])

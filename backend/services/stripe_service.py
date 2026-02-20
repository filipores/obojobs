import stripe

from config import config

# Pin API version for stability
stripe.api_version = "2024-12-18.acacia"


class StripeService:
    """Service for Stripe payment operations."""

    def __init__(self):
        if not config.STRIPE_SECRET_KEY:
            raise ValueError("STRIPE_SECRET_KEY is not configured")
        stripe.api_key = config.STRIPE_SECRET_KEY

    def create_customer(self, email: str, name: str | None = None, metadata: dict | None = None) -> str:
        """Create a Stripe customer and return the customer ID."""
        customer_data = {"email": email}
        if name:
            customer_data["name"] = name
        if metadata:
            customer_data["metadata"] = metadata

        return stripe.Customer.create(**customer_data).id

    def get_customer(self, customer_id: str) -> stripe.Customer:
        """Retrieve a Stripe customer by ID."""
        return stripe.Customer.retrieve(customer_id)

    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: dict | None = None,
    ) -> stripe.checkout.Session:
        """Create a Stripe Checkout session for one-time credit purchase."""
        session_params = {
            "customer": customer_id,
            "mode": "payment",
            "payment_method_types": ["card"],
            "line_items": [{"price": price_id, "quantity": 1}],
            "success_url": success_url,
            "cancel_url": cancel_url,
            "allow_promotion_codes": True,
        }
        if metadata:
            session_params["metadata"] = metadata

        return stripe.checkout.Session.create(**session_params)

    def create_portal_session(self, customer_id: str, return_url: str) -> stripe.billing_portal.Session:
        """Create a Stripe Customer Portal session for subscription management."""
        return stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )

    def get_subscription(self, subscription_id: str) -> stripe.Subscription:
        """Retrieve a Stripe subscription by ID."""
        return stripe.Subscription.retrieve(subscription_id)

    def modify_subscription(
        self,
        subscription_id: str,
        new_price_id: str,
        proration_behavior: str = "create_prorations",
    ) -> stripe.Subscription:
        """Modify a subscription to change plans (upgrade/downgrade)."""
        subscription = stripe.Subscription.retrieve(subscription_id)

        return stripe.Subscription.modify(
            subscription_id,
            items=[
                {
                    "id": subscription["items"]["data"][0]["id"],
                    "price": new_price_id,
                }
            ],
            proration_behavior=proration_behavior,
        )

    def cancel_subscription(self, subscription_id: str) -> stripe.Subscription:
        """Cancel a subscription at the end of the billing period."""
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )

    def construct_webhook_event(self, payload: bytes, sig_header: str) -> stripe.Event:
        """Construct and verify a webhook event from Stripe."""
        return stripe.Webhook.construct_event(
            payload,
            sig_header,
            config.STRIPE_WEBHOOK_SECRET,
        )

    def list_prices(self, active_only: bool = True) -> list:
        """List all Stripe prices (subscription plans)."""
        return stripe.Price.list(active=active_only).data

    def get_price(self, price_id: str) -> stripe.Price:
        """Retrieve a Stripe price by ID with expanded product."""
        return stripe.Price.retrieve(price_id, expand=["product"])

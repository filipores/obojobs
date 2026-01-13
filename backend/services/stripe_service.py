import stripe

from config import config


class StripeService:
    """
    Service for Stripe payment operations.
    Handles subscriptions, checkout sessions, and webhook processing.
    """

    def __init__(self):
        """Initialize Stripe SDK with credentials from config"""
        stripe.api_key = config.STRIPE_SECRET_KEY

        # Verify API key is set (in test mode, key starts with sk_test_)
        if not config.STRIPE_SECRET_KEY:
            raise ValueError("STRIPE_SECRET_KEY is not configured")

    def create_customer(self, email: str, name: str | None = None) -> str:
        """
        Create a Stripe customer.

        Args:
            email: Customer email address
            name: Optional customer name

        Returns:
            Stripe customer ID
        """
        customer_data = {"email": email}
        if name:
            customer_data["name"] = name

        customer = stripe.Customer.create(**customer_data)
        return customer.id

    def get_customer(self, customer_id: str) -> stripe.Customer:
        """
        Retrieve a Stripe customer by ID.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Stripe Customer object
        """
        return stripe.Customer.retrieve(customer_id)

    def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> stripe.checkout.Session:
        """
        Create a Stripe Checkout session for subscription.

        Args:
            customer_id: Stripe customer ID
            price_id: Stripe price ID for the subscription plan
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if user cancels

        Returns:
            Stripe Checkout Session object with URL
        """
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session

    def create_portal_session(
        self,
        customer_id: str,
        return_url: str,
    ) -> stripe.billing_portal.Session:
        """
        Create a Stripe Customer Portal session for subscription management.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session

        Returns:
            Stripe Portal Session object with URL
        """
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session

    def get_subscription(self, subscription_id: str) -> stripe.Subscription:
        """
        Retrieve a subscription by ID.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Stripe Subscription object
        """
        return stripe.Subscription.retrieve(subscription_id)

    def cancel_subscription(self, subscription_id: str) -> stripe.Subscription:
        """
        Cancel a subscription at the end of the billing period.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Updated Stripe Subscription object
        """
        return stripe.Subscription.modify(
            subscription_id,
            cancel_at_period_end=True,
        )

    def construct_webhook_event(
        self,
        payload: bytes,
        sig_header: str,
    ) -> stripe.Event:
        """
        Construct and verify a webhook event from Stripe.

        Args:
            payload: Raw request body
            sig_header: Stripe-Signature header value

        Returns:
            Verified Stripe Event object

        Raises:
            stripe.error.SignatureVerificationError: If signature is invalid
        """
        return stripe.Webhook.construct_event(
            payload,
            sig_header,
            config.STRIPE_WEBHOOK_SECRET,
        )

    def list_prices(self, active_only: bool = True) -> list:
        """
        List all prices (subscription plans).

        Args:
            active_only: Only return active prices

        Returns:
            List of Stripe Price objects
        """
        return stripe.Price.list(active=active_only).data

    def get_price(self, price_id: str) -> stripe.Price:
        """
        Retrieve a price by ID.

        Args:
            price_id: Stripe price ID

        Returns:
            Stripe Price object
        """
        return stripe.Price.retrieve(price_id, expand=["product"])

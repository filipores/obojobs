import paypalrestsdk

from config import config


class PayPalService:
    def __init__(self):
        """Initialize PayPal SDK with credentials from config"""
        paypalrestsdk.configure({
            "mode": config.PAYPAL_MODE,  # sandbox or live
            "client_id": config.PAYPAL_CLIENT_ID,
            "client_secret": config.PAYPAL_CLIENT_SECRET
        })

    def create_order(self, package_name: str, return_url: str, cancel_url: str):
        """
        Create a PayPal payment order for credit purchase

        Args:
            package_name: Name of the package ('small', 'medium', 'large')
            return_url: URL to return to after successful payment
            cancel_url: URL to return to if user cancels

        Returns:
            dict with payment_id and approval_url

        Raises:
            ValueError: If package_name is invalid
            Exception: If PayPal API call fails
        """
        package = config.CREDIT_PACKAGES.get(package_name)
        if not package:
            raise ValueError(f"Invalid package: {package_name}")

        payment = paypalrestsdk.Payment({
            "intent": "sale",
            "payer": {
                "payment_method": "paypal"
            },
            "redirect_urls": {
                "return_url": return_url,
                "cancel_url": cancel_url
            },
            "transactions": [{
                "item_list": {
                    "items": [{
                        "name": f"{package['name']} - {package['credits']} Credits",
                        "sku": package_name,
                        "price": f"{package['price']:.2f}",
                        "currency": "EUR",
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": f"{package['price']:.2f}",
                    "currency": "EUR"
                },
                "description": f"Kauf von {package['credits']} Credits für obo"
            }]
        })

        if payment.create():
            # Find approval URL
            approval_url = None
            for link in payment.links:
                if link.rel == 'approval_url':
                    approval_url = link.href
                    break

            return {
                'payment_id': payment.id,
                'approval_url': approval_url
            }
        else:
            raise Exception(f"PayPal Error: {payment.error}")

    def execute_payment(self, payment_id: str, payer_id: str):
        """
        Execute/Capture a PayPal payment after user approval

        Args:
            payment_id: The PayPal payment ID
            payer_id: The payer ID from PayPal redirect

        Returns:
            dict with success status, payer_email, and transaction_id

        Raises:
            Exception: If payment execution fails
        """
        payment = paypalrestsdk.Payment.find(payment_id)

        if payment.execute({"payer_id": payer_id}):
            # Extract payer info and transaction ID
            payer_email = payment.payer.payer_info.email
            transaction_id = payment.transactions[0].related_resources[0].sale.id

            return {
                'success': True,
                'payer_email': payer_email,
                'transaction_id': transaction_id
            }
        else:
            raise Exception(f"Payment execution failed: {payment.error}")

    def get_payment_details(self, payment_id: str):
        """
        Get payment details from PayPal

        Args:
            payment_id: The PayPal payment ID

        Returns:
            dict with payment details
        """
        payment = paypalrestsdk.Payment.find(payment_id)
        return payment.to_dict()

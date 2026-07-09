from decimal import Decimal
from typing import Optional

import stripe

from .base import PaymentProvider, PaymentResult


class StripeProvider(PaymentProvider):
    def __init__(self, api_key: str, webhook_secret: str = None):
        if api_key and not api_key.startswith("sk_test_"):
            raise ValueError(
                "StripeProvider only accepts Stripe TEST secret keys (they start with 'sk_test_')."
            )
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        stripe.api_key = api_key

    def initialize_payment(
        self, amount: Decimal, currency: str = "usd", **kwargs
    ) -> PaymentResult:
        order_number = kwargs.get("order_number")
        success_url = kwargs["success_url"]
        cancel_url = kwargs["cancel_url"]
        description = kwargs.get("description", f"Order {order_number}")

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": currency,
                            "product_data": {"name": description},
                            "unit_amount": int(amount * 100),
                        },
                        "quantity": 1,
                    }
                ],
                metadata={"order_number": order_number},
                success_url=success_url,
                cancel_url=cancel_url,
            )
        except stripe.error.StripeError as e:
            return PaymentResult(success=False, message=str(e))

        return PaymentResult(
            success=True,
            transaction_id=session.id,
            amount=amount,
            currency=currency,
            metadata={"checkout_url": session.url, "session_id": session.id},
        )

    def verify_payment(self, transaction_id: str) -> PaymentResult:
        try:
            session = stripe.checkout.Session.retrieve(transaction_id)
        except stripe.error.StripeError as e:
            return PaymentResult(success=False, message=str(e))
        paid = session.payment_status == "paid"
        return PaymentResult(
            success=paid,
            transaction_id=session.id,
            message=session.payment_status,
            metadata={"payment_intent": session.payment_intent},
        )

    def refund_payment(
        self, transaction_id: str, amount: Optional[Decimal] = None
    ) -> PaymentResult:
        try:
            session = stripe.checkout.Session.retrieve(transaction_id)
            refund_kwargs = {"payment_intent": session.payment_intent}
            if amount is not None:
                refund_kwargs["amount"] = int(amount * 100)
            refund = stripe.Refund.create(**refund_kwargs)
        except stripe.error.StripeError as e:
            return PaymentResult(success=False, message=str(e))
        return PaymentResult(
            success=refund.status in ("succeeded", "pending"),
            transaction_id=refund.id,
            message=refund.status,
        )

    def construct_webhook_event(self, payload: bytes, sig_header: str):
        return stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)

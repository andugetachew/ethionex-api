from decimal import Decimal
import uuid
from .base import PaymentProvider, PaymentResult
from typing import Optional


class ChapaProvider(PaymentProvider):
    """Chapa payment provider for Ethiopia"""

    def __init__(self, api_key: str, webhook_secret: str = None):
        self.api_key = api_key
        self.webhook_secret = webhook_secret

    def initialize_payment(
        self, amount: Decimal, currency: str = "ETB", **kwargs
    ) -> PaymentResult:
        # Simulate payment initialization
        # In production, call Chapa API here
        transaction_id = f"CHAPA_{uuid.uuid4().hex[:12]}"

        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
            amount=amount,
            currency=currency,
            metadata={"checkout_url": f"https://checkout.chapa.co/{transaction_id}"},
        )

    def verify_payment(self, transaction_id: str) -> PaymentResult:
        # Simulate verification
        return PaymentResult(
            success=True, transaction_id=transaction_id, message="Payment verified"
        )

    def refund_payment(
        self, transaction_id: str, amount: Optional[Decimal] = None
    ) -> PaymentResult:
        # Simulate refund
        return PaymentResult(
            success=True, transaction_id=transaction_id, message="Refund processed"
        )

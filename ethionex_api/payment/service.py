# ethionex_api/payment/service.py
from decimal import Decimal
from django.conf import settings
from .base import PaymentResult
from .chapa import ChapaProvider
from .stripe_provider import StripeProvider


class PaymentService:
    """Payment abstraction service"""

    _providers = {
        "chapa": ChapaProvider,
        "stripe": StripeProvider,
    }

    def __init__(self, provider_name: str = "chapa"):
        if provider_name not in self._providers:
            raise ValueError(f"Unknown provider: {provider_name}")

        provider_class = self._providers[provider_name]
        self.provider = provider_class(
            api_key=getattr(settings, f"{provider_name.upper()}_API_KEY", ""),
            webhook_secret=getattr(
                settings, f"{provider_name.upper()}_WEBHOOK_SECRET", None
            ),
        )

    def process_payment(
        self, amount: Decimal, currency: str = "ETB", **kwargs
    ) -> PaymentResult:
        """Process payment using configured provider"""
        return self.provider.initialize_payment(amount, currency, **kwargs)

    def verify_payment(self, transaction_id: str) -> PaymentResult:
        """Verify payment status"""
        return self.provider.verify_payment(transaction_id)

    def refund_payment(
        self, transaction_id: str, amount: Decimal = None
    ) -> PaymentResult:
        """Process refund"""
        return self.provider.refund_payment(transaction_id, amount)

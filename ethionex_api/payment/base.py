# ethionex_api/payment/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Dict


@dataclass
class PaymentResult:
    """Standard payment result object"""

    success: bool
    transaction_id: Optional[str] = None
    message: str = ""
    amount: Optional[Decimal] = None
    currency: str = "ETB"
    metadata: Optional[Dict] = None


class PaymentProvider(ABC):
    """Abstract base class for all payment providers"""

    @abstractmethod
    def initialize_payment(
        self, amount: Decimal, currency: str, **kwargs
    ) -> PaymentResult:
        """Initialize a payment (for Chapa, Stripe, etc.)"""
        pass

    @abstractmethod
    def verify_payment(self, transaction_id: str) -> PaymentResult:
        """Verify payment status"""
        pass

    @abstractmethod
    def refund_payment(
        self, transaction_id: str, amount: Optional[Decimal] = None
    ) -> PaymentResult:
        """Process refund"""
        pass

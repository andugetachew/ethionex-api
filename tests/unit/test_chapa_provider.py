from decimal import Decimal

from ethionex_api.payment.chapa import ChapaProvider


class TestChapaProviderInit:
    def test_stores_api_key_and_webhook_secret(self):
        provider = ChapaProvider(api_key="chapa_key_123", webhook_secret="whsec_abc")
        assert provider.api_key == "chapa_key_123"
        assert provider.webhook_secret == "whsec_abc"


class TestInitializePayment:
    def test_returns_success_with_generated_transaction_id(self):
        provider = ChapaProvider(api_key="chapa_key_123")
        result = provider.initialize_payment(amount=Decimal("500.00"), currency="ETB")

        assert result.success is True
        assert result.transaction_id.startswith("CHAPA_")
        assert result.amount == Decimal("500.00")
        assert result.currency == "ETB"
        assert "checkout_url" in result.metadata

    def test_checkout_url_contains_transaction_id(self):
        provider = ChapaProvider(api_key="chapa_key_123")
        result = provider.initialize_payment(amount=Decimal("100"), currency="ETB")

        assert result.transaction_id in result.metadata["checkout_url"]

    def test_transaction_ids_are_unique(self):
        provider = ChapaProvider(api_key="chapa_key_123")
        result1 = provider.initialize_payment(amount=Decimal("100"), currency="ETB")
        result2 = provider.initialize_payment(amount=Decimal("100"), currency="ETB")

        assert result1.transaction_id != result2.transaction_id


class TestVerifyPayment:
    def test_always_returns_success(self):
        """
        Documents real behavior: this is a simulated implementation —
        verify_payment always returns success=True regardless of the
        transaction_id passed in, since there's no real Chapa API call.
        Worth knowing this is not yet a real integration.
        """
        provider = ChapaProvider(api_key="chapa_key_123")
        result = provider.verify_payment("any_transaction_id_even_fake")

        assert result.success is True
        assert result.message == "Payment verified"


class TestRefundPayment:
    def test_always_returns_success(self):
        """
        Documents real behavior: refund_payment is also fully
        simulated — always succeeds regardless of transaction_id or
        amount, since there's no real Chapa refund API call yet.
        """
        provider = ChapaProvider(api_key="chapa_key_123")
        result = provider.refund_payment("any_id", amount=Decimal("50"))

        assert result.success is True
        assert result.message == "Refund processed"
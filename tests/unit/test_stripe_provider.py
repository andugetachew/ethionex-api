import pytest
from decimal import Decimal
from unittest.mock import patch, Mock
import stripe

from ethionex_api.payment.stripe_provider import StripeProvider
from ethionex_api.payment.base import PaymentResult


class TestStripeProviderInit:
    def test_accepts_valid_test_key(self):
        provider = StripeProvider(api_key="sk_test_abc123")
        assert provider.api_key == "sk_test_abc123"

    def test_rejects_live_key(self):
        with pytest.raises(ValueError, match="TEST secret keys"):
            StripeProvider(api_key="sk_live_realkey")

    def test_allows_empty_key(self):
        # Falsy api_key skips the validation entirely (if api_key and not...)
        provider = StripeProvider(api_key="")
        assert provider.api_key == ""

    def test_sets_stripe_module_api_key(self):
        StripeProvider(api_key="sk_test_xyz")
        assert stripe.api_key == "sk_test_xyz"


class TestInitializePayment:
    @patch("ethionex_api.payment.stripe_provider.stripe.checkout.Session.create")
    def test_successful_checkout_session_creation(self, mock_create):
        mock_create.return_value = Mock(
            id="cs_test_123", url="https://checkout.stripe.com/session123"
        )
        provider = StripeProvider(api_key="sk_test_abc")

        result = provider.initialize_payment(
            amount=Decimal("49.99"),
            currency="usd",
            order_number="ORD-001",
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
        )

        assert result.success is True
        assert result.transaction_id == "cs_test_123"
        assert result.amount == Decimal("49.99")
        assert result.metadata["checkout_url"] == "https://checkout.stripe.com/session123"

    @patch("ethionex_api.payment.stripe_provider.stripe.checkout.Session.create")
    def test_converts_amount_to_cents(self, mock_create):
        mock_create.return_value = Mock(id="cs_1", url="http://x")
        provider = StripeProvider(api_key="sk_test_abc")

        provider.initialize_payment(
            amount=Decimal("49.99"), currency="usd",
            success_url="http://s", cancel_url="http://c",
        )

        _, kwargs = mock_create.call_args
        assert kwargs["line_items"][0]["price_data"]["unit_amount"] == 4999

    @patch("ethionex_api.payment.stripe_provider.stripe.checkout.Session.create")
    def test_stripe_error_returns_failed_result(self, mock_create):
        mock_create.side_effect = stripe.error.StripeError("card declined")
        provider = StripeProvider(api_key="sk_test_abc")

        result = provider.initialize_payment(
            amount=Decimal("10"), currency="usd",
            success_url="http://s", cancel_url="http://c",
        )

        assert result.success is False
        assert "card declined" in result.message

    @patch("ethionex_api.payment.stripe_provider.stripe.checkout.Session.create")
    def test_uses_default_description_from_order_number(self, mock_create):
        mock_create.return_value = Mock(id="cs_1", url="http://x")
        provider = StripeProvider(api_key="sk_test_abc")

        provider.initialize_payment(
            amount=Decimal("10"), currency="usd", order_number="ORD-42",
            success_url="http://s", cancel_url="http://c",
        )

        _, kwargs = mock_create.call_args
        product_name = kwargs["line_items"][0]["price_data"]["product_data"]["name"]
        assert product_name == "Order ORD-42"

    def test_missing_success_url_raises_key_error(self):
        provider = StripeProvider(api_key="sk_test_abc")
        with pytest.raises(KeyError):
            provider.initialize_payment(
                amount=Decimal("10"), currency="usd", cancel_url="http://c"
            )


class TestVerifyPayment:
    @patch("ethionex_api.payment.stripe_provider.stripe.checkout.Session.retrieve")
    def test_paid_session_returns_success(self, mock_retrieve):
        mock_retrieve.return_value = Mock(
            id="cs_123", payment_status="paid", payment_intent="pi_123"
        )
        provider = StripeProvider(api_key="sk_test_abc")

        result = provider.verify_payment("cs_123")

        assert result.success is True
        assert result.metadata["payment_intent"] == "pi_123"

    @patch("ethionex_api.payment.stripe_provider.stripe.checkout.Session.retrieve")
    def test_unpaid_session_returns_failure(self, mock_retrieve):
        mock_retrieve.return_value = Mock(
            id="cs_123", payment_status="unpaid", payment_intent=None
        )
        provider = StripeProvider(api_key="sk_test_abc")

        result = provider.verify_payment("cs_123")

        assert result.success is False
        assert result.message == "unpaid"

    @patch("ethionex_api.payment.stripe_provider.stripe.checkout.Session.retrieve")
    def test_stripe_error_returns_failed_result(self, mock_retrieve):
        mock_retrieve.side_effect = stripe.error.StripeError("session not found")
        provider = StripeProvider(api_key="sk_test_abc")

        result = provider.verify_payment("invalid_id")

        assert result.success is False
        assert "session not found" in result.message


class TestRefundPayment:
    @patch("ethionex_api.payment.stripe_provider.stripe.Refund.create")
    @patch("ethionex_api.payment.stripe_provider.stripe.checkout.Session.retrieve")
    def test_full_refund_succeeds(self, mock_retrieve, mock_refund_create):
        mock_retrieve.return_value = Mock(payment_intent="pi_123")
        mock_refund_create.return_value = Mock(id="re_123", status="succeeded")
        provider = StripeProvider(api_key="sk_test_abc")

        result = provider.refund_payment("cs_123")

        assert result.success is True
        assert result.transaction_id == "re_123"
        _, kwargs = mock_refund_create.call_args
        assert "amount" not in kwargs

    @patch("ethionex_api.payment.stripe_provider.stripe.Refund.create")
    @patch("ethionex_api.payment.stripe_provider.stripe.checkout.Session.retrieve")
    def test_partial_refund_includes_amount_in_cents(self, mock_retrieve, mock_refund_create):
        mock_retrieve.return_value = Mock(payment_intent="pi_123")
        mock_refund_create.return_value = Mock(id="re_123", status="succeeded")
        provider = StripeProvider(api_key="sk_test_abc")

        provider.refund_payment("cs_123", amount=Decimal("15.50"))

        _, kwargs = mock_refund_create.call_args
        assert kwargs["amount"] == 1550

    @patch("ethionex_api.payment.stripe_provider.stripe.checkout.Session.retrieve")
    def test_stripe_error_during_refund_returns_failure(self, mock_retrieve):
        mock_retrieve.side_effect = stripe.error.StripeError("not found")
        provider = StripeProvider(api_key="sk_test_abc")

        result = provider.refund_payment("bad_id")

        assert result.success is False

    @patch("ethionex_api.payment.stripe_provider.stripe.Refund.create")
    @patch("ethionex_api.payment.stripe_provider.stripe.checkout.Session.retrieve")
    def test_pending_refund_status_counts_as_success(self, mock_retrieve, mock_refund_create):
        mock_retrieve.return_value = Mock(payment_intent="pi_123")
        mock_refund_create.return_value = Mock(id="re_123", status="pending")
        provider = StripeProvider(api_key="sk_test_abc")

        result = provider.refund_payment("cs_123")

        assert result.success is True


class TestConstructWebhookEvent:
    @patch("ethionex_api.payment.stripe_provider.stripe.Webhook.construct_event")
    def test_delegates_to_stripe_webhook_construct_event(self, mock_construct):
        mock_construct.return_value = {"type": "checkout.session.completed"}
        provider = StripeProvider(api_key="sk_test_abc", webhook_secret="whsec_123")

        event = provider.construct_webhook_event(b"payload", "sig_header_value")

        assert event == {"type": "checkout.session.completed"}
        mock_construct.assert_called_once_with(b"payload", "sig_header_value", "whsec_123")
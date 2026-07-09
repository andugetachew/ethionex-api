"""
Tests for the payment integration (test-mode Stripe, simulated Chapa):
initialization, webhook handling, order creation, verification,
transaction history, and refunds.
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.urls import reverse

from cart.models import Cart
from orders.models import Order, PaymentTransaction, PendingCheckout

CHECKOUT_PAYLOAD = {
    "payment_method": "stripe",
    "full_name": "Test User",
    "phone_number": "0912345678",
    "address": "123 Test St",
    "city": "Addis Ababa",
}


def checkout_url(provider):
    return reverse("payment-checkout", args=[provider])


def webhook_url(provider):
    return reverse("payment-webhook", args=[provider])


# ---------------------------------------------------------------------------
# 1 & 2. Initialization, multiple providers
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCreateCheckoutView:
    @patch("orders.payment_views.PaymentService")
    def test_stripe_checkout_creates_pending_checkout_not_an_order(
        self, mock_service_cls, auth_client, test_cart
    ):
        mock_service = MagicMock()
        mock_service.process_payment.return_value = MagicMock(
            success=True,
            transaction_id="cs_test_abc",
            message="",
            metadata={"checkout_url": "https://checkout.stripe.com/test/cs_test_abc"},
        )
        mock_service_cls.return_value = mock_service

        response = auth_client.post(checkout_url("stripe"), CHECKOUT_PAYLOAD)

        assert response.status_code == 201
        assert response.data["mode"] == "test"
        assert Order.objects.count() == 0
        pc = PendingCheckout.objects.get(provider_reference="cs_test_abc")
        assert pc.provider == "stripe"

    @patch("orders.payment_views.PaymentService")
    def test_chapa_checkout_is_simulated(
        self, mock_service_cls, auth_client, test_cart
    ):
        mock_service = MagicMock()
        mock_service.process_payment.return_value = MagicMock(
            success=True,
            transaction_id="CHAPA_abc123",
            message="",
            metadata={"checkout_url": "https://checkout.chapa.co/CHAPA_abc123"},
        )
        mock_service_cls.return_value = mock_service

        payload = {**CHECKOUT_PAYLOAD, "payment_method": "chapa"}
        response = auth_client.post(checkout_url("chapa"), payload)

        assert response.status_code == 201
        assert response.data["mode"] == "simulated"
        pc = PendingCheckout.objects.get(provider_reference="CHAPA_abc123")
        assert pc.provider == "chapa"

    def test_rejects_unknown_provider(self, auth_client, test_cart):
        response = auth_client.post(checkout_url("paypal"), CHECKOUT_PAYLOAD)
        assert response.status_code == 400

    def test_rejects_empty_cart(self, auth_client, test_user):
        Cart.objects.get_or_create(user=test_user)
        response = auth_client.post(checkout_url("stripe"), CHECKOUT_PAYLOAD)
        assert response.status_code == 400

    def test_requires_authentication(self, api_client, test_cart):
        response = api_client.post(checkout_url("stripe"), CHECKOUT_PAYLOAD)
        assert response.status_code == 401

    @patch("orders.payment_views.PaymentService")
    def test_logs_transaction_history_on_init(
        self, mock_service_cls, auth_client, test_cart, test_user
    ):
        mock_service = MagicMock()
        mock_service.process_payment.return_value = MagicMock(
            success=True,
            transaction_id="cs_test_xyz",
            message="",
            metadata={"checkout_url": "https://checkout.stripe.com/test/cs_test_xyz"},
        )
        mock_service_cls.return_value = mock_service

        auth_client.post(checkout_url("stripe"), CHECKOUT_PAYLOAD)

        txn = PaymentTransaction.objects.get(transaction_id="cs_test_xyz")
        assert txn.kind == "initialize"
        assert txn.success is True
        assert txn.user == test_user


# ---------------------------------------------------------------------------
# 3 & 5. Webhook -> Order Created -> Inventory Updated -> Seller Notified
#          -> Receipt Generated
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPaymentWebhook:
    def _pending_checkout(
        self, test_user, test_product, provider="stripe", ref="cs_test_abc"
    ):
        return PendingCheckout.objects.create(
            user=test_user,
            provider=provider,
            provider_reference=ref,
            cart_snapshot=[
                {
                    "product_id": test_product.id,
                    "quantity": 2,
                    "price": str(test_product.price),
                }
            ],
            full_name="Test User",
            phone_number="0912345678",
            address="123 Test St",
            city="Addis Ababa",
            subtotal=test_product.price * 2,
            total=test_product.price * 2,
        )

    def test_stripe_invalid_signature_rejected(self, api_client):
        response = api_client.post(
            webhook_url("stripe"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="bad_signature",
        )
        assert response.status_code == 400

    @patch("orders.payment_views.EmailService.send_payment_receipt")
    @patch("orders.payment_views.EmailService.send_seller_order_notification")
    @patch("orders.payment_views.stripe.Webhook.construct_event")
    def test_stripe_full_pipeline_on_payment_success(
        self,
        mock_construct_event,
        mock_notify_seller,
        mock_receipt,
        api_client,
        test_user,
        test_product,
    ):
        starting_stock = test_product.stock_quantity
        self._pending_checkout(test_user, test_product)

        mock_construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_test_abc", "payment_intent": "pi_test_123"}},
        }

        response = api_client.post(
            webhook_url("stripe"),
            data=b"{}",
            content_type="application/json",
            HTTP_STRIPE_SIGNATURE="valid_test_signature",
        )
        assert response.status_code == 200

        order = Order.objects.get(stripe_checkout_session_id="cs_test_abc")
        assert order.status == "paid"
        assert order.items.count() == 1

        test_product.refresh_from_db()
        assert test_product.stock_quantity == starting_stock - 2

        mock_notify_seller.assert_called_once()
        mock_receipt.assert_called_once()

        txn = PaymentTransaction.objects.get(
            transaction_id="cs_test_abc", kind="webhook"
        )
        assert txn.success is True

    @patch("orders.payment_views.stripe.Webhook.construct_event")
    def test_stripe_duplicate_webhook_does_not_double_create_order(
        self, mock_construct_event, api_client, test_user, test_product
    ):
        self._pending_checkout(test_user, test_product)
        mock_construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_test_abc", "payment_intent": "pi_test_123"}},
        }

        for _ in range(2):
            api_client.post(
                webhook_url("stripe"),
                data=b"{}",
                content_type="application/json",
                HTTP_STRIPE_SIGNATURE="valid_test_signature",
            )

        assert (
            Order.objects.filter(stripe_checkout_session_id="cs_test_abc").count() == 1
        )

    def test_chapa_webhook_requires_shared_secret(self, api_client, settings):
        settings.CHAPA_WEBHOOK_SECRET = "expected-secret"
        response = api_client.post(
            webhook_url("chapa"),
            {"tx_ref": "CHAPA_abc", "status": "success"},
            HTTP_X_CHAPA_SIGNATURE="wrong-secret",
        )
        assert response.status_code == 400

    @patch("orders.payment_views.EmailService.send_payment_receipt")
    @patch("orders.payment_views.EmailService.send_seller_order_notification")
    def test_chapa_webhook_success_creates_order(
        self,
        mock_notify_seller,
        mock_receipt,
        api_client,
        test_user,
        test_product,
        settings,
    ):
        settings.CHAPA_WEBHOOK_SECRET = "expected-secret"
        self._pending_checkout(
            test_user, test_product, provider="chapa", ref="CHAPA_abc"
        )

        response = api_client.post(
            webhook_url("chapa"),
            {"tx_ref": "CHAPA_abc", "status": "success"},
            HTTP_X_CHAPA_SIGNATURE="expected-secret",
        )
        assert response.status_code == 200

        order = Order.objects.get(payment_method="chapa")
        assert order.status == "paid"

    def test_chapa_webhook_failed_status_does_not_create_order(
        self, api_client, test_user, test_product, settings
    ):
        settings.CHAPA_WEBHOOK_SECRET = "expected-secret"
        self._pending_checkout(
            test_user, test_product, provider="chapa", ref="CHAPA_fail"
        )

        response = api_client.post(
            webhook_url("chapa"),
            {"tx_ref": "CHAPA_fail", "status": "failed"},
            HTTP_X_CHAPA_SIGNATURE="expected-secret",
        )
        assert response.status_code == 200
        assert Order.objects.count() == 0


# ---------------------------------------------------------------------------
# 4. Payment verification
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestVerifyPaymentView:
    @patch("orders.payment_views.PaymentService")
    def test_verifies_payment_status(
        self, mock_service_cls, auth_client, test_user, test_product
    ):
        pc = PendingCheckout.objects.create(
            user=test_user,
            provider="stripe",
            provider_reference="cs_test_verify",
            cart_snapshot=[
                {
                    "product_id": test_product.id,
                    "quantity": 1,
                    "price": str(test_product.price),
                }
            ],
            full_name="Test User",
            phone_number="0912345678",
            address="123 Test St",
            city="Addis Ababa",
            subtotal=test_product.price,
            total=test_product.price,
        )
        mock_service = MagicMock()
        mock_service.verify_payment.return_value = MagicMock(
            success=True, message="paid"
        )
        mock_service_cls.return_value = mock_service

        url = reverse("payment-verify", args=["cs_test_verify"])
        response = auth_client.get(url)

        assert response.status_code == 200
        assert response.data["paid"] is True
        assert PaymentTransaction.objects.filter(
            transaction_id="cs_test_verify", kind="verify"
        ).exists()

    def test_unknown_transaction_returns_404(self, auth_client):
        url = reverse("payment-verify", args=["cs_test_doesnotexist"])
        response = auth_client.get(url)
        assert response.status_code == 404


# ---------------------------------------------------------------------------
# 6. Payment transaction history
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPaymentTransactionHistoryView:
    def test_lists_only_own_transactions(
        self, auth_client, test_user, django_user_model
    ):
        other_user = django_user_model.objects.create_user(
            username="other", email="other@test.com", password="SecurePass123"
        )
        PaymentTransaction.objects.create(
            user=test_user,
            provider="stripe",
            kind="initialize",
            transaction_id="cs_mine",
            amount=Decimal("10.00"),
            success=True,
        )
        PaymentTransaction.objects.create(
            user=other_user,
            provider="stripe",
            kind="initialize",
            transaction_id="cs_not_mine",
            amount=Decimal("10.00"),
            success=True,
        )

        url = reverse("payment-history")
        response = auth_client.get(url)

        assert response.status_code == 200
        transaction_ids = [t["transaction_id"] for t in response.data]
        assert "cs_mine" in transaction_ids
        assert "cs_not_mine" not in transaction_ids


# ---------------------------------------------------------------------------
# 7. Refund API
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestRefundPaymentView:
    @patch("orders.payment_views.PaymentService")
    def test_admin_can_refund_paid_order(
        self, mock_service_cls, admin_client, test_order
    ):
        test_order.status = "paid"
        test_order.payment_method = "stripe"
        test_order.stripe_checkout_session_id = "cs_test_refund"
        test_order.save()

        mock_service = MagicMock()
        mock_service.refund_payment.return_value = MagicMock(
            success=True, transaction_id="re_test_123", message=""
        )
        mock_service_cls.return_value = mock_service

        url = reverse("order-refund", args=[test_order.order_number])
        response = admin_client.post(url)

        assert response.status_code == 200
        test_order.refresh_from_db()
        assert test_order.status == "refunded"
        assert PaymentTransaction.objects.filter(
            order=test_order, kind="refund", success=True
        ).exists()

    def test_non_admin_cannot_refund(self, auth_client, test_order):
        test_order.status = "paid"
        test_order.save()
        url = reverse("order-refund", args=[test_order.order_number])
        response = auth_client.post(url)
        assert response.status_code == 403

    def test_cannot_refund_pending_order(self, admin_client, test_order):
        url = reverse("order-refund", args=[test_order.order_number])
        response = admin_client.post(url)
        assert response.status_code == 400

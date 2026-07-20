# orders/payment_views.py
"""
Payment endpoints — TEST/SIMULATED MODE ONLY.

Ethiopia has no licensed setup for taking real charges yet: Stripe
doesn't operate/support ETB there, and Chapa (the real option) needs
business registration that hasn't been completed. So:

  - Stripe runs against its real sandbox (test API keys, test webhook
    signing secret, Stripe's published test cards e.g. 4242 4242 4242
    4242).
  - Chapa is fully simulated (ChapaProvider never calls a real API —
    it fabricates a transaction id and a fake checkout URL) until
    business registration is done and it can be swapped for real calls.

Covers: payment initialization, multiple providers (Stripe + Chapa),
webhook handling, payment verification, order status updates after
payment, payment transaction history, and a refund API (real for
Stripe test mode, simulated for Chapa).

Flow:
    Customer -> Checkout -> Payment -> Order Created -> Inventory
    Updated -> Seller Notified -> Receipt Generated
"""

import logging
from decimal import Decimal, InvalidOperation

import stripe
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from cart.models import Cart
from ethionex_api.payment.service import PaymentService
from notifications.email_service import EmailService
from products.models import Product

from .models import Order, OrderItem, PaymentTransaction, PendingCheckout
from .serializers import CreateOrderSerializer

from .services import InventoryService

logger = logging.getLogger(__name__)

VALID_PROVIDERS = {"stripe", "chapa"}
PROVIDER_CURRENCY = {
    "stripe": lambda: settings.STRIPE_CURRENCY,
    "chapa": lambda: settings.CHAPA_CURRENCY,
}


class CreateCheckoutView(APIView):
    """
    POST /api/v1/orders/checkout/<provider>/   provider = "stripe" | "chapa"

    Starts a checkout for the user's current cart with the given
    provider. No Order exists yet — only a PendingCheckout snapshot.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, provider):
        if provider not in VALID_PROVIDERS:
            return Response(
                {
                    "error": f"Unknown provider '{provider}'. Use one of: {sorted(VALID_PROVIDERS)}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CreateOrderSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            return Response(
                {"error": "Your cart is empty"}, status=status.HTTP_400_BAD_REQUEST
            )

        if not cart.items.exists():
            return Response(
                {"error": "Cannot check out an empty cart"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        for cart_item in cart.items.all():
            if cart_item.quantity > cart_item.product.stock_quantity:
                return Response(
                    {
                        "error": f"Insufficient stock for {cart_item.product.title}. "
                        f"Available: {cart_item.product.stock_quantity}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        subtotal = sum(item.product.price * item.quantity for item in cart.items.all())
        delivery_fee = serializer.validated_data.get("delivery_fee", 0)
        total = subtotal + delivery_fee
        currency = PROVIDER_CURRENCY[provider]()

        cart_snapshot = [
            {
                "product_id": item.product.id,
                "quantity": item.quantity,
                "price": str(item.product.price),
            }
            for item in cart.items.all()
        ]

        pending_checkout = PendingCheckout.objects.create(
            user=request.user,
            provider=provider,
            provider_reference="",  # filled in once the provider returns a reference
            cart_snapshot=cart_snapshot,
            payment_method=provider,
            full_name=serializer.validated_data["full_name"],
            phone_number=serializer.validated_data["phone_number"],
            address=serializer.validated_data["address"],
            city=serializer.validated_data["city"],
            sub_city=serializer.validated_data.get("sub_city", ""),
            notes=serializer.validated_data.get("notes", ""),
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total=total,
        )

        success_url = request.data.get(
            "success_url", f"{settings.FRONTEND_URL}/checkout/success"
        )
        cancel_url = request.data.get(
            "cancel_url", f"{settings.FRONTEND_URL}/checkout/cancelled"
        )

        try:
            service = PaymentService(provider_name=provider)
        except ValueError as e:
            pending_checkout.delete()
            logger.error(f"{provider} provider misconfigured: {e}")
            return Response(
                {"error": f"{provider} payments are not configured."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        result = service.process_payment(
            amount=total,
            currency=currency,
            order_number=f"checkout-{pending_checkout.id}",
            description=f"EthioNex cart checkout ({cart.items.count()} item(s))",
            success_url=success_url,
            cancel_url=cancel_url,
        )

        PaymentTransaction.objects.create(
            user=request.user,
            order=None,
            provider=provider,
            kind="initialize",
            transaction_id=result.transaction_id or "",
            amount=total,
            currency=currency,
            success=result.success,
            message=result.message,
        )

        if not result.success:
            pending_checkout.delete()
            return Response(
                {"error": result.message}, status=status.HTTP_502_BAD_GATEWAY
            )

        pending_checkout.provider_reference = result.transaction_id
        pending_checkout.save(update_fields=["provider_reference"])

        return Response(
            {
                "provider": provider,
                "checkout_url": result.metadata["checkout_url"],
                "transaction_id": result.transaction_id,
                "mode": "test" if provider == "stripe" else "simulated",
            },
            status=status.HTTP_201_CREATED,
        )


@method_decorator(csrf_exempt, name="dispatch")
class PaymentWebhookView(APIView):
    """
    POST /api/v1/orders/webhook/<provider>/

    Stripe: real signature-verified webhook.
    Chapa: simulated — trusts a shared-secret header since ChapaProvider
    itself is simulated (no real Chapa account to receive real webhooks
    from yet).
    """

    permission_classes = []
    authentication_classes = []

    def post(self, request, provider):
        if provider not in VALID_PROVIDERS:
            return Response({"error": "Unknown provider"}, status=400)

        if provider == "stripe":
            return self._handle_stripe(request)
        return self._handle_chapa(request)

    def _handle_stripe(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError) as e:
            logger.warning(f"Stripe webhook rejected: {e}")
            return Response({"error": "Invalid payload or signature"}, status=400)

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            self._complete_checkout(
                provider="stripe",
                provider_reference=session.get("id"),
                paid=True,
                provider_transaction_id=session.get("payment_intent", "") or "",
            )

        return Response({"received": True})

    def _handle_chapa(self, request):
        shared_secret = request.META.get("HTTP_X_CHAPA_SIGNATURE", "")
        if (
            not settings.CHAPA_WEBHOOK_SECRET
            or shared_secret != settings.CHAPA_WEBHOOK_SECRET
        ):
            logger.warning("Chapa webhook rejected: bad or missing signature")
            return Response({"error": "Invalid signature"}, status=400)

        tx_ref = request.data.get("tx_ref")
        chapa_status = request.data.get("status")  # "success" | "failed"

        if not tx_ref:
            return Response({"error": "Missing tx_ref"}, status=400)

        self._complete_checkout(
            provider="chapa",
            provider_reference=tx_ref,
            paid=(chapa_status == "success"),
            provider_transaction_id=tx_ref,
        )
        return Response({"received": True})

    @transaction.atomic
    def _complete_checkout(
        self, provider, provider_reference, paid, provider_transaction_id
    ):
        pending_checkout = (
            PendingCheckout.objects.select_for_update()
            .filter(provider=provider, provider_reference=provider_reference)
            .first()
        )
        if pending_checkout is None:
            logger.warning(
                f"Webhook: no PendingCheckout for {provider}:{provider_reference}"
            )
            return

        if pending_checkout.consumed_at is not None:
            return

        if not paid:
            pending_checkout.consumed_at = timezone.now()
            pending_checkout.save(update_fields=["consumed_at"])
            PaymentTransaction.objects.create(
                user=pending_checkout.user,
                order=None,
                provider=provider,
                kind="webhook",
                transaction_id=provider_reference,
                amount=pending_checkout.total,
                success=False,
                message="Payment failed or was cancelled",
            )
            return

        order = Order.objects.create(
            user=pending_checkout.user,
            status="paid",
            payment_method=provider,
            full_name=pending_checkout.full_name,
            phone_number=pending_checkout.phone_number,
            address=pending_checkout.address,
            city=pending_checkout.city,
            sub_city=pending_checkout.sub_city,
            subtotal=pending_checkout.subtotal,
            delivery_fee=pending_checkout.delivery_fee,
            total=pending_checkout.total,
            notes=pending_checkout.notes,
            stripe_checkout_session_id=(
                provider_reference if provider == "stripe" else None
            ),
            stripe_payment_intent_id=(
                provider_transaction_id if provider == "stripe" else None
            ),
            paid_at=timezone.now(),
        )

        sellers_to_notify = set()
        stock_failures = []
        for line in pending_checkout.cart_snapshot:
            product = Product.objects.select_for_update().get(id=line["product_id"])
            quantity = line["quantity"]

            OrderItem.objects.create(
                order=order, product=product, quantity=quantity, price=line["price"]
            )

            try:
                InventoryService.reserve_stock(product.id, quantity)
            except ValidationError as e:
                logger.critical(
                    f"Stock reservation FAILED for paid order {order.order_number} "
                    f"(product {product.id}, qty {quantity}): {e}"
                )
                stock_failures.append(
                    {
                        "product_id": product.id,
                        "product_title": getattr(product, "title", str(product.id)),
                        "error": str(e),
                    }
                )

            if product.seller_id:
                sellers_to_notify.add(product.seller)

        if stock_failures:
            order.status = "needs_review"
            failure_note = (
                "STOCK RESERVATION FAILURES (requires manual review): "
                + "; ".join(
                    f"{f['product_title']} (id={f['product_id']}): {f['error']}"
                    for f in stock_failures
                )
            )
            order.notes = (
                f"{order.notes}\n{failure_note}".strip()
                if order.notes
                else failure_note
            )
            order.save(update_fields=["status", "notes"])

            PaymentTransaction.objects.create(
                user=order.user,
                order=order,
                provider=provider,
                kind="webhook",
                transaction_id=provider_reference,
                amount=order.total,
                success=True,
                message=f"Payment confirmed but stock reservation failed for {len(stock_failures)} item(s) — flagged for review",
            )
        else:

            PaymentTransaction.objects.create(
                user=order.user,
                order=order,
                provider=provider,
                kind="webhook",
                transaction_id=provider_reference,
                amount=order.total,
                success=True,
                message="Payment confirmed",
            )

        cart = Cart.objects.filter(user=pending_checkout.user).first()
        if cart:
            cart.items.filter(
                product_id__in=[
                    item["product_id"] for item in pending_checkout.cart_snapshot
                ]
            ).delete()

        pending_checkout.consumed_at = timezone.now()
        pending_checkout.save(update_fields=["consumed_at"])

        for seller in sellers_to_notify:
            try:
                EmailService.send_seller_order_notification(order, seller)
            except Exception as e:
                logger.error(
                    f"Seller notification failed for order {order.order_number}: {e}"
                )

        if stock_failures:
            try:
                EmailService.send_admin_alert(
                    subject=f"Stock reservation failed on paid order {order.order_number}",
                    message=failure_note,
                )
            except Exception as e:
                logger.error(
                    f"Admin alert email failed for order {order.order_number}: {e}"
                )

        try:
            EmailService.send_payment_receipt(
                order,
                {"transaction_id": provider_transaction_id, "amount": str(order.total)},
            )
        except Exception as e:
            logger.error(f"Receipt email failed for order {order.order_number}: {e}")


class VerifyPaymentView(APIView):
    """GET /api/v1/orders/payments/<transaction_id>/verify/"""

    permission_classes = [IsAuthenticated]

    def get(self, request, transaction_id):
        pending_checkout = PendingCheckout.objects.filter(
            provider_reference=transaction_id, user=request.user
        ).first()

        if pending_checkout is None:
            return Response(
                {"error": "No checkout found for this transaction"}, status=404
            )

        order = Order.objects.filter(
            stripe_checkout_session_id=transaction_id, user=request.user
        ).first()

        if order is None:

            confirming_txn = PaymentTransaction.objects.filter(
                user=request.user,
                provider=pending_checkout.provider,
                transaction_id=transaction_id,
                kind="webhook",
                success=True,
                order__isnull=False,
            ).first()
            if confirming_txn:
                order = confirming_txn.order

        service = PaymentService(provider_name=pending_checkout.provider)
        result = service.verify_payment(transaction_id)

        PaymentTransaction.objects.create(
            user=request.user,
            order=order,
            provider=pending_checkout.provider,
            kind="verify",
            transaction_id=transaction_id,
            amount=pending_checkout.total,
            success=result.success,
            message=result.message,
        )

        return Response(
            {
                "paid": result.success,
                "status": result.message,
                "order_number": order.order_number if order else None,
            }
        )


class PaymentTransactionHistoryView(APIView):
    """GET /api/v1/orders/payments/history/"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        transactions = PaymentTransaction.objects.filter(user=request.user)

        data = [
            {
                "id": t.id,
                "provider": t.provider,
                "kind": t.kind,
                "transaction_id": t.transaction_id,
                "amount": str(t.amount) if t.amount is not None else None,
                "currency": t.currency,
                "success": t.success,
                "message": t.message,
                "order_number": t.order.order_number if t.order else None,
                "created_at": t.created_at,
            }
            for t in transactions
        ]
        return Response(data)


class RefundPaymentView(APIView):
    """
    POST /api/v1/orders/<order_number>/refund/

    Admin-only. Refunds a paid order in full or partially (test mode /
    simulated).
    """

    permission_classes = [IsAdminUser]

    def post(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number)

        if order.status not in ("paid", "processing"):
            return Response(
                {"error": f"Order is '{order.status}', cannot be refunded."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        provider = order.payment_method
        if provider not in VALID_PROVIDERS:
            return Response(
                {
                    "error": f"Order was paid via '{provider}', which has no refund flow."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        provider_reference = (
            order.stripe_checkout_session_id if provider == "stripe" else None
        )
        if not provider_reference:
            txn = order.payment_transactions.filter(
                kind="webhook", success=True
            ).first()
            provider_reference = txn.transaction_id if txn else None

        if not provider_reference:
            return Response(
                {"error": "No payment reference found for this order."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        raw_amount = request.data.get("amount")
        amount = None
        if raw_amount is not None:
            try:
                amount = Decimal(str(raw_amount))
            except (InvalidOperation, TypeError, ValueError):
                return Response(
                    {"error": "amount must be a valid number."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if amount <= 0:
                return Response(
                    {"error": "amount must be greater than zero."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if amount > order.total:
                return Response(
                    {
                        "error": f"amount ({amount}) cannot exceed the order total ({order.total})."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        service = PaymentService(provider_name=provider)
        result = service.refund_payment(provider_reference, amount)

        PaymentTransaction.objects.create(
            user=order.user,
            order=order,
            provider=provider,
            kind="refund",
            transaction_id=result.transaction_id or provider_reference,
            amount=amount or order.total,
            success=result.success,
            message=result.message,
        )

        if not result.success:
            return Response(
                {"error": result.message}, status=status.HTTP_502_BAD_GATEWAY
            )

        order.status = "refunded"
        order.refunded_at = timezone.now()
        order.save(update_fields=["status", "refunded_at"])

        return Response(
            {
                "order_number": order.order_number,
                "refund_transaction_id": result.transaction_id,
                "mode": "test" if provider == "stripe" else "simulated",
            }
        )

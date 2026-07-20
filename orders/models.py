# orders/models.py
from django.db import models
from django.conf import settings
from products.models import Product
from cart.models import Cart
from django.utils.crypto import get_random_string


class Order(models.Model):
    """Order model for purchases"""

    STATUS_CHOICES = [
        ("pending", "Pending Payment"),
        ("paid", "Paid"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
        ("needs_review", "Needs Review"),  # FIX: paid order with a stock
        # reservation failure — see orders/payment_views.py and
        # orders/state_machine.py
    ]

    PAYMENT_CHOICES = [
        ("cash", "Cash on Delivery"),
        ("telebirr", "Telebirr"),
        ("chapa", "Chapa"),
        ("bank", "Bank Transfer"),
        ("stripe", "Stripe (Test Mode)"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    order_number = models.CharField(max_length=20, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(
        max_length=20, choices=PAYMENT_CHOICES, default="cash"
    )

    # Address information
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    sub_city = models.CharField(max_length=100, blank=True)

    # Order totals
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    # Tracking
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    # Order Status History
    status_history = models.JSONField(default=list, blank=True)

    # Stripe (test-mode) payment tracking
    stripe_checkout_session_id = models.CharField(max_length=200, blank=True, null=True)
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    refunded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number} - {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import datetime

            date_str = datetime.datetime.now().strftime("%Y%m%d")
            last_order = Order.objects.filter(
                order_number__startswith=f"ORD-{date_str}"
            ).count()
            self.order_number = f"ORD-{date_str}-{last_order + 1:04d}"
        super().save(*args, **kwargs)

    def add_status_history(self, status, note=""):
        """Add status change to history"""
        from django.utils import timezone

        history_entry = {
            "status": status,
            "timestamp": timezone.now().isoformat(),
            "note": note,
        }
        if not self.status_history:
            self.status_history = []
        self.status_history.append(history_entry)
        self.save()

    def update_status(self, new_status, note=""):
        """Update order status with history tracking"""
        self.status = new_status
        self.add_status_history(new_status, note)

        from django.utils import timezone

        if new_status == "shipped" and not self.shipped_at:
            self.shipped_at = timezone.now()
        elif new_status == "delivered" and not self.delivered_at:
            self.delivered_at = timezone.now()

        self.save()


class PendingCheckout(models.Model):
    """
    Snapshot of a cart + shipping details taken the moment a payment
    provider checkout is started (a real Stripe Checkout Session, or a
    simulated Chapa initialization).

    The real Order is only created AFTER the provider confirms payment
    (see PaymentWebhookView), matching:
    Checkout -> Payment -> Order Created -> Inventory Updated ->
    Seller Notified -> Receipt Generated.

    This snapshot exists because the webhook can't safely re-read the
    live cart (the user might have changed it, or it could be cleared
    by then) — it needs a frozen record of what was actually paid for.
    """

    PROVIDER_CHOICES = [
        ("stripe", "Stripe (Test Mode)"),
        ("chapa", "Chapa (Simulated)"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.CharField(
        max_length=20, choices=PROVIDER_CHOICES, default="stripe"
    )
    provider_reference = models.CharField(max_length=200, unique=True)

    cart_snapshot = models.JSONField()  # [{product_id, quantity, price}, ...]

    payment_method = models.CharField(max_length=20, default="stripe")
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    sub_city = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    created_at = models.DateTimeField(auto_now_add=True)
    consumed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"PendingCheckout({self.provider}:{self.provider_reference})"


class OrderItem(models.Model):
    """Individual items in an order"""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(
        max_digits=10, decimal_places=2
    )  # Price at time of purchase

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def subtotal(self):
        return self.price * self.quantity


class OrderStatusLog(models.Model):
    order = models.ForeignKey(
        "Order", on_delete=models.CASCADE, related_name="status_logs"
    )
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    reason = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.order.id}: {self.old_status} → {self.new_status}"


class PaymentTransaction(models.Model):
    """
    Log of every payment attempt (initialize / verify / refund), across
    providers, whether it succeeded or failed. This is the payment
    transaction history — independent of order status, since a failed
    or duplicate payment attempt should still show up here.
    """

    KIND_CHOICES = [
        ("initialize", "Initialize"),
        ("verify", "Verify"),
        ("webhook", "Webhook Confirmation"),
        ("refund", "Refund"),
    ]

    PROVIDER_CHOICES = [
        ("stripe", "Stripe (Test Mode)"),
        ("chapa", "Chapa (Simulated)"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="payment_transactions",
    )
    order = models.ForeignKey(
        "Order",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="payment_transactions",
    )
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    transaction_id = models.CharField(max_length=200, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, blank=True)
    success = models.BooleanField(default=False)
    message = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.provider}:{self.kind} - {self.transaction_id} ({'ok' if self.success else 'failed'})"

from django.db import models
from django.conf import settings
from products.models import Product
from cart.models import Cart
from django.utils.crypto import get_random_string


class Order(models.Model):
    """Order model for purchases"""

    STATUS_CHOICES = [
        ("pending", "Pending Payment"),
        ("processing", "Processing"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
        ("refunded", "Refunded"),
    ]

    PAYMENT_CHOICES = [
        ("cash", "Cash on Delivery"),
        ("telebirr", "Telebirr"),
        ("chapa", "Chapa"),
        ("bank", "Bank Transfer"),
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
    # Order Tracking Fields (add these)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    shipped_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    # Order Status History
    status_history = models.JSONField(default=list, blank=True)

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"ORD-{get_random_string(8).upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_number}"

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

        # Update timestamps based on status
        from django.utils import timezone

        if new_status == "shipped" and not self.shipped_at:
            self.shipped_at = timezone.now()
        elif new_status == "delivered" and not self.delivered_at:
            self.delivered_at = timezone.now()

        self.save()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number} - {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number: ORD-20260402-0001
            import datetime

            date_str = datetime.datetime.now().strftime("%Y%m%d")
            last_order = Order.objects.filter(
                order_number__startswith=f"ORD-{date_str}"
            ).count()
            self.order_number = f"ORD-{date_str}-{last_order + 1:04d}"
        super().save(*args, **kwargs)


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

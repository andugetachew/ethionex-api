# tests/unit/test_models.py
import pytest
from django.core.exceptions import ValidationError
from products.models import Product, Category
from orders.models import Order


@pytest.mark.django_db
class TestProductModel:

    def test_product_creation(self, test_product):
        assert test_product.title == "Test Laptop"
        assert float(test_product.price) == 999.99
        assert test_product.stock_quantity == 50
        assert test_product.is_active is True

    def test_product_str(self, test_product):
        assert str(test_product) == "Test Laptop"

    def test_negative_stock_fails_validation(self, test_product):
        test_product.stock_quantity = -5
        with pytest.raises(ValidationError):
            test_product.full_clean()

    def test_soft_delete(self, test_product):
        test_product.soft_delete()
        assert test_product.is_deleted is True
        assert test_product.is_active is False

    def test_soft_deleted_excluded_from_active_qs(self, test_product):
        test_product.soft_delete()
        assert not Product.objects.filter(pk=test_product.pk, is_active=True).exists()


@pytest.mark.django_db
class TestOrderModel:

    def test_order_creation(self, test_order):
        assert test_order.order_number == "TEST123"
        assert float(test_order.total) == 1999.98
        assert test_order.status == "pending"

    def test_order_number_auto_generated(self, test_user):
        """Order without explicit order_number gets one on save."""
        order = Order.objects.create(
            user=test_user,
            full_name="Auto",
            phone_number="09",
            address="Addr",
            city="City",
            payment_method="cash",
            subtotal=100,
            total=100,
        )
        assert order.order_number
        assert order.order_number.startswith("ORD-")

    def test_add_status_history(self, test_order):
        test_order.add_status_history("paid", "Payment received")
        assert len(test_order.status_history) == 1
        assert test_order.status_history[0]["status"] == "paid"

    def test_update_status_sets_shipped_at(self, test_order):
        test_order.update_status("shipped")
        assert test_order.shipped_at is not None

    def test_update_status_sets_delivered_at(self, test_order):
        test_order.update_status("delivered")
        assert test_order.delivered_at is not None

    def test_order_str(self, test_order):
        assert "TEST123" in str(test_order)

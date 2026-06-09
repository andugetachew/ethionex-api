# tests/integration/test_inventory.py
import pytest
from django.core.exceptions import ValidationError
from orders.services import InventoryService
from products.models import Product


@pytest.mark.django_db
class TestInventoryService:

    def test_reserve_reduces_stock(self, test_product):
        before = test_product.stock_quantity
        InventoryService.reserve_stock(test_product.id, 3)
        test_product.refresh_from_db()
        assert test_product.stock_quantity == before - 3

    def test_reserve_insufficient_raises(self, test_product):
        with pytest.raises(ValidationError):
            InventoryService.reserve_stock(test_product.id, 999)

    def test_release_restores_stock(self, test_product):
        before = test_product.stock_quantity
        InventoryService.reserve_stock(test_product.id, 5)
        InventoryService.release_stock(test_product.id, 5)
        test_product.refresh_from_db()
        assert test_product.stock_quantity == before

    def test_check_availability_true(self, test_product):
        assert InventoryService.check_stock_availability(
            test_product.id, test_product.stock_quantity
        ) is True

    def test_check_availability_false(self, test_product):
        assert InventoryService.check_stock_availability(
            test_product.id, test_product.stock_quantity + 1
        ) is False

    def test_reserve_atomic_rollback_on_error(self, test_product):
        """Failed reserve must not change stock."""
        before = test_product.stock_quantity
        try:
            InventoryService.reserve_stock(test_product.id, 9999)
        except ValidationError:
            pass
        test_product.refresh_from_db()
        assert test_product.stock_quantity == before
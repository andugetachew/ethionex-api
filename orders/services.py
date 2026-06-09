from django.db import transaction
from django.core.exceptions import ValidationError
from products.models import Product


class InventoryService:
    @staticmethod
    @transaction.atomic
    def reserve_stock(product_id, quantity):
        """Reserve stock with row lock to prevent overselling"""
        product = Product.objects.select_for_update().get(id=product_id)

        if product.stock_quantity < quantity:
            raise ValidationError(
                f"Not enough stock. Available: {product.stock_quantity}"
            )

        product.stock_quantity -= quantity
        product.save()
        return product

    @staticmethod
    @transaction.atomic
    def release_stock(product_id, quantity):
        """Release reserved stock (for cancelled orders)"""
        product = Product.objects.select_for_update().get(id=product_id)
        product.stock_quantity += quantity
        product.save()
        return product

    @staticmethod
    def check_stock_availability(product_id, quantity):
        """Check stock without modifying"""
        product = Product.objects.get(id=product_id)
        return product.stock_quantity >= quantity

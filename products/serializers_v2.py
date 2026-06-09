# products/serializers_v2.py (for future version)
from rest_framework import serializers
from .models import Product


class ProductSerializerV2(serializers.ModelSerializer):
    """Product serializer for API v2 with additional fields"""

    seller_name = serializers.CharField(source="seller.username", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    in_stock = serializers.BooleanField(source="stock_quantity > 0", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "description",
            "price",
            "in_stock",
            "seller_name",
            "category_name",
            "created_at",
        ]

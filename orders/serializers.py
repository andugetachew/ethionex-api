# orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer

from django.db.models import Sum, Count, Avg


class SellerOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name")
    product_price = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2
    )

    class Meta:
        model = OrderItem
        fields = ["product_name", "quantity", "price", "product_price", "subtotal"]


class SellerOrderSerializer(serializers.ModelSerializer):
    items = SellerOrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="user.username")
    customer_phone = serializers.CharField(source="user.phone_number")

    class Meta:
        model = Order
        fields = [
            "order_number",
            "customer_name",
            "customer_phone",
            "status",
            "total",
            "delivery_fee",
            "items",
            "full_name",
            "phone_number",
            "address",
            "city",
            "created_at",
            "notes",
        ]


class SellerAnalyticsSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()

class OrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source="product", read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_details", "quantity", "price", "subtotal"]

    def get_subtotal(self, obj):
        return obj.quantity * obj.price


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "payment_method",
            "full_name",
            "phone_number",
            "address",
            "city",
            "sub_city",
            "subtotal",
            "delivery_fee",
            "total",
            "items",
            "total_items",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "order_number", "created_at", "updated_at"]

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())


class CreateOrderSerializer(serializers.Serializer):
    """Serializer for creating an order from cart"""

    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_CHOICES)
    full_name = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=15)
    address = serializers.CharField()
    city = serializers.CharField(max_length=100)
    sub_city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    delivery_fee = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)# orders/serializers.py
from rest_framework import serializers
from .models import Order, OrderItem
from products.serializers import ProductSerializer

from django.db.models import Sum, Count, Avg


class SellerOrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name")
    product_price = serializers.DecimalField(
        source="product.price", max_digits=10, decimal_places=2
    )

    class Meta:
        model = OrderItem
        fields = ["product_name", "quantity", "price", "product_price", "subtotal"]


class SellerOrderSerializer(serializers.ModelSerializer):
    items = SellerOrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source="user.username")
    customer_phone = serializers.CharField(source="user.phone_number")

    class Meta:
        model = Order
        fields = [
            "order_number",
            "customer_name",
            "customer_phone",
            "status",
            "total",
            "delivery_fee",
            "items",
            "full_name",
            "phone_number",
            "address",
            "city",
            "created_at",
            "notes",
        ]


class SellerAnalyticsSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()
    pending_orders = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()

class OrderItemSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source="product", read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_details", "quantity", "price", "subtotal"]

    def get_subtotal(self, obj):
        return obj.quantity * obj.price


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "payment_method",
            "full_name",
            "phone_number",
            "address",
            "city",
            "sub_city",
            "subtotal",
            "delivery_fee",
            "total",
            "items",
            "total_items",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "order_number", "created_at", "updated_at"]

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())


class CreateOrderSerializer(serializers.Serializer):
    """Serializer for creating an order from cart"""

    payment_method = serializers.ChoiceField(choices=Order.PAYMENT_CHOICES)
    full_name = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=15)
    address = serializers.CharField()
    city = serializers.CharField(max_length=100)
    sub_city = serializers.CharField(max_length=100, required=False, allow_blank=True)
    delivery_fee = serializers.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)
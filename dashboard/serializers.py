from rest_framework import serializers
from products.serializers import ProductSerializer
from orders.serializers import OrderSerializer


class SellerStatsSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_items_sold = serializers.IntegerField()
    average_order_value = serializers.DecimalField(max_digits=10, decimal_places=2)
    low_stock_count = serializers.IntegerField()
    recent_orders = OrderSerializer(many=True)
    top_products = ProductSerializer(many=True)
    monthly_sales = serializers.DictField()

# admin_dashboard/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from products.models import Product, Category
from orders.models import Order

User = get_user_model()


class AdminStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_sellers = serializers.IntegerField()
    total_products = serializers.IntegerField()
    total_categories = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    pending_orders = serializers.IntegerField()
    completed_orders = serializers.IntegerField()
    cancelled_orders = serializers.IntegerField()


class UserListSerializer(serializers.ModelSerializer):
    is_seller = serializers.BooleanField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "is_active", "date_joined", "is_seller"]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "is_active"]


class SalesReportSerializer(serializers.Serializer):
    date = serializers.DateField()
    total_orders = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)


class TopProductSerializer(serializers.ModelSerializer):
    total_sold = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Product
        fields = [
            "id",
            "title",
            "price",
            "stock_quantity",
            "total_sold",
            "total_revenue",
        ]


class TopSellerSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    store_name = serializers.CharField()
    total_products = serializers.IntegerField()
    total_sales = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)

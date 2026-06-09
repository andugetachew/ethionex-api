from rest_framework import serializers
from .models import Order

from datetime import timedelta


class StatusHistorySerializer(serializers.Serializer):
    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    note = serializers.CharField(required=False, allow_blank=True)


class OrderTrackingSerializer(serializers.ModelSerializer):
    status_history = StatusHistorySerializer(many=True, read_only=True)
    days_in_transit = serializers.SerializerMethodField()
    estimated_delivery = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "status",
            "tracking_number",
            "shipped_at",
            "delivered_at",
            "status_history",
            "days_in_transit",
            "estimated_delivery",
            "created_at",
        ]
        read_only_fields = ["status_history"]

    def get_days_in_transit(self, obj):
        if obj.shipped_at and obj.delivered_at:
            return (obj.delivered_at - obj.shipped_at).days
        elif obj.shipped_at:
            from django.utils import timezone

            return (timezone.now() - obj.shipped_at).days
        return None

    def get_estimated_delivery(self, obj):
        if obj.shipped_at and not obj.delivered_at:
            # Estimate 3-5 days after shipping
            return obj.shipped_at + timedelta(days=5)
        return None


class OrderStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("shipped", "Shipped"),
            ("delivered", "Delivered"),
            ("cancelled", "Cancelled"),
        ]
    )
    tracking_number = serializers.CharField(required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)

# notifications/services.py
import json
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Notification, NotificationChannel


class NotificationService:
    """Service for sending real-time notifications"""

    @staticmethod
    def send_notification(
        user_id, title, message, notification_type="system", metadata=None
    ):
        """Send notification to specific user"""
        from django.contrib.auth import get_user_model

        User = get_user_model()

        user = User.objects.get(id=user_id)

        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            metadata=metadata or {},
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}_notifications",
            {
                "type": "send_notification",
                "id": notification.id,
                "title": title,
                "message": message,
                "created_at": notification.created_at.isoformat(),
                "is_read": notification.is_read,
            },
        )

        return notification

    @staticmethod
    def register_channel(user_id, channel_name):
        """Register WebSocket channel for user"""
        from django.contrib.auth import get_user_model

        User = get_user_model()

        user = User.objects.get(id=user_id)
        NotificationChannel.objects.update_or_create(
            user=user, defaults={"channel_name": channel_name}
        )

    @staticmethod
    def send_order_status_update(order_id, user_id, status, tracking_number=None):
        """Send order status update notification"""
        status_messages = {
            "pending": "Your order has been received",
            "processing": "Your order is being processed",
            "shipped": f'Your order has been shipped! Tracking: {tracking_number or "N/A"}',
            "delivered": "Your order has been delivered",
            "cancelled": "Your order has been cancelled",
        }

        message = status_messages.get(status, f"Order status updated to {status}")

        channel_layer = get_channel_layer()
        from django.utils import timezone

        async_to_sync(channel_layer.group_send)(
            f"order_{order_id}",
            {
                "type": "order_status_update",
                "order_id": str(order_id),
                "status": status,
                "tracking_number": tracking_number,
                "updated_at": timezone.now().isoformat(),
                "message": message,
            },
        )

        NotificationService.send_notification(
            user_id,
            f"Order #{order_id} Update",
            message,
            "order",
            {"order_id": order_id, "status": status},
        )

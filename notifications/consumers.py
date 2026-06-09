# notifications/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

# User = get_user_model()


class NotificationConsumer(AsyncWebsocketConsumer):
    """Real-time notifications for users"""

    async def connect(self):
        self.user = self.scope["user"]

        if self.user.is_anonymous:
            await self.close()
        else:
            self.room_group_name = f"user_{self.user.id}_notifications"
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def receive(self, text_data):
        """Receive message from WebSocket"""
        data = json.loads(text_data)
        message_type = data.get("type")

        if message_type == "mark_read":
            await self.mark_notifications_read(data.get("notification_ids", []))
        elif message_type == "ping":
            await self.send(text_data=json.dumps({"type": "pong"}))

    async def send_notification(self, event):
        """Send notification to client"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "notification",
                    "id": event["id"],
                    "title": event["title"],
                    "message": event["message"],
                    "created_at": event["created_at"],
                    "is_read": event["is_read"],
                }
            )
        )

    @database_sync_to_async
    def mark_notifications_read(self, notification_ids):
        from .models import Notification

        Notification.objects.filter(id__in=notification_ids, user=self.user).update(
            is_read=True
        )


class OrderTrackingConsumer(AsyncWebsocketConsumer):
    """Real-time order tracking"""

    async def connect(self):
        self.user = self.scope["user"]
        self.order_id = self.scope["url_route"]["kwargs"]["order_id"]

        if self.user.is_anonymous:
            await self.close()
        else:
            # Verify user owns this order
            if await self.is_order_owner():
                self.room_group_name = f"order_{self.order_id}"
                await self.channel_layer.group_add(
                    self.room_group_name, self.channel_name
                )
                await self.accept()
            else:
                await self.close()

    async def disconnect(self, close_code):
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )

    async def order_status_update(self, event):
        """Send order status update to client"""
        await self.send(
            text_data=json.dumps(
                {
                    "type": "order_update",
                    "order_id": event["order_id"],
                    "status": event["status"],
                    "tracking_number": event.get("tracking_number"),
                    "updated_at": event["updated_at"],
                    "message": event["message"],
                }
            )
        )

    @database_sync_to_async
    def is_order_owner(self):
        from orders.models import Order

        try:
            order = Order.objects.get(id=self.order_id)
            return order.user == self.user
        except Order.DoesNotExist:
            return False

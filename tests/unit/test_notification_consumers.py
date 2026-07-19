import json
import pytest
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from channels.db import database_sync_to_async
from django.urls import re_path
from django.contrib.auth import get_user_model

from notifications.consumers import NotificationConsumer, OrderTrackingConsumer
from notifications.models import Notification
from orders.models import Order

User = get_user_model()

application = URLRouter([
    re_path(r"^ws/notifications/$", NotificationConsumer.as_asgi()),
    re_path(r"^ws/orders/(?P<order_id>\w+)/track/$", OrderTrackingConsumer.as_asgi()),
])


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestNotificationConsumer:
    async def test_anonymous_user_connection_rejected(self):
        from django.contrib.auth.models import AnonymousUser
        communicator = WebsocketCommunicator(application, "/ws/notifications/")
        communicator.scope["user"] = AnonymousUser()

        connected, _ = await communicator.connect()
        assert connected is False

    async def test_authenticated_user_can_connect(self, test_user):
        communicator = WebsocketCommunicator(application, "/ws/notifications/")
        communicator.scope["user"] = test_user

        connected, _ = await communicator.connect()
        assert connected is True

        await communicator.disconnect()

    async def test_ping_receives_pong(self, test_user):
        communicator = WebsocketCommunicator(application, "/ws/notifications/")
        communicator.scope["user"] = test_user
        await communicator.connect()

        await communicator.send_to(text_data=json.dumps({"type": "ping"}))
        response = await communicator.receive_from()
        data = json.loads(response)

        assert data["type"] == "pong"
        await communicator.disconnect()

    async def test_mark_read_updates_notification(self, test_user):
        notification = await database_sync_to_async(Notification.objects.create)(
            user=test_user, title="Test", message="Hello", is_read=False,
        )

        communicator = WebsocketCommunicator(application, "/ws/notifications/")
        communicator.scope["user"] = test_user
        await communicator.connect()

        await communicator.send_to(text_data=json.dumps({
            "type": "mark_read", "notification_ids": [notification.id]
        }))
        await communicator.disconnect()

        refreshed = await database_sync_to_async(Notification.objects.get)(id=notification.id)
        assert refreshed.is_read is True


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
class TestOrderTrackingConsumer:
    async def test_owner_connection_accepted(self, test_user, test_order):
        communicator = WebsocketCommunicator(
            application, f"/ws/orders/{test_order.id}/track/"
        )
        communicator.scope["user"] = test_user
        communicator.scope["url_route"] = {"kwargs": {"order_id": str(test_order.id)}}

        connected, _ = await communicator.connect()
        assert connected is True

        await communicator.disconnect()

    async def test_non_owner_connection_rejected(self, test_order):
        other_user = await database_sync_to_async(User.objects.create_user)(
            username="otherbuyer", email="other@test.com", password="pass123"
        )

        communicator = WebsocketCommunicator(
            application, f"/ws/orders/{test_order.id}/track/"
        )
        communicator.scope["user"] = other_user
        communicator.scope["url_route"] = {"kwargs": {"order_id": str(test_order.id)}}

        connected, _ = await communicator.connect()
        assert connected is False

    async def test_anonymous_user_rejected(self, test_order):
        from django.contrib.auth.models import AnonymousUser
        communicator = WebsocketCommunicator(
            application, f"/ws/orders/{test_order.id}/track/"
        )
        communicator.scope["user"] = AnonymousUser()
        communicator.scope["url_route"] = {"kwargs": {"order_id": str(test_order.id)}}

        connected, _ = await communicator.connect()
        assert connected is False

    async def test_nonexistent_order_rejected(self, test_user):
        communicator = WebsocketCommunicator(
            application, "/ws/orders/999999/track/"
        )
        communicator.scope["user"] = test_user
        communicator.scope["url_route"] = {"kwargs": {"order_id": "999999"}}

        connected, _ = await communicator.connect()
        assert connected is False
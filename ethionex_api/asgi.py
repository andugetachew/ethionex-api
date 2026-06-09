# ethionex_api/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.urls import path
from notifications import consumers

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ethionex_api.settings")

application = ProtocolTypeRouter(
    {
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(
                [
                    # WebSocket endpoints
                    path("ws/notifications/", consumers.NotificationConsumer.as_asgi()),
                    path(
                        "ws/orders/<str:order_id>/",
                        consumers.OrderTrackingConsumer.as_asgi(),
                    ),
                ]
            )
        ),
    }
)

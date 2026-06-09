
from django.urls import path, re_path
from . import views
from .tracking_views import (
    TrackOrderView,
    MyOrderTrackingView,
    AdminOrderStatusUpdateView,
    AdminBulkOrderUpdateView,
)

from .views import OrderFeedView, AdminOrderListView

urlpatterns = [
    path("", views.OrderListCreateView.as_view(), name="create-order"),
    path("track/", TrackOrderView.as_view(), name="track-order"),
    path("track/<int:order_id>/", MyOrderTrackingView.as_view(), name="my-order-track"),
    path("admin/", AdminOrderListView.as_view(), name="admin-order-list"),          # ← moved up
    path("feed/", OrderFeedView.as_view(), name="order-feed"),                      # ← moved up
    path("admin/bulk-update/", AdminBulkOrderUpdateView.as_view(), name="admin-bulk-update"),
    path("admin/<int:order_id>/update-status/", AdminOrderStatusUpdateView.as_view(), name="admin-update-status"),
    path("<int:order_id>/status/", views.OrderStatusUpdateView.as_view(), name="order-status-update"),
    path("<str:order_number>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("<str:order_number>/status/", views.OrderStatusUpdateView.as_view(), name="order-status-update-by-number"),
]

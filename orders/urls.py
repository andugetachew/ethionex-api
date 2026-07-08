from django.urls import path, re_path
from . import views
from .tracking_views import (
    TrackOrderView,
    MyOrderTrackingView,
    AdminOrderStatusUpdateView,
    AdminBulkOrderUpdateView,
)
from .payment_views import (
    CreateCheckoutView,
    PaymentWebhookView,
    VerifyPaymentView,
    PaymentTransactionHistoryView,
    RefundPaymentView,
)

from .views import OrderFeedView, AdminOrderListView

urlpatterns = [
    path("", views.OrderListCreateView.as_view(), name="create-order"),
    path("track/", TrackOrderView.as_view(), name="track-order"),
    path("track/<int:order_id>/", MyOrderTrackingView.as_view(), name="my-order-track"),
    path("admin/", AdminOrderListView.as_view(), name="admin-order-list"),
    path("feed/", OrderFeedView.as_view(), name="order-feed"),
    path("admin/bulk-update/", AdminBulkOrderUpdateView.as_view(), name="admin-bulk-update"),
    path("admin/<int:order_id>/update-status/", AdminOrderStatusUpdateView.as_view(), name="admin-update-status"),
    path("checkout/<str:provider>/", CreateCheckoutView.as_view(), name="payment-checkout"),
    path("webhook/<str:provider>/", PaymentWebhookView.as_view(), name="payment-webhook"),
    path("payments/history/", PaymentTransactionHistoryView.as_view(), name="payment-history"),
    path("payments/<str:transaction_id>/verify/", VerifyPaymentView.as_view(), name="payment-verify"),
    path("<str:order_number>/refund/", RefundPaymentView.as_view(), name="order-refund"),
    path("<int:order_id>/status/", views.OrderStatusUpdateView.as_view(), name="order-status-update"),
    path("<str:order_number>/", views.OrderDetailView.as_view(), name="order-detail"),
    path("<str:order_number>/status/", views.OrderStatusUpdateView.as_view(), name="order-status-update-by-number"),
]
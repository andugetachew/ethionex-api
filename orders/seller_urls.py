# orders/seller_urls.py
from django.urls import path
from . import seller_views

urlpatterns = [
    path(
        "orders/",
        seller_views.SellerOrdersView.as_view(),
        name="seller-orders",
    ),
    path(
        "orders/<str:order_number>/status/",
        seller_views.UpdateOrderStatusView.as_view(),
        name="update-order-status",
    ),
    path(
        "products/",
        seller_views.SellerProductsView.as_view(),
        name="seller-products",
    ),
    path(
        "top-products/",
        seller_views.TopSellingProductsView.as_view(),
        name="top-products",
    ),
]

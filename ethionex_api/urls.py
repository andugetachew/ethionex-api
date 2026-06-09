"""
EthioNex API URL Configuration
--------------------------------
Main entry point for all API endpoints.
Supports API versioning (v1), documentation, and reports.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import HttpResponse
import csv

v1_urls = [
    path("auth/", include("users.urls")),
    path("", include("products.urls")),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("seller/", include("dashboard.urls")),
    path("admin/", include("admin_dashboard.urls")),
]


@api_view(["GET"])
def welcome(request):
    """API root endpoint - shows available resources"""
    return Response(
        {
            "message": "Welcome to EthioNex API",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "docs": "/api/docs/",
                "admin": "/admin/",
                "api_root": "/api/",
                "api_v1": "/api/v1/",
            },
        }
    )


class ExportOrdersCSV(APIView):
    """Export all orders to CSV file"""

    def get(self, request):
        from orders.models import Order

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="orders.csv"'
        writer = csv.writer(response)
        writer.writerow(["Order ID", "Customer", "Total", "Status", "Date"])

        for order in Order.objects.all():
            writer.writerow(
                [
                    order.id,
                    order.user.username,
                    order.total,
                    order.status,
                    order.created_at,
                ]
            )
        return response


class ExportProductsCSV(APIView):
    """Export all products to CSV file"""

    def get(self, request):
        from products.models import Product

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="products.csv"'
        writer = csv.writer(response)
        writer.writerow(["Product ID", "Title", "Price", "Stock", "Category"])

        for product in Product.objects.all():
            writer.writerow(
                [
                    product.id,
                    product.title,
                    product.price,
                    product.stock_quantity,
                    product.category.name if product.category else "",
                ]
            )
        return response


schema_view = SpectacularAPIView.as_view()
swagger_view = SpectacularSwaggerView.as_view(url_name="schema")
redoc_view = SpectacularRedocView.as_view(url_name="schema")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", welcome, name="welcome"),
    path("api/", welcome, name="api-root"),
    path("api/v1/", include(v1_urls)),
    path("api/schema/", schema_view, name="schema"),
    path("api/docs/", swagger_view, name="swagger-ui"),
    path("api/redoc/", redoc_view, name="redoc"),
    path("api/auth/", include("users.urls")),
    path(
        "api/password_reset/",
        include("django_rest_passwordreset.urls", namespace="password_reset"),
    ),
    path("api/reports/orders/", ExportOrdersCSV.as_view(), name="export-orders"),
    path("api/reports/products/", ExportProductsCSV.as_view(), name="export-products"),
    path("api/notifications/", include("notifications.urls")),
]


if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

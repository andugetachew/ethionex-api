from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

# Import views
from .views import index
from .reports_views import ExportOrdersCSV, ExportProductsCSV

# Swagger schema view
schema_view = get_schema_view(
    openapi.Info(
        title="EthioNex Marketplace API",
        default_version="v1",
        description="API documentation for EthioNex Marketplace",
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)


# Welcome view
def welcome(request):
    return HttpResponse(
        """
        <h1>Welcome to EthioNex Marketplace API</h1>
        <p>API is running successfully! 🚀</p>
        <p>Visit <a href="/frontend/">/frontend/</a> for the frontend interface</p>
        <hr>
        <h3>API Endpoints:</h3>
        <ul>
            <li><a href="/api/auth/register/">POST /api/auth/register/</a> - Register</li>
            <li><a href="/api/auth/login/">POST /api/auth/login/</a> - Login</li>
            <li><a href="/api/products/">GET /api/products/</a> - Products</li>
            <li><a href="/api/cart/">GET /api/cart/</a> - Cart</li>
            <li><a href="/api/orders/">GET /api/orders/</a> - Orders</li>
            <li><a href="/api/docs/">/api/docs/</a> - Swagger Documentation</li>
        </ul>
    """
    )


urlpatterns = [
    path("", welcome, name="welcome"),
    path("frontend/", index, name="frontend"),
    path("admin/", admin.site.urls),
    path(
        "api/docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path(
        "api/redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
    ),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("products.urls")),
    path("api/cart/", include("cart.urls")),
    path("api/orders/", include("orders.urls")),
    path("api/seller/", include("orders.seller_urls")),
    path("api/admin/", include("ethionex_api.admin_urls")),
    path("api/reports/orders/", ExportOrdersCSV.as_view(), name="export-orders"),
    path("api/reports/products/", ExportProductsCSV.as_view(), name="export-products"),
    path(
        "api/password_reset/",
        include("django_rest_passwordreset.urls", namespace="password_reset"),
    ),
    path("api/mobile/", include("ethionex_api.mobile_urls")),  # Correct
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r"products", views.ProductViewSet)
router.register(r"categories", views.CategoryViewSet)


urlpatterns = [
    path("categories/", views.CategoryListCreateView.as_view(), name="category-list"),
    path(
        "categories/<int:pk>/",
        views.CategoryDetailView.as_view(),
        name="category-detail",
    ),
    path("products/", views.ProductListCreateView.as_view(), name="product-list"),
    path(
        "products/<int:pk>/", views.ProductDetailView.as_view(), name="product-detail"
    ),
    path(
        "",
        views.ProductViewSet.as_view({"get": "list", "post": "create"}),
        name="product-list",
    ),
    path(
        "<int:pk>/",
        views.ProductViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "destroy"}
        ),
        name="product-detail",
    ),
    path(
        "sellers/<int:seller_id>/products/",
        views.SellerProductsView.as_view(),
        name="seller-products",
    ),
    path(
        "products/<int:product_id>/reviews/",
        views.ReviewListCreateView.as_view(),
        name="product-reviews",
    ),
    path(
        "<int:product_id>/reviews/",
        views.ReviewListCreateView.as_view(),
        name="product-reviews",
    ),
    path(
        "<int:product_id>/reviews/create/",
        views.ReviewCreateView.as_view(),
        name="review-create",
    ),
    path("reviews/<int:pk>/", views.ReviewDetailView.as_view(), name="review-detail"),
    # Wishlist endpoints -
    path("wishlist/", views.WishlistListView.as_view(), name="wishlist"),
    path("wishlist/add/", views.AddToWishlistView.as_view(), name="add-to-wishlist"),
    path(
        "wishlist/remove/<int:product_id>/",
        views.RemoveFromWishlistView.as_view(),
        name="remove-from-wishlist",
    ),
    path("wishlist/clear/", views.ClearWishlistView.as_view(), name="clear-wishlist"),
    path("", include(router.urls)),
]

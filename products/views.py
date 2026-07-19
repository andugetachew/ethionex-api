# products/views.py
from rest_framework import generics, permissions, viewsets, filters, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Product, Review, Wishlist
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductCreateUpdateSerializer,
    ReviewSerializer,
    WishlistSerializer,
)
from utils.cache_service import CacheService

from ethionex_api.permissions import IsSeller, IsOwnerOrReadOnly
from ethionex_api.throttles import (
    ProductCreateRateThrottle,
    ProductUpdateRateThrottle,
    ProductDeleteRateThrottle,
    SearchRateThrottle,
)
from ethionex_api.pagination import StandardPagination, LargePagination, SmallPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated


class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save()


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


# FIX: removed the earlier duplicate ProductViewSet definition (no
# permission_classes at all) that this one silently overwrote — dead,
# confusing clutter with no functional effect since nothing referenced
# the name in between, but worth cleaning up since it's exactly the
# kind of duplicate-definition mistake that caused a real bug elsewhere
# in this codebase (orders/serializers.py's OrderItemSerializer).
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [
        permissions.IsAuthenticatedOrReadOnly,
        IsSeller,
        IsOwnerOrReadOnly,
    ]
    pagination_class = StandardPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "price", "is_active"]
    search_fields = ["title", "description"]
    ordering_fields = ["price", "created_at", "title"]
    ordering = ["-created_at"]
    throttle_classes = [SearchRateThrottle]

    def get_queryset(self):
        return (
            Product.objects.filter(is_active=True)
            .select_related("category", "seller")
            .prefetch_related("reviews")
            .defer("description")
            .order_by("-created_at")
        )

    def list(self, request, *args, **kwargs):
        cache_key = CacheService.get_product_list_key(
            page=int(request.query_params.get("page", 1)),
            page_size=int(request.query_params.get("page_size", 20)),
            filters={
                "category": request.query_params.get("category"),
                "search": request.query_params.get("search"),
                "sort": request.query_params.get("sort"),
            },
        )
        cached_data = CacheService.get_or_set(
            cache_key, lambda: super().list(request, *args, **kwargs).data
        )
        return Response(cached_data)

    def retrieve(self, request, *args, **kwargs):
        cache_key = CacheService.get_product_detail_key(kwargs["pk"])
        cached_data = CacheService.get_or_set(
            cache_key, lambda: super().retrieve(request, *args, **kwargs).data
        )
        return Response(cached_data)

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)
        CacheService.invalidate_product_list()

    def perform_update(self, serializer):
        serializer.save()
        CacheService.invalidate_product_detail(serializer.instance.id)
        CacheService.invalidate_product_list()

    def perform_destroy(self, instance):
        instance.soft_delete()
        CacheService.invalidate_product_detail(instance.id)
        CacheService.invalidate_product_list()

    def get_throttles(self):
        if self.request.method == "POST":
            self.throttle_classes = [ProductCreateRateThrottle]
        elif self.request.method == "PUT":
            self.throttle_classes = [ProductUpdateRateThrottle]
        elif self.request.method == "DELETE":
            self.throttle_classes = [ProductDeleteRateThrottle]
        elif self.request.method == "GET":
            self.throttle_classes = [SearchRateThrottle]
        return super().get_throttles()

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProductCreateUpdateSerializer
        return ProductSerializer


class ProductListCreateView(generics.ListCreateAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "condition", "is_active"]
    search_fields = ["title", "description"]
    ordering_fields = ["price", "created_at", "views_count"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(
                {
                    "message": "Product created successfully!",
                    "product": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=["views_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_update(self, serializer):
        if self.get_object().seller != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only update your own products")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.seller != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only delete your own products")
        instance.delete()


class SellerProductsView(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        seller_id = self.kwargs["seller_id"]
        return Product.objects.filter(seller_id=seller_id, is_available=True)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        result = []
        for product in queryset:
            image_url = (
                request.build_absolute_uri(product.image.url) if product.image else None
            )
            result.append(
                {
                    "id": product.id,
                    "name": product.name,
                    "price": str(product.price),
                    "quantity": product.quantity,
                    "condition": product.condition,
                    "description": product.description,
                    "image_url": image_url,
                    "seller": product.seller.username,
                    "created_at": product.created_at,
                }
            )
        return Response(result)


class ReviewListCreateView(generics.ListCreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = SmallPagination

    def get_queryset(self):
        return Review.objects.filter(product_id=self.kwargs["product_id"])

    def perform_create(self, serializer):
        product = get_object_or_404(Product, id=self.kwargs["product_id"])
        if Review.objects.filter(product=product, user=self.request.user).exists():
            from rest_framework.exceptions import ValidationError

            raise ValidationError("You have already reviewed this product")
        serializer.save(product=product, user=self.request.user)


class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        product = get_object_or_404(Product, id=self.kwargs["product_id"])
        serializer.save(user=self.request.user, product=product)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_update(self, serializer):
        if self.get_object().user != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only update your own reviews")
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only delete your own reviews")
        instance.delete()


class WishlistListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist_items = Wishlist.objects.filter(user=request.user)
        serializer = WishlistSerializer(wishlist_items, many=True)
        return Response(serializer.data)


class AddToWishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")
        if not product_id:
            return Response(
                {"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND
            )

        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user, product=product
        )
        message = (
            f"{product.title} added to your wishlist"
            if created
            else f"{product.title} is already in your wishlist"
        )
        return Response(
            {"message": message, "product": ProductSerializer(product).data},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class RemoveFromWishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        try:
            wishlist_item = Wishlist.objects.get(
                user=request.user, product_id=product_id
            )
            wishlist_item.delete()
            return Response(
                {"message": "Removed from wishlist"}, status=status.HTTP_200_OK
            )
        except Wishlist.DoesNotExist:
            return Response(
                {"error": "Item not found"}, status=status.HTTP_404_NOT_FOUND
            )


class ClearWishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        count = Wishlist.objects.filter(user=request.user).count()
        Wishlist.objects.filter(user=request.user).delete()
        return Response(
            {"message": f"Cleared {count} item(s) from your wishlist"},
            status=status.HTTP_200_OK,
        )


class AdminProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = LargePagination
    permission_classes = [IsAdminUser]


class CategoryViewSet(viewsets.ModelViewSet):

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


from django.core.mail import send_mail
from django.conf import settings


def check_low_stock(product):
    if product.stock_quantity <= product.reorder_level:
        send_mail(
            f"Low Stock Alert: {product.title}",
            f"Product {product.title} has only {product.stock_quantity} left. Reorder soon!",
            settings.DEFAULT_FROM_EMAIL,
            [product.seller.email],
            fail_silently=True,
        )
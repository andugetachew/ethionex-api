from rest_framework import generics, permissions, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, permissions, filters, status

from .models import Category, Product, Review
from .models import Category, Product, Review, Wishlist
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    ProductCreateUpdateSerializer,
    ReviewSerializer,
    WishlistSerializer,
)


class CategoryListCreateView(generics.ListCreateAPIView):
    """List all categories or create a new category"""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save()


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a category"""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class ProductListCreateView(generics.ListCreateAPIView):
    """List all products or create a new product"""

    queryset = Product.objects.filter(is_available=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["category", "condition", "is_available"]
    search_fields = ["name", "description"]
    ordering_fields = ["price", "created_at", "views_count"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a product"""

    queryset = Product.objects.all()
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return ProductCreateUpdateSerializer
        return ProductSerializer

    def retrieve(self, request, *args, **kwargs):
        """Increase view count when product is viewed"""
        instance = self.get_object()
        instance.views_count += 1
        instance.save(update_fields=["views_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_update(self, serializer):
        """Only seller can update their product"""
        if self.get_object().seller != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only update your own products")
        serializer.save()

    def perform_destroy(self, instance):
        """Only seller can delete their product"""
        if instance.seller != self.request.user:
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("You can only delete your own products")
        instance.delete()


class SellerProductsView(generics.ListAPIView):
    """List products by specific seller"""

    serializer_class = ProductSerializer

    def get_queryset(self):
        seller_id = self.kwargs["seller_id"]
        return Product.objects.filter(seller_id=seller_id, is_available=True)


# Add these views at the bottom of the file
class ReviewListCreateView(generics.ListCreateAPIView):
    """List reviews for a product or create a new review"""

    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        product_id = self.kwargs["product_id"]
        return Review.objects.filter(product_id=product_id)

    def perform_create(self, serializer):
        product_id = self.kwargs["product_id"]
        product = generics.get_object_or_404(Product, id=product_id)

        # Check if user already reviewed this product
        if Review.objects.filter(product=product, user=self.request.user).exists():
            from rest_framework.exceptions import ValidationError

            raise ValidationError("You have already reviewed this product")

        serializer.save(product=product, user=self.request.user)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete a review"""

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


#


# Add these views at the bottom
class WishlistListView(APIView):
    """View user's wishlist"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        wishlist_items = Wishlist.objects.filter(user=request.user)
        serializer = WishlistSerializer(wishlist_items, many=True)
        return Response(serializer.data)


class AddToWishlistView(APIView):
    """Add product to wishlist"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")

        if not product_id:
            return Response(
                {"error": "product_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(id=product_id, is_available=True)
        except Product.DoesNotExist:
            return Response(
                {"error": "Product not found"}, status=status.HTTP_404_NOT_FOUND
            )

        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user, product=product
        )

        if created:
            return Response(
                {
                    "message": f"{product.name} added to your wishlist",
                    "product": ProductSerializer(product).data,
                },
                status=status.HTTP_201_CREATED,
            )
        else:
            return Response(
                {
                    "message": f"{product.name} is already in your wishlist",
                    "product": ProductSerializer(product).data,
                },
                status=status.HTTP_200_OK,
            )


class RemoveFromWishlistView(APIView):
    """Remove product from wishlist"""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, product_id):
        try:
            wishlist_item = Wishlist.objects.get(
                user=request.user, product_id=product_id
            )
            product_name = wishlist_item.product.name
            wishlist_item.delete()

            return Response(
                {"message": f"{product_name} removed from your wishlist"},
                status=status.HTTP_200_OK,
            )

        except Wishlist.DoesNotExist:
            return Response(
                {"error": "Product not found in your wishlist"},
                status=status.HTTP_404_NOT_FOUND,
            )


class ClearWishlistView(APIView):
    """Clear entire wishlist"""

    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        count = Wishlist.objects.filter(user=request.user).count()
        Wishlist.objects.filter(user=request.user).delete()

        return Response(
            {"message": f"Cleared {count} item(s) from your wishlist"},
            status=status.HTTP_200_OK,
        )

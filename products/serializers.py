from rest_framework import serializers
from .models import Category, Product, ProductImage
from .models import Category, Product, ProductImage, Review
from .models import Category, Product, ProductImage, Review, Wishlist


class ReviewSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Review
        fields = [
            "id",
            "user",
            "user_name",
            "rating",
            "comment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "user", "created_at", "updated_at"]


class CategorySerializer(serializers.ModelSerializer):
    """Category serializer"""

    products_count = serializers.IntegerField(source="products.count", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description", "products_count", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductImageSerializer(serializers.ModelSerializer):
    """Product image serializer"""

    class Meta:
        model = ProductImage
        fields = ["id", "image", "is_primary"]


class ProductSerializer(serializers.ModelSerializer):
    seller = serializers.StringRelatedField(read_only=True)
    seller_id = serializers.IntegerField(source="seller.id", read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    average_rating = serializers.ReadOnlyField()  # Add this
    total_reviews = serializers.ReadOnlyField()  # Add this
    reviews = ReviewSerializer(many=True, read_only=True)
    image_url = serializers.SerializerMethodField()
    gallery = ProductImageSerializer(source="extra_images", many=True, read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "seller",
            "seller_id",
            "category",
            "category_name",
            "name",
            "slug",
            "description",
            "price",
            "condition",
            "quantity",
            "image",
            "is_available",
            "views_count",
            "average_rating",
            "total_reviews",
            "reviews",  # Added fields
            "created_at",
            "updated_at",
            "images",
        ]
        read_only_fields = ["id", "seller", "views_count", "created_at", "updated_at"]


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products"""

    class Meta:
        model = Product
        fields = [
            "category",
            "name",
            "slug",
            "description",
            "price",
            "condition",
            "quantity",
            "image",
            "is_available",
        ]


class WishlistSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source="product", read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "product", "product_details", "added_at"]
        read_only_fields = ["id", "added_at"]

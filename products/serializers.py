from rest_framework import serializers
from .models import Category, Product, ProductImage, Review, Wishlist


class CategorySerializer(serializers.ModelSerializer):
    products_count = serializers.IntegerField(source="products.count", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "slug", "description", "products_count", "created_at"]
        read_only_fields = ["id", "created_at"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]


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


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "title",
            "category",
            "slug",
            "description",
            "price",
            "condition",
            "stock_quantity",
            "cover_image",
            "is_active",
        ]
        extra_kwargs = {"slug": {"required": False}, "cover_image": {"required": False}}

    def create(self, validated_data):
        if "slug" not in validated_data or not validated_data["slug"]:
            base_slug = validated_data["title"].lower().replace(" ", "-")
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            validated_data["slug"] = slug
        return super().create(validated_data)


class ProductSerializer(serializers.ModelSerializer):
    seller = serializers.StringRelatedField(read_only=True)
    seller_id = serializers.IntegerField(source="seller.id", read_only=True)
    category_name = serializers.CharField(source="category.slug", read_only=True)
    images = ProductImageSerializer(source="extra_images", many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    cover_image_url = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "id",
            "seller",
            "seller_id",
            "category",
            "category_name",
            "title",
            "slug",
            "description",
            "price",
            "condition",
            "stock_quantity",
            "cover_image",
            "cover_image_url",
            "is_active",
            "views_count",
            "reviews",
            "images",
            "created_at",
            "updated_at",
        ]

    def get_cover_image_url(self, obj):
        if obj.cover_image:
            return obj.cover_image.url
        return None


class WishlistSerializer(serializers.ModelSerializer):
    product_details = ProductSerializer(source="product", read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "product", "product_details", "added_at"]

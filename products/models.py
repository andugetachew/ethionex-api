from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Category(models.Model):
    """Product category"""

    name = models.CharField(max_length=100, unique=True, db_index=True)
    slug = models.SlugField(unique=True, db_index=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Product(models.Model):
    """Product model for marketplace"""

    CONDITION_CHOICES = [
        ("new", "New"),
        ("like_new", "Like New"),
        ("good", "Good"),
        ("fair", "Fair"),
    ]

    # Relationships
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="products",
        db_index=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
        db_index=True,
    )

    # Basic info
    title = models.CharField(max_length=200, db_index=True)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    stock_quantity = models.IntegerField(default=0)
    cover_image = models.ImageField(upload_to="covers/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    # Pricing & Stock
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        db_index=True,
    )
    stock_quantity = models.IntegerField(default=0, db_index=True)

    # Product details
    condition = models.CharField(
        max_length=20, choices=CONDITION_CHOICES, default="good"
    )
    cover_image = models.ImageField(upload_to="products/", blank=True, null=True)

    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    views_count = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)  # Soft delete flag
    deleted_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    def soft_delete(self):
        from django.utils import timezone

        self.is_deleted = True
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save()

    def restore(self):
        self.is_deleted = False
        self.is_active = True
        self.deleted_at = None
        self.save()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["price", "created_at"]),
            models.Index(fields=["category", "is_active"]),
            models.Index(fields=["seller", "is_active"]),
        ]

    def __str__(self):
        return self.title

    @property
    def average_rating(self):
        """Calculate average rating"""
        ratings = self.reviews.all().values_list("rating", flat=True)
        if ratings:
            return sum(ratings) / len(ratings)
        return 0

    @property
    def total_reviews(self):
        """Count total reviews"""
        return self.reviews.count()

    @property
    def is_visible(self):
        return self.is_active and not self.is_deleted


class ProductImage(models.Model):
    """Multiple images for a product"""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="extra_images"
    )
    image = models.ImageField(upload_to="products/gallery/")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.product.title}"


class Review(models.Model):
    """Product review and rating"""

    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["product", "user"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} - {self.product.title}: {self.rating}★"


class Wishlist(models.Model):
    """User wishlist for saving favorite products"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlist_items",
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="wished_by"
    )
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "product"]
        ordering = ["-added_at"]

    def __str__(self):
        return f"{self.user.username} - {self.product.title}"

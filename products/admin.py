from django.contrib import admin
from .models import Product, Category, Review


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "quantity", "is_available", "image_preview"]
    list_filter = ["category", "condition", "is_available"]
    search_fields = ["name", "description"]
    list_editable = ["price", "quantity"]
    fields = [
        "name",
        "slug",
        "category",
        "seller",
        "price",
        "description",
        "condition",
        "quantity",
        "image",
        "is_available",
    ]

    def image_preview(self, obj):
        if obj.image:
            from django.utils.html import format_html

            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover; border-radius: 5px;" />',
                obj.image.url,
            )
        return "No Image"

    image_preview.short_description = "Image"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "rating", "created_at"]

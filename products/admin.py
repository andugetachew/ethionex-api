# products/admin.py
from django.contrib import admin
from .models import Product, Category, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "slug"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "title",
        "price",
        "stock_quantity",
        "is_active",
        "seller",
        "created_at",
    ]
    list_filter = ["is_active", "category", "created_at"]
    search_fields = ["title", "description", "seller__username"]
    list_editable = ["price", "stock_quantity", "is_active"]
    readonly_fields = ["created_at", "updated_at"]
    raw_id_fields = ["seller", "category"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["id", "product", "user", "rating", "created_at"]
    list_filter = ["rating", "created_at"]
    search_fields = ["product__title", "user__username"]

import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ethionex_api.settings")
django.setup()

from products.models import Category, Product
from accounts.models import User

# Get or create category
cat, _ = Category.objects.get_or_create(name="Electronics", slug="electronics")

# Get or create seller
seller, _ = User.objects.get_or_create(username="testuser")
seller.is_seller = True
seller.save()

# Products data
products = [
    {"name": "iPhone 13 Pro", "price": 85000, "condition": "like_new", "quantity": 1},
    {
        "name": "Samsung Galaxy S24 Ultra",
        "price": 125000,
        "condition": "new",
        "quantity": 3,
    },
    {
        "name": "Sony WH-1000XM5 Headphones",
        "price": 25000,
        "condition": "new",
        "quantity": 5,
    },
    {
        "name": "iPad Air 5th Gen",
        "price": 65000,
        "condition": "like_new",
        "quantity": 2,
    },
    {"name": "Apple Watch Series 9", "price": 45000, "condition": "new", "quantity": 4},
    {"name": "Google Pixel 8 Pro", "price": 85000, "condition": "new", "quantity": 2},
    {"name": "Hat", "price": 1000, "condition": "new", "quantity": 10},
    {"name": "Smart Watch", "price": 28000, "condition": "new", "quantity": 5},
    {"name": "Ring", "price": 24000, "condition": "new", "quantity": 8},
    {"name": "Jewelry", "price": 30000, "condition": "new", "quantity": 6},
]

for p in products:
    product, created = Product.objects.get_or_create(
        name=p["name"],
        defaults={
            "slug": p["name"].lower().replace(" ", "-"),
            "price": p["price"],
            "condition": p["condition"],
            "quantity": p["quantity"],
            "category": cat,
            "seller": seller,
            "is_available": True,
        },
    )
    if created:
        print(f"Added: {p['name']}")
    else:
        print(f"Already exists: {p['name']}")

print(f"\nTotal products: {Product.objects.count()}")

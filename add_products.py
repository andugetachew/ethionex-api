import requests
import json

# Login
print("🔐 Logging in...")
login_response = requests.post(
    "http://127.0.0.1:8000/api/auth/login/",
    json={"username": "testuser", "password": "testpass123"},
)

if login_response.status_code == 200:
    token = login_response.json()["access"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("✅ Logged in successfully!\n")

    # Products to add
    products_list = [
        {
            "category": 1,
            "name": "Samsung Galaxy S24 Ultra",
            "slug": "samsung-galaxy-s24-ultra",
            "description": "Latest Samsung flagship, 512GB storage, 12GB RAM",
            "price": 125000,
            "condition": "new",
            "quantity": 3,
            "is_available": True,
        },
        {
            "category": 1,
            "name": "Sony WH-1000XM5 Headphones",
            "slug": "sony-wh1000xm5",
            "description": "Noise-cancelling wireless headphones, 30-hour battery life",
            "price": 25000,
            "condition": "new",
            "quantity": 5,
            "is_available": True,
        },
        {
            "category": 1,
            "name": "iPad Air 5th Gen",
            "slug": "ipad-air-5th-gen",
            "description": "10.9-inch display, M1 chip, 64GB, Wi-Fi + Cellular",
            "price": 65000,
            "condition": "like_new",
            "quantity": 2,
            "is_available": True,
        },
        {
            "category": 1,
            "name": "Apple Watch Series 9",
            "slug": "apple-watch-series-9",
            "description": "GPS + Cellular, 45mm, Midnight Aluminum Case",
            "price": 45000,
            "condition": "new",
            "quantity": 4,
            "is_available": True,
        },
        {
            "category": 1,
            "name": "Google Pixel 8 Pro",
            "slug": "google-pixel-8-pro",
            "description": "Google flagship phone, 256GB storage, amazing camera",
            "price": 85000,
            "condition": "new",
            "quantity": 2,
            "is_available": True,
        },
    ]

    print("📦 Adding products...\n")

    for product in products_list:
        response = requests.post(
            "http://127.0.0.1:8000/api/products/", headers=headers, json=product
        )

        if response.status_code == 201:
            data = response.json()
            print(f"✅ Added: {data['name']}")
            print(f"   Price: {data['price']} ETB")
            # Check if 'id' exists in response
            if "id" in data:
                print(f"   ID: {data['id']}")
            print()
        else:
            print(f"❌ Failed: {product['name']}")
            print(f"   Status: {response.status_code}")
            print(f"   Error: {response.text}\n")

    # Show all products
    print("=" * 50)
    print("📋 Current Products in Marketplace:")
    print("=" * 50)

    products_response = requests.get("http://127.0.0.1:8000/api/products/")

    if products_response.status_code == 200:
        all_products = products_response.json()
        if all_products:
            for idx, product in enumerate(all_products, 1):
                print(f"\n{idx}. {product['name']}")
                print(f"   Price: {product['price']} ETB")
                print(f"   Condition: {product['condition']}")
                print(f"   Available: {product['is_available']}")
        else:
            print("No products found yet.")
    else:
        print(f"Error fetching products: {products_response.status_code}")

else:
    print(f"❌ Login failed: {login_response.text}")

print("\n" + "=" * 50)
print("✨ Done!")
print("=" * 50)

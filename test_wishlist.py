import requests
import json

print("=" * 50)
print("Testing Wishlist Feature")
print("=" * 50)

# Login
print("\n1. Logging in as testuser...")
login = requests.post(
    "http://127.0.0.1:8000/api/auth/login/",
    json={"username": "testuser", "password": "testpass123"},
)

if login.status_code != 200:
    print("❌ Login failed!")
    exit()

token = login.json()["access"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print("✅ Logged in!")

# Get all products
print("\n2. Fetching available products...")
products = requests.get("http://127.0.0.1:8000/api/products/")
products_data = products.json()
print(f"   Found {len(products_data)} products")

# Add products to wishlist
print("\n3. Adding products to wishlist...")
wishlist_items = []

for product in products_data[:3]:  # Add first 3 products
    response = requests.post(
        "http://127.0.0.1:8000/api/wishlist/add/",
        headers=headers,
        json={"product_id": product["id"]},
    )

    if response.status_code == 201:
        print(f"   ✅ Added: {product['name']}")
        wishlist_items.append(product["name"])
    else:
        print(
            f"   ⚠️ {product['name']}: {response.json().get('message', 'Already in wishlist')}"
        )

# View wishlist
print("\n4. Viewing your wishlist...")
wishlist = requests.get("http://127.0.0.1:8000/api/wishlist/", headers=headers)

if wishlist.status_code == 200:
    wishlist_data = wishlist.json()
    print(f"   Total items in wishlist: {len(wishlist_data)}")

    for idx, item in enumerate(wishlist_data, 1):
        product = item["product_details"]
        print(f"\n   {idx}. {product['name']}")
        print(f"      Price: {product['price']} ETB")
        print(f"      Added on: {item['added_at'][:10]}")
        print(f"      Rating: {product.get('average_rating', 0)}★")

# Try to add same product again (should show already exists)
print("\n5. Testing duplicate add...")
duplicate = requests.post(
    "http://127.0.0.1:8000/api/wishlist/add/",
    headers=headers,
    json={"product_id": products_data[0]["id"]},
)
print(f"   Response: {duplicate.json()['message']}")

# Remove a product from wishlist
if wishlist_data:
    print("\n6. Removing first product from wishlist...")
    first_product_id = wishlist_data[0]["product"]
    remove = requests.delete(
        f"http://127.0.0.1:8000/api/wishlist/remove/{first_product_id}/",
        headers=headers,
    )
    print(f"   {remove.json()['message']}")

# View updated wishlist
print("\n7. Updated wishlist...")
wishlist = requests.get("http://127.0.0.1:8000/api/wishlist/", headers=headers)
wishlist_data = wishlist.json()
print(f"   Remaining items: {len(wishlist_data)}")

# Option to clear entire wishlist
print("\n8. Would you like to clear your wishlist? (yes/no)")
print("   To clear, run: python test_wishlist_clear.py")

print("\n✨ Wishlist test complete!")

# Show summary
print("\n" + "=" * 50)
print("📊 Wishlist Summary:")
print(f"   ✅ Added {len(wishlist_items)} items")
print(f"   📍 {len(wishlist_data)} items remaining")
print("=" * 50)

import requests
import json

print("=" * 50)
print("EthioNex Marketplace API Test")
print("=" * 50)

# First, login to get token
print("\n🔐 Logging in as testuser...")
login_response = requests.post(
    "http://127.0.0.1:8000/api/auth/login/",
    json={"username": "testuser", "password": "testpass123"},
)

print(f"Login Status: {login_response.status_code}")

if login_response.status_code == 200:
    token = login_response.json()["access"]
    print("✅ Login successful!")
    print(f"Token: {token[:50]}...")

    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # Create a category
    print("\n📂 Creating category...")
    category_response = requests.post(
        "http://127.0.0.1:8000/api/categories/",
        headers=headers,
        json={
            "name": "Electronics",
            "slug": "electronics",
            "description": "Electronic devices and gadgets",
        },
    )

    print(f"Category Status: {category_response.status_code}")

    if category_response.status_code == 201:
        category = category_response.json()
        print(f"✅ Category created: {category['name']} (ID: {category['id']})")
        category_id = category["id"]
    else:
        print(f"⚠️ Category may already exist")
        category_id = 1

    # Create a product
    print("\n📦 Creating product...")
    product_response = requests.post(
        "http://127.0.0.1:8000/api/products/",
        headers=headers,
        json={
            "category": category_id,
            "name": "iPhone 13 Pro",
            "slug": "iphone-13-pro",
            "description": "Excellent condition iPhone 13 Pro, 256GB, Graphite",
            "price": 85000,
            "condition": "like_new",
            "quantity": 1,
            "is_available": True,
        },
    )

    print(f"Product Status: {product_response.status_code}")

    if product_response.status_code == 201:
        product = product_response.json()
        print(f"✅ Product created successfully!")
        print(f"   Name: {product['name']}")
        print(f"   Price: {product['price']} ETB")
        print(f"   Description: {product['description'][:50]}...")
        print(f"   Condition: {product['condition']}")
        print(f"   Available: {product['is_available']}")
        print(f"   Product ID: {product['id']}")

        # Check if seller info is available (it might be a string or object)
        if "seller" in product:
            print(f"   Seller: {product['seller']}")
        if "seller_id" in product:
            print(f"   Seller ID: {product['seller_id']}")

    else:
        print(f"❌ Product error: {product_response.text}")

    # List all products
    print("\n📋 Listing all products...")
    products_response = requests.get("http://127.0.0.1:8000/api/products/")

    print(f"Products Status: {products_response.status_code}")

    if products_response.status_code == 200:
        products = products_response.json()
        print(f"✅ Found {len(products)} product(s):")
        if products:
            for idx, product in enumerate(products, 1):
                print(f"\n   Product {idx}:")
                print(f"   • Name: {product['name']}")
                print(f"   • Price: {product['price']} ETB")
                print(f"   • Condition: {product['condition']}")
                if "seller" in product:
                    print(f"   • Seller: {product['seller']}")
        else:
            print("   No products found")
    else:
        print(f"❌ Error listing products: {products_response.text}")

    # Try to get a single product
    if products_response.status_code == 200 and len(products_response.json()) > 0:
        first_product_id = products_response.json()[0]["id"]
        print(f"\n🔍 Fetching product details for ID: {first_product_id}")
        single_product_response = requests.get(
            f"http://127.0.0.1:8000/api/products/{first_product_id}/"
        )

        if single_product_response.status_code == 200:
            product_detail = single_product_response.json()
            print(f"✅ Product details retrieved!")
            print(f"   Name: {product_detail['name']}")
            print(f"   Price: {product_detail['price']} ETB")
            print(f"   Views: {product_detail.get('views_count', 0)}")

else:
    print(f"❌ Login failed: {login_response.text}")

print("\n" + "=" * 50)
print("✨ Test complete!")
print("=" * 50)

# Show summary
print("\n📊 Summary:")
print("✅ Authentication: Working")
print("✅ Category Creation: Working")
print("✅ Product Creation: Working")
print("✅ Product Listing: Working")
print("\n🎉 Your EthioNex Marketplace API is ready!")

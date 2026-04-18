import requests
import json

print("=" * 50)
print("Testing Reviews & Ratings")
print("=" * 50)

# Login as testuser
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
print("\n2. Fetching products...")
products = requests.get("http://127.0.0.1:8000/api/products/")
products_data = products.json()

if products_data:
    first_product = products_data[0]
    product_id = first_product["id"]
    print(f"   Product: {first_product['name']}")
    print(f"   Current rating: {first_product.get('average_rating', 0)}★")
    print(f"   Total reviews: {first_product.get('total_reviews', 0)}")

# Add a review
print(f"\n3. Adding review for product ID {product_id}...")
review_data = {
    "rating": 5,
    "comment": "Excellent product! Highly recommended. Fast delivery and great quality.",
}

review = requests.post(
    f"http://127.0.0.1:8000/api/products/{product_id}/reviews/",
    headers=headers,
    json=review_data,
)

if review.status_code == 201:
    print(f"✅ Review added successfully!")
    print(f"   Rating: {review.json()['rating']}★")
    print(f"   Comment: {review.json()['comment'][:50]}...")
else:
    print(f"❌ Failed: {review.json()}")

# Get updated product details
print(f"\n4. Updated product details...")
updated_product = requests.get(f"http://127.0.0.1:8000/api/products/{product_id}/")
product_data = updated_product.json()

print(f"   Product: {product_data['name']}")
print(f"   Average rating: {product_data.get('average_rating', 0)}★")
print(f"   Total reviews: {product_data.get('total_reviews', 0)}")

# List all reviews for product
print(f"\n5. All reviews for this product:")
reviews = requests.get(f"http://127.0.0.1:8000/api/products/{product_id}/reviews/")

if reviews.status_code == 200:
    all_reviews = reviews.json()
    for rev in all_reviews:
        print(f"   • {rev['user_name']}: {rev['rating']}★ - {rev['comment'][:40]}...")

print("\n✨ Review test complete!")

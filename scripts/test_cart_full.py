import requests
import json

print("=" * 50)
print("Testing Cart API")
print("=" * 50)

# 1. Login
print("\n1. Logging in...")
login = requests.post(
    "http://127.0.0.1:8000/api/auth/login/",
    json={"username": "testuser", "password": "testpass123"},
)

if login.status_code != 200:
    print("❌ Login failed!")
    exit()

token = login.json()["access"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print("✅ Logged in successfully!")

# 2. View current cart
print("\n2. Viewing current cart...")
cart = requests.get("http://127.0.0.1:8000/api/cart/", headers=headers)
print(f"Cart: {json.dumps(cart.json(), indent=2)}")

# 3. Add product to cart (product_id: 1 = iPhone 13 Pro)
print("\n3. Adding iPhone 13 Pro to cart (quantity: 2)...")
add_item = requests.post(
    "http://127.0.0.1:8000/api/cart/add/",
    headers=headers,
    json={"product_id": 2, "quantity": 5},
)
print(f"Response: {add_item.json()}")

# 4. View cart after adding
print("\n4. Cart after adding items...")
cart = requests.get("http://127.0.0.1:8000/api/cart/", headers=headers)
cart_data = cart.json()
print(f"Total items: {cart_data.get('total_items', 0)}")
print(f"Total price: {cart_data.get('total_price', 0)} ETB")
print("\nItems in cart:")
for item in cart_data.get("items", []):
    print(f"  • {item['product_details']['name']}")
    print(f"    Quantity: {item['quantity']}")
    print(f"    Subtotal: {item['subtotal']} ETB")

print("\n✨ Cart test complete!")

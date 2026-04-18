import requests
import json

print("=" * 50)
print("Testing Order System")
print("=" * 50)

# Login
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
print("✅ Logged in!")

# First, add items to cart
print("\n2. Adding items to cart...")
cart_add = requests.post(
    "http://127.0.0.1:8000/api/cart/add/",
    headers=headers,
    json={"product_id": 1, "quantity": 2},
)
print(f"   {cart_add.json()['message']}")

# Create order from cart
print("\n3. Creating order from cart...")
order_data = {
    "payment_method": "cash",
    "full_name": "Test User",
    "phone_number": "0912345678",
    "address": "Bole Road",
    "city": "Addis Ababa",
    "sub_city": "Bole",
    "delivery_fee": 100,
    "notes": "Please call before delivery",
}

order = requests.post(
    "http://127.0.0.1:8000/api/orders/", headers=headers, json=order_data
)

if order.status_code == 201:
    order_info = order.json()
    print(f"✅ Order created successfully!")
    print(f"   Order Number: {order_info['order_number']}")
    print(f"   Total Amount: {order_info['total']} ETB")
    print(f"   Status: {order_info['status']}")

    # View all orders
    print("\n4. Viewing all orders...")
    orders = requests.get("http://127.0.0.1:8000/api/orders/", headers=headers)
    user_orders = orders.json()
    print(f"   Total orders: {len(user_orders)}")

    for ord in user_orders:
        print(f"\n   📦 Order: {ord['order_number']}")
        print(f"      Status: {ord['status']}")
        print(f"      Total: {ord['total']} ETB")
        print(f"      Date: {ord['created_at'][:10]}")

else:
    print(f"❌ Order failed: {order.json()}")

print("\n✨ Order test complete!")

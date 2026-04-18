import requests

print("Testing Order Status Update")
print("=" * 40)

# Login
login = requests.post(
    "http://127.0.0.1:8000/api/auth/login/",
    json={"username": "testuser", "password": "testpass123"},
)
token = login.json()["access"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Get orders
orders = requests.get("http://127.0.0.1:8000/api/seller/orders/", headers=headers)

if orders.status_code == 200 and len(orders.json()) > 0:
    first_order = orders.json()[0]
    order_number = first_order["order_number"]
    current_status = first_order["status"]

    print(f"\n📦 Order: {order_number}")
    print(f"Current status: {current_status}")

    # Update status to processing
    update = requests.put(
        f"http://127.0.0.1:8000/api/seller/orders/{order_number}/status/",
        headers=headers,
        json={"status": "processing"},
    )

    if update.status_code == 200:
        print(f"✅ Status updated to: {update.json()['status']}")
    else:
        print(f"❌ Update failed: {update.json()}")
else:
    print("No orders found to update")

print("\n✨ Done!")

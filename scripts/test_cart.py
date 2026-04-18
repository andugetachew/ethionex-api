import requests

# Login
print("🔐 Logging in...")
login_response = requests.post(
    "http://127.0.0.1:8000/api/auth/login/",
    json={"username": "testuser", "password": "testpass123"},
)

if login_response.status_code == 200:
    token = login_response.json()["access"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("✅ Logged in!\n")

    # 1. View empty cart
    print("📋 Viewing cart:")
    cart_response = requests.get("http://127.0.0.1:8000/api/cart/", headers=headers)
    print(f"Cart: {cart_response.json()}\n")

    # 2. Add product to cart (product_id 1 = iPhone 13 Pro)
    print("➕ Adding iPhone 13 Pro to cart (quantity: 2):")
    add_response = requests.post(
        "http://127.0.0.1:8000/api/cart/add/",
        headers=headers,
        json={"product_id": 1, "quantity": 2},
    )
    print(f"Response: {add_response.json()}\n")

    # 3. View cart after adding
    print("📋 Cart after adding:")
    cart_response = requests.get("http://127.0.0.1:8000/api/cart/", headers=headers)
    cart_data = cart_response.json()
    print(f"Total items: {cart_data.get('total_items', 0)}")
    print(f"Total price: {cart_data.get('total_price', 0)} ETB")

    if cart_data.get("items"):
        print("\nItems in cart:")
        for item in cart_data["items"]:
            print(
                f"  • {item['product_details']['name']} - {item['quantity']} x {item['product_details']['price']} ETB = {item['subtotal']} ETB"
            )

    # 4. Add another product
    print("\n➕ Adding Samsung Galaxy to cart (quantity: 1):")
    add_response = requests.post(
        "http://127.0.0.1:8000/api/cart/add/",
        headers=headers,
        json={"product_id": 2, "quantity": 1},
    )
    print(f"Response: {add_response.json()['message']}\n")

    # 5. View final cart
    print("📋 Final Cart:")
    cart_response = requests.get("http://127.0.0.1:8000/api/cart/", headers=headers)
    cart_data = cart_response.json()
    print(f"Total items: {cart_data.get('total_items', 0)}")
    print(f"Total price: {cart_data.get('total_price', 0)} ETB")

    for item in cart_data.get("items", []):
        print(
            f"  • {item['product_details']['name']}: {item['quantity']} pcs = {item['subtotal']} ETB"
        )

else:
    print("❌ Login failed")

print("\n✨ Cart test complete!")

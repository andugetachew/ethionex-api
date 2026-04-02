import requests
import json

print("=" * 60)
print("Seller Dashboard Test")
print("=" * 60)

# Login as seller
print("\n1. Logging in as testuser (seller)...")
login = requests.post(
    "http://127.0.0.1:8000/api/auth/login/",
    json={"username": "testuser", "password": "testpass123"},
)

if login.status_code != 200:
    print("❌ Login failed!")
    exit()

token = login.json()["access"]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
print("✅ Logged in as seller!")

# Get dashboard analytics
print("\n2. Dashboard Analytics...")
dashboard = requests.get("http://127.0.0.1:8000/api/seller/dashboard/", headers=headers)

if dashboard.status_code == 200:
    data = dashboard.json()
    print("\n📊 Your Store Analytics:")
    print(f"   📦 Total Products: {data.get('total_products', 0)}")
    print(f"   🛒 Total Orders: {data.get('total_orders', 0)}")
    print(f"   💰 Total Revenue: {data.get('total_revenue', 0)} ETB")
    print(f"   ⭐ Average Rating: {data.get('average_rating', 0)}★")
    print(f"   📝 Total Reviews: {data.get('total_reviews', 0)}")
    print(f"   ⏳ Pending Orders: {data.get('pending_orders', 0)}")
    print(f"   ⚠️ Low Stock Items: {data.get('low_stock_products', 0)}")
else:
    print(f"❌ Error: {dashboard.json()}")

# Get seller's products
print("\n3. Your Products...")
products = requests.get("http://127.0.0.1:8000/api/seller/products/", headers=headers)

if products.status_code == 200:
    product_list = products.json()
    print(f"   Total products: {len(product_list)}")
    for product in product_list[:5]:
        # Fix: Only show fields that exist in simplified API
        print(f"   • {product['name']} - {product['price']} ETB")
else:
    print(f"❌ Error: {products.json()}")

# Get seller's orders
print("\n4. Orders containing your products...")
orders = requests.get("http://127.0.0.1:8000/api/seller/orders/", headers=headers)

if orders.status_code == 200:
    order_list = orders.json()
    print(f"   Total orders: {len(order_list.get('orders', []))}")
else:
    print(f"❌ Error: {orders.json()}")

print("\n" + "=" * 60)
print("✨ Seller Dashboard Test Complete!")
print("=" * 60)

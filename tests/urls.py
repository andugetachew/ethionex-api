# # tests/urls.py
# BASE = "/api/v1"

# AUTH_REGISTER = f"{BASE}/auth/register/"
# AUTH_LOGIN = f"{BASE}/auth/login/"
# AUTH_PROFILE = f"{BASE}/auth/profile/"
# TOKEN_REFRESH = f"{BASE}/auth/token/refresh/"

# PRODUCTS = f"{BASE}/products/"
# PRODUCT_DETAIL = lambda pk: f"{BASE}/products/{pk}/"

# CART = f"{BASE}/cart/"
# CART_ADD = f"{BASE}/cart/add/"
# CART_UPDATE = lambda pk: f"{BASE}/cart/update/{pk}/"
# CART_REMOVE = lambda pk: f"{BASE}/cart/remove/{pk}/"

# ORDERS = f"{BASE}/orders/"
# ORDER_DETAIL = lambda num: f"{BASE}/orders/{num}/"

# SELLER_STATS = f"{BASE}/seller/stats/"
# CATEGORIES = f"{BASE}/categories/"


# tests/urls.py

# Auth
AUTH_LOGIN = "/api/v1/auth/login/"
AUTH_REGISTER = "/api/v1/auth/register/"
AUTH_PROFILE = "/api/v1/auth/profile/"

# Products
PRODUCTS = "/api/v1/products/"
PRODUCT_DETAIL = lambda pk: f"/api/v1/products/{pk}/"
SELLER_STATS = "/api/v1/seller/stats/"

# Cart
CART = "/api/v1/cart/"
CART_ADD = "/api/v1/cart/add/"

# Orders
ORDERS = "/api/v1/orders/"
ORDER_DETAIL = lambda order_number: f"/api/v1/orders/{order_number}/"

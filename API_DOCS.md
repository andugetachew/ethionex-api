# 📡 EthioNex API Documentation

## Base URL
http://localhost:8000/api/

---

## 🔐 Authentication

### Register
POST /auth/register/

```json
{
  "username": "buyer",
  "email": "buyer@example.com",
  "password": "SecurePass123",
  "password2": "SecurePass123"
}
Login

POST /auth/login/

{
  "username": "buyer",
  "password": "SecurePass123"
}

Response:

{
  "access": "jwt_token",
  "refresh": "jwt_token"
}
Verify Email

POST /auth/verify-email/

{
  "token": "verification_token"
}
📦 Products
List Products

GET /products/?page=1&search=laptop

Create Product

POST /products/

Headers:
Authorization: Bearer <token>

{
  "title": "Wireless Mouse",
  "price": 29.99,
  "stock_quantity": 100
}
🛒 Orders
Create Order

POST /orders/create/

{
  "shipping_address": "123 Main St",
  "phone": "0912345678"
}

Response:

{
  "order_number": "ORD-123ABC",
  "status": "pending",
  "total": "59.98"
}
Track Order

GET /orders/track/?order_number=ORD-123ABC

⚡ Rate Limits
Endpoint	Limit
/auth/login	5/min
/auth/register	3/min
/orders/create	10/min
🔌 WebSocket

ws://localhost:8000/ws/orders/{user_id}/

{
  "type": "order_status_update",
  "order_id": 1,
  "status": "shipped"
}
❌ Errors
{
  "error": "Bad Request"
}

401 Unauthorized
403 Forbidden
404 Not Found
429 Too Many Requests
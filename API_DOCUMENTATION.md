 # EthioNex Marketplace API Documentation

## Base URL
- Production: `https://Ethionex.pythonanywhere.com/api/`
- Local: `http://127.0.0.1:8000/api/`

## Authentication
All endpoints except register/login require JWT token:
`Authorization: Bearer <your_token>`

## Endpoints Summary

| Module | Endpoints | Methods |
|--------|-----------|---------|
| Auth | /auth/register/, /auth/login/, /auth/profile/ | POST, GET |
| Products | /products/ | GET, POST, PUT, DELETE |
| Cart | /cart/, /cart/add/ | GET, POST, PUT, DELETE |
| Orders | /orders/ | GET, POST |
| Reviews | /products/{id}/reviews/ | GET, POST |
| Wishlist | /wishlist/ | GET, POST, DELETE |

## Testing the API

### 1. Register a user
```bash
curl -X POST https://Ethionex.pythonanywhere.com/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"pass123","password_confirm":"pass123"}'
# EthioNex API — Multi-Vendor Marketplace

![Coverage](https://img.shields.io/badge/coverage-87%25-brightgreen)
![Tests](https://img.shields.io/badge/tests-370%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.2-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Redis](https://img.shields.io/badge/Redis-7-red)
![Celery](https://img.shields.io/badge/Celery-enabled-green)
![Docker](https://img.shields.io/badge/Docker-enabled-blue)
![License](https://img.shields.io/badge/license-MIT-yellow)
[![CI](https://github.com/andugetachew/ethionex-api/actions/workflows/ci.yml/badge.svg)](https://github.com/andugetachew/ethionex-api/actions)

>A production-ready multi-vendor marketplace backend built with Django REST Framework, PostgreSQL, Redis, Celery, Django Channels, and Docker. Buyers browse and purchase products, sellers manage inventory and orders, and administrators oversee the platform.

## 🌐 Live Demo

| | URL |
|--|--|
| **API Base** | https://ethionex-api.onrender.com |
| **Swagger Docs** | https://ethionex-api.onrender.com/api/docs/ |
| **ReDoc** | https://ethionex-api.onrender.com/api/redoc/ |
| **Health Check** | https://ethionex-api.onrender.com/health/ |

## 📊 Quality Metrics

- 370 automated tests
- 87% code coverage
- Unit, integration, and performance tests
- Includes inventory, payment, and order workflow testing

## 📸 API Documentation Preview

> Full interactive documentation available at `/api/docs/` — supports JWT authentication directly in the browser.

### Overview & Authentication
![Swagger Overview](docs/swagger1.png)

### Products & Orders
![Products and Orders](docs/swagger2.png)

### Dashboards & Analytics
![Dashboards and Analytics](docs/swagger3.png)


---

## ⚡ Why EthioNex?

Most portfolio APIs are CRUD wrappers. EthioNex handles real production concerns:

| Challenge | Solution |
|-----------|----------|
| Race conditions on stock | `select_for_update()` inside atomic transactions |
| Order integrity | Explicit state machine with validated transitions |
| Email blocking HTTP | All emails dispatched as Celery background tasks |
| Cache staleness | Structured cache keys with immediate write invalidation |
| Real-time tracking | WebSocket rooms with ownership verification |
| Auth security | JWT rotation + blacklisting + rate limiting |

---


## 🚀 Features

- JWT authentication with email verification
- Multi-vendor marketplace (buyers, sellers, admins)
- Product catalog with filtering and search
- Shopping cart and order management
- Atomic inventory reservation
- Stripe (test mode) + simulated Chapa payments
- Redis caching and rate limiting
- Celery background tasks
- Real-time notifications via WebSockets
- Seller and admin dashboards

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.2, Django REST Framework 3.15 |
| Database | PostgreSQL 16 |
| Cache & Broker | Redis 7 |
| Authentication | JWT (djangorestframework-simplejwt) |
| Background Tasks | Celery + Redis |
| Real-Time | Django Channels + WebSockets |
| API Docs | drf-spectacular (Swagger + ReDoc) |
| Testing | pytest, pytest-django, pytest-cov |
| Containerization | Docker, Docker Compose |

---

## 🏗 Architecture

```text
Client
   │
   ▼
Django REST API (Gunicorn)
   │
   ├── PostgreSQL
   ├── Redis (Cache + Broker)
   ├── Celery Workers
   └── Django Channels (WebSockets)
```
---

## 📁 Project Structure

```text
ethionex-api/
├── users/
├── products/
├── cart/
├── orders/
│   ├── state_machine.py
│   ├── services.py
│   └── tracking_views.py
├── notifications/
├── dashboard/
├── admin_dashboard/
├── audit/
└── utils/
```

---

## 📡 API Endpoints

## 📡 API Overview

| Resource | Endpoint |
|----------|----------|
| Authentication | `/api/v1/auth/*` |
| Products | `/api/v1/products/*` |
| Cart | `/api/v1/cart/*` |
| Orders | `/api/v1/orders/*` |
| Payments | `/api/v1/orders/checkout/*` |
| Dashboards | `/api/v1/seller/*`, `/api/v1/admin/*` |
| WebSockets | `/ws/*` |
| Monitoring | `/health/` |

---

## 💡 Example API Usage

**Register and get JWT token:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "buyer@example.com",
    "username": "testbuyer",
    "password": "securepass123",
    "password2": "securepass123"
  }'
```

**Browse products:**
```bash
curl http://localhost:8000/api/v1/products/?search=laptop&ordering=-price
```

**Place an order:**
```bash
curl -X POST http://localhost:8000/api/v1/orders/ \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "payment_method": "cash",
    "full_name": "Andualem Getachew",
    "phone_number": "0923069966",
    "address": "Bole Road",
    "city": "Addis Ababa"
  }'
```

**Track an order:**
```bash
curl http://localhost:8000/api/v1/orders/track/?order_number=ORD-20260608-0001
```

**Start a Stripe test-mode checkout (cart → payment → order):**
```bash
curl -X POST http://localhost:8000/api/v1/orders/checkout/stripe/ \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Andualem Getachew",
    "phone_number": "0923069966",
    "address": "Bole Road",
    "city": "Addis Ababa"
  }'
# → returns a Stripe test Checkout URL. Pay with card 4242 4242 4242 4242
# (any future expiry, any CVC). The Order is created only after Stripe
# confirms payment via webhook.
```

---

## 🧪 Testing

```bash
# Run full test suite inside Docker
docker-compose exec web pytest --tb=short -q

# With coverage report
docker-compose exec web pytest --cov=. --cov-report=term-missing

# Run a specific module
docker-compose exec web pytest tests/unit/test_state_machine.py -v
```

### ✅ Test Results: 370 passed — 87% coverage


### Test Structure

```text
tests/
├── integration/
├── unit/
└── performance/
```

---

## 🎯 Design Decisions

**Atomic stock reservation** — `InventoryService.reserve_stock` uses `select_for_update()` inside a database transaction, preventing race conditions when concurrent requests order the same product.

**Order state machine** — transitions are validated against an explicit map. Invalid transitions raise `ValidationError`. Every transition is logged to `OrderStatusLog` with timestamp, reason, and actor. Cancellation automatically triggers stock release via `InventoryService.release_stock`.

**Cache invalidation strategy** — product list and detail caches use structured keys (`page`, `page_size`, filters). Any write operation invalidates all related keys immediately, ensuring cache consistency.

**Email via Celery** — all emails are dispatched as background tasks so HTTP responses are never blocked by SMTP latency. Task failures are handled gracefully and logged.

**WebSocket ownership** — `OrderTrackingConsumer` verifies the connecting user owns the order before accepting the connection. Anonymous users are rejected immediately.

---

## 📦 Quick Start

**With Docker:**
```bash
git clone https://github.com/andugetachew/ethionex-api.git
cd ethionex-api
cp .env.example .env
docker-compose up --build
```

**Locally:**
```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```
Once the application is running:

- API: http://localhost:8000
- Swagger: http://localhost:8000/api/docs/
- ReDoc: http://localhost:8000/api/redoc/
- Health: http://localhost:8000/health/
---

## 🔑 Environment Variables

```env
SECRET_KEY=
DATABASE_URL=
REDIS_URL=
EMAIL_HOST_USER=
STRIPE_API_KEY=
CHAPA_API_KEY=
...
```

---

## 📄 License

MIT License

---

## 👨‍💻 Author

**Andualem Getachew**
[![GitHub](https://img.shields.io/badge/GitHub-andugetachew-black?logo=github)](https://github.com/andugetachew)
[![Email](https://img.shields.io/badge/Email-andugeta41%40gmail.com-red?logo=gmail)](mailto:andugeta41@gmail.com)
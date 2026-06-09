# 🏗 EthioNex Architecture

## System Overview

Client → Nginx → Django API → PostgreSQL  
                     ↓  
                    Redis  
                     ↓  
                   Celery

---

## Request Flow (Order Creation)

1. Client sends request
2. JWT authentication is validated
3. Product stock is locked using database transaction
4. Order is created
5. Celery task is triggered for email notification
6. Response is returned to client

---

## Inventory Protection

Uses database row locking:

```python
with transaction.atomic():
    product = Product.objects.select_for_update().get(id=id)

    if product.stock_quantity < quantity:
        raise ValidationError("Out of stock")

    product.stock_quantity -= quantity
    product.save()
Caching Strategy
Feature	TTL
Product list	5 min
Product detail	10–15 min
Seller dashboard	10 min
Rate Limiting

Applied to:

Authentication endpoints
Order creation
Cart operations
Order Lifecycle

pending → processing → shipped → delivered → cancelled

Async Tasks (Celery)
Send order confirmation email
Send verification email
Low stock alerts
Database Indexing
product category
order user
created_at fields
Deployment

Docker Compose includes:

Django API
PostgreSQL
Redis
Celery Worker
Nginx
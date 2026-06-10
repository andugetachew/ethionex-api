import pytest
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from products.models import Product, Category
from orders.models import Order
from cart.models import Cart, CartItem
from unittest.mock import patch, MagicMock
from django.core.cache import cache

User = get_user_model()


from django.core import mail
from django.conf import settings


@pytest.fixture
def rf():
    return RequestFactory()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, test_user):
    api_client.force_authenticate(user=test_user)
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client


@pytest.fixture
def test_user(db):
    return User.objects.create_user(
        username="testbuyer", email="buyer@test.com", password="SecurePass123"
    )


@pytest.fixture
def test_seller(db):
    user = User.objects.create_user(
        username="testseller", email="seller@test.com", password="SecurePass123"
    )
    user.is_seller = True
    user.save()
    return user


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(
        username="admin", email="admin@test.com", password="admin123"
    )


@pytest.fixture
def test_category(db):
    return Category.objects.create(slug="electronics")


@pytest.fixture
def test_product(db, test_seller, test_category):
    return Product.objects.create(
        seller=test_seller,
        category=test_category,
        title="Test Laptop",
        description="High performance laptop",
        price=999.99,
        stock_quantity=50,
        is_active=True,
    )


@pytest.fixture
def test_cart(db, test_user, test_product):
    cart, _ = Cart.objects.get_or_create(user=test_user)
    CartItem.objects.create(cart=cart, product=test_product, quantity=2)
    return cart


@pytest.fixture
def test_order(db, test_user):
    return Order.objects.create(
        user=test_user,
        order_number="TEST123",
        full_name="Test User",
        address="123 Test St",
        city="Addis Ababa",
        phone_number="0912345678",
        payment_method="cash",
        status="pending",
        subtotal=1999.98,
        total=1999.98,
    )


@pytest.fixture(autouse=True)
def mock_email_sending():
    """Mock all email sending during tests"""
    with patch("notifications.email_service.send_mail") as mock_send:
        with patch(
            "notifications.email_service.EmailService.send_order_confirmation"
        ) as mock_order:
            with patch(
                "notifications.email_service.EmailService.send_welcome_email"
            ) as mock_welcome:
                mock_send.return_value = 1
                mock_order.return_value = True
                mock_welcome.return_value = True
                yield mock_send, mock_order, mock_welcome


@pytest.fixture(autouse=True)
def email_backend_setup():
    """Set up in-memory email backend for all tests"""
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    mail.outbox = []
    yield mail.outbox


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear cache before each test to reset throttle counters"""
    cache.clear()
    yield
    cache.clear()


import pytest
from orders.models import Order


@pytest.fixture
def order(test_user):
    return Order.objects.create(
        user=test_user,
        full_name="Test",
        phone_number="000",
        address="Test",
        city="Test",
        payment_method="cash",
        status="pending",
        subtotal=100,
        total=100,
    )

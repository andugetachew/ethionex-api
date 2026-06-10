# tests/integration/test_notification.py
import pytest
from unittest.mock import patch
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from products.models import Product, Category
from tests.urls import CART_ADD, ORDERS, AUTH_REGISTER

User = get_user_model()


@pytest.mark.django_db
class TestNotifications:

    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="buyer", email="buyer@example.com", password="pass123"
        )
        self.seller = User.objects.create_user(
            username="seller", password="pass123", is_seller=True
        )
        self.category = Category.objects.create(slug="electronics")
        self.product = Product.objects.create(
            seller=self.seller,
            title="Test Product",
            price=29.99,
            stock_quantity=10,
            category=self.category,
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)

    @patch("users.views.send_mail")
    def test_order_confirmation_email_sent(self, mock_mail):
        """Email service is called during order creation."""
        mock_mail.return_value = 1
        self.client.post(CART_ADD, {"product_id": self.product.id, "quantity": 1})
        response = self.client.post(
            ORDERS,
            {
                "payment_method": "cash",
                "full_name": "Test User",
                "phone_number": "0911234567",
                "address": "123 Test St",
                "city": "Addis Ababa",
            },
        )
        assert response.status_code == 201
        assert "order_number" in response.data

    @patch("users.views.send_mail")
    def test_welcome_email_on_registration(self, mock_mail):
        """Registration triggers a verification email via send_mail."""
        mock_mail.return_value = 1
        response = self.client.post(
            AUTH_REGISTER,
            {
                "username": "newuser",
                "email": "new@example.com",
                "password": "StrongPass123",
                "password2": "StrongPass123",
            },
        )
        assert response.status_code == 201
        # send_mail is called by RegisterView.send_verification_email
        assert mock_mail.called
        # email sent to the registered address
        call_args = mock_mail.call_args
        assert "new@example.com" in call_args[0][3]

    @patch("users.views.send_mail")
    def test_verification_email_contains_token(self, mock_mail):
        """Verification email body contains a token link."""
        mock_mail.return_value = 1
        self.client.post(
            AUTH_REGISTER,
            {
                "username": "tokenuser",
                "email": "token@example.com",
                "password": "StrongPass123",
                "password2": "StrongPass123",
            },
        )
        assert mock_mail.called
        message_body = mock_mail.call_args[0][1]
        assert "verify-email" in message_body

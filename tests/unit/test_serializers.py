# tests/unit/test_serializers.py
import pytest
from products.serializers import (
    ProductSerializer,
    ProductCreateUpdateSerializer,
    ReviewSerializer,
)
from users.serializers import RegisterSerializer


@pytest.mark.django_db
class TestProductSerializer:
    def test_valid_product_data(self, test_category):
        data = {
            "title": "New Product",
            "description": "Description",
            "price": 49.99,
            "category": test_category.id,
            "condition": "new",
            "stock_quantity": 10,
        }
        serializer = ProductCreateUpdateSerializer(data=data)
        assert serializer.is_valid() is True

    def test_invalid_price(self, test_category):
        data = {
            "title": "Invalid",
            "description": "Desc",
            "price": -10.00,
            "category": test_category.id,
        }
        serializer = ProductCreateUpdateSerializer(data=data)
        assert serializer.is_valid() is False
        assert "price" in serializer.errors


@pytest.mark.django_db
class TestRegisterSerializer:
    def test_valid_registration(self):
        data = {
            "username": "newuser",
            "email": "new@test.com",
            "password": "StrongPass123",
            "password2": "StrongPass123",
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid() is True

    def test_password_mismatch(self):
        data = {
            "username": "newuser",
            "email": "new@test.com",
            "password": "Pass123",
            "password2": "Pass456",
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid() is False
        assert "password" in serializer.errors

from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import Category, Product
from accounts.models import User


class ProductTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="seller",
            password="seller123",
            is_seller=True,
            is_email_verified=True,
        )
        self.category = Category.objects.create(name="Electronics", slug="electronics")

        # Get token
        response = self.client.post(
            "/api/auth/login/",
            {"username": "seller", "password": "seller123"},
            format="json",
        )
        self.token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_create_product(self):
        """Test seller can create product"""
        data = {
            "name": "Test Product",
            "slug": "test-product",
            "description": "This is a test product",
            "price": 1000,
            "category": self.category.id,
            "quantity": 10,
        }
        response = self.client.post("/api/products/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)

    def test_list_products(self):
        """Test products list endpoint"""
        response = self.client.get("/api/products/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

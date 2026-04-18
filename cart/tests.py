from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Category, Product
from accounts.models import User


class CartTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="buyer", password="buyer123", is_email_verified=True
        )
        self.category = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            price=1000,
            category=self.category,
            seller=self.user,
            quantity=10,
            is_available=True,
        )

        # Login
        response = self.client.post(
            "/api/auth/login/",
            {"username": "buyer", "password": "buyer123"},
            format="json",
        )
        self.token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_add_to_cart(self):
        """Test adding product to cart"""
        data = {"product_id": self.product.id, "quantity": 2}
        response = self.client.post("/api/cart/add/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

    def test_view_cart(self):
        """Test viewing cart"""
        response = self.client.get("/api/cart/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

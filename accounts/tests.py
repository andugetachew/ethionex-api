from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("register")
        self.login_url = reverse("login")

    def test_user_registration(self):
        """Test user can register"""
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
            "phone_number": "0912345678",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

    def test_duplicate_registration(self):
        """Test cannot register with same username"""
        User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        data = {
            "username": "testuser",
            "email": "new@example.com",
            "password": "testpass123",
            "password_confirm": "testpass123",
        }
        response = self.client.post(self.register_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_with_verified_email(self):
        """Test verified user can login"""
        user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            is_email_verified=True,
        )
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_login_without_verification(self):
        """Test unverified user cannot login"""
        User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            is_email_verified=False,
        )
        data = {"username": "testuser", "password": "testpass123"}
        response = self.client.post(self.login_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ProductTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="seller",
            password="seller123",
            is_seller=True,
            is_email_verified=True,
        )

        # Login and get token
        response = self.client.post(
            "/api/auth/login/",
            {"username": "seller", "password": "seller123"},
            format="json",
        )
        self.token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_create_product(self):
        """Test seller can create product"""
        # Create category first
        from products.models import Category

        cat = Category.objects.create(name="Electronics", slug="electronics")

        data = {
            "name": "Test Product",
            "slug": "test-product",
            "description": "Test description",
            "price": 1000,
            "category": cat.id,
            "quantity": 10,
        }
        response = self.client.post("/api/products/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_unauthorized_product_creation(self):
        """Test non-seller cannot create product"""
        self.client.credentials()  # Remove auth
        data = {"name": "Test", "price": 100}
        response = self.client.post("/api/products/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CartTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="buyer", password="buyer123", is_email_verified=True
        )

        # Login
        response = self.client.post(
            "/api/auth/login/",
            {"username": "buyer", "password": "buyer123"},
            format="json",
        )
        self.token = response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

        # Create product
        from products.models import Category, Product

        cat = Category.objects.create(name="Electronics", slug="electronics")
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            price=1000,
            category=cat,
            seller=self.user,
            quantity=10,
            is_available=True,
        )

    def test_add_to_cart(self):
        """Test adding product to cart"""
        data = {"product_id": self.product.id, "quantity": 2}
        response = self.client.post("/api/cart/add/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_cart(self):
        """Test viewing cart"""
        response = self.client.get("/api/cart/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

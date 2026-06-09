import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from products.models import Product, Category
from tests.urls import SELLER_STATS

User = get_user_model()


@pytest.mark.django_db
class TestSellerDashboard:
    def setup_method(self):
        self.client = APIClient()
        self.seller = User.objects.create_user(
            username="seller", password="pass123", is_seller=True
        )
        self.category = Category.objects.create(slug="electronics")
        self.product = Product.objects.create(
            seller=self.seller,
            title="Seller Product",
            price=49.99,
            stock_quantity=10,
            category=self.category,
            is_active=True,
        )
        self.client.force_authenticate(user=self.seller)

    def test_seller_can_view_dashboard(self):
        response = self.client.get(SELLER_STATS)
        assert response.status_code == 200
        assert "total_products" in response.data

    def test_dashboard_shows_correct_product_count(self):
        response = self.client.get(SELLER_STATS)
        assert response.data["total_products"] >= 1

    def test_buyer_cannot_access_seller_dashboard(self):
        buyer = User.objects.create_user(username="buyer", password="pass123")
        self.client.force_authenticate(user=buyer)
        response = self.client.get(SELLER_STATS)
        assert response.status_code == 403

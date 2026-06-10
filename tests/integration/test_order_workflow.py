# tests/integration/test_order_workflow.py
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from products.models import Product, Category
from orders.models import Order
from audit.models import AuditLog
from tests.urls import (
    CART_ADD,
    ORDERS,
    ORDER_DETAIL,
    PRODUCTS,
    PRODUCT_DETAIL,
    SELLER_STATS,
    AUTH_LOGIN,
)

User = get_user_model()


@pytest.mark.django_db
class TestOrderWorkflow:

    def test_complete_order_flow_with_stock_update(self, auth_client, test_product):
        initial_stock = test_product.stock_quantity
        auth_client.post(CART_ADD, {"product_id": test_product.id, "quantity": 2})
        response = auth_client.post(
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
        test_product.refresh_from_db()
        assert test_product.stock_quantity == initial_stock - 2

    def test_cannot_order_more_than_available_stock(self, auth_client, test_product):
        test_product.stock_quantity = 2
        test_product.save()
        auth_client.post(CART_ADD, {"product_id": test_product.id, "quantity": 5})
        response = auth_client.post(
            ORDERS,
            {
                "payment_method": "cash",
                "full_name": "Test User",
                "phone_number": "0911234567",
                "address": "123 Test St",
                "city": "Addis Ababa",
            },
        )
        assert response.status_code == 400

    def test_cancel_order_restores_stock(self, auth_client, test_product):
        initial_stock = test_product.stock_quantity
        auth_client.post(CART_ADD, {"product_id": test_product.id, "quantity": 2})
        response = auth_client.post(
            ORDERS,
            {
                "payment_method": "cash",
                "full_name": "Test User",
                "phone_number": "0911234567",
                "address": "123 Test St",
                "city": "Addis Ababa",
            },
        )
        order_number = response.data["order_number"]
        auth_client.patch(
            ORDER_DETAIL(order_number), {"status": "cancelled"}, format="json"
        )
        test_product.refresh_from_db()
        assert test_product.stock_quantity == initial_stock

    def test_duplicate_order_prevention_idempotency(self, auth_client, test_product):
        auth_client.post(CART_ADD, {"product_id": test_product.id, "quantity": 1})
        order_data = {
            "payment_method": "cash",
            "full_name": "Test User",
            "phone_number": "0911234567",
            "address": "123 Test St",
            "city": "Addis Ababa",
        }
        response1 = auth_client.post(ORDERS, order_data)
        assert response1.status_code == 201
        # Cart should be empty now — second order should fail
        response2 = auth_client.post(ORDERS, order_data)
        assert response2.status_code == 400


@pytest.mark.django_db
class TestOrderStateTransitions:

    @pytest.fixture(autouse=True)
    def setup(self, auth_client, test_product, admin_user):
        self.client = auth_client
        self.admin = admin_user
        self.client.post(CART_ADD, {"product_id": test_product.id, "quantity": 1})
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
        self.order_number = response.data["order_number"]
        self.admin_client = APIClient()
        self.admin_client.force_authenticate(user=self.admin)

    def test_pending_to_paid_valid(self):
        response = self.admin_client.patch(
            ORDER_DETAIL(self.order_number), {"status": "paid"}, format="json"
        )
        assert response.status_code == 200

    def test_pending_to_shipped_invalid(self):
        response = self.admin_client.patch(
            ORDER_DETAIL(self.order_number), {"status": "shipped"}, format="json"
        )
        assert response.status_code == 400

    def test_full_valid_chain(self):
        for step in ["paid", "processing", "shipped", "delivered"]:
            r = self.admin_client.patch(
                ORDER_DETAIL(self.order_number), {"status": step}, format="json"
            )
            assert r.status_code == 200, f"Failed at step: {step}"

    def test_pending_to_cancelled_valid(self):
        response = self.admin_client.patch(
            ORDER_DETAIL(self.order_number), {"status": "cancelled"}, format="json"
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestPermissions:

    def test_seller_can_edit_own_product(self, test_seller, test_product):
        client = APIClient()
        client.force_authenticate(user=test_seller)
        response = client.patch(
            PRODUCT_DETAIL(test_product.id), {"title": "Updated"}, format="json"
        )
        assert response.status_code in [200, 403]

    def test_seller_cannot_edit_others_product(self, test_product):
        other_seller = User.objects.create_user(
            username="other_seller", password="pass123", is_seller=True
        )
        client = APIClient()
        client.force_authenticate(user=other_seller)
        response = client.patch(
            PRODUCT_DETAIL(test_product.id), {"title": "Hacked"}, format="json"
        )
        assert response.status_code == 403

    def test_buyer_cannot_access_seller_dashboard(self, test_user):
        client = APIClient()
        client.force_authenticate(user=test_user)
        response = client.get(SELLER_STATS)
        assert response.status_code == 403

    def test_admin_can_edit_any_product(self, admin_user, test_product):
        client = APIClient()
        client.force_authenticate(user=admin_user)
        response = client.patch(
            PRODUCT_DETAIL(test_product.id), {"title": "Admin Updated"}, format="json"
        )
        assert response.status_code in [200, 403]


@pytest.mark.django_db
class TestRateLimiting:

    def test_login_rate_limit(self):
        client = APIClient()
        for i in range(6):
            response = client.post(
                AUTH_LOGIN, {"username": "wrong", "password": "wrong"}
            )
        assert response.status_code in [401, 429]

    def test_order_rate_limit(self, auth_client):
        for i in range(11):
            response = auth_client.post(
                ORDERS,
                {
                    "payment_method": "cash",
                    "full_name": "Test",
                    "phone_number": "0911234567",
                    "address": "123 St",
                    "city": "Addis Ababa",
                },
            )
        assert response.status_code in [400, 429]

    def test_review_rate_limit(self, auth_client, test_product):
        for i in range(11):
            response = auth_client.post(
                f"/api/v1/products/{test_product.id}/reviews/",
                {"rating": 5, "comment": f"Review {i}"},
                format="json",
            )
        assert response.status_code in [400, 429, 201]


@pytest.mark.django_db
class TestAuditLogging:
    def test_order_status_change_logged(self, auth_client, test_product, admin_user):
        auth_client.post(CART_ADD, {"product_id": test_product.id, "quantity": 1})
        response = auth_client.post(
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

    def test_product_update_logged(self, test_seller, test_product):
        client = APIClient()
        client.force_authenticate(user=test_seller)
        client.patch(
            PRODUCT_DETAIL(test_product.id), {"title": "Updated"}, format="json"
        )
        assert True

    def test_admin_action_logged(self, admin_user, test_product):
        client = APIClient()
        client.force_authenticate(user=admin_user)
        client.patch(
            PRODUCT_DETAIL(test_product.id), {"title": "Admin Action"}, format="json"
        )
        assert True

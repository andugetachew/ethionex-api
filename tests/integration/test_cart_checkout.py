# tests/integration/test_cart_checkout.py
import pytest
from tests.urls import CART, CART_ADD, ORDERS


@pytest.mark.django_db
class TestCartCheckoutFlow:

    def test_complete_purchase_flow(self, auth_client, test_product):
        # Step 1: Add to cart
        response = auth_client.post(
            CART_ADD, {"product_id": test_product.id, "quantity": 2}
        )
        assert response.status_code == 200

        # Step 2: View cart
        response = auth_client.get(CART)
        assert response.status_code == 200

        # Step 3: Create order
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
        assert "order_number" in response.data

        # Step 4: Stock decreased by the ordered quantity (2)
        stock_before = test_product.stock_quantity
        test_product.refresh_from_db()
        assert test_product.stock_quantity == stock_before - 2

    def test_empty_cart_cannot_checkout(self, auth_client):
        """Ordering with an empty cart returns 400."""
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

    def test_cart_cleared_after_order(self, auth_client, test_product):
        """Cart items are deleted once order is created."""
        auth_client.post(CART_ADD, {"product_id": test_product.id, "quantity": 1})
        auth_client.post(
            ORDERS,
            {
                "payment_method": "cash",
                "full_name": "Test User",
                "phone_number": "0911234567",
                "address": "123 Test St",
                "city": "Addis Ababa",
            },
        )
        response = auth_client.get(CART)
        assert response.status_code == 200
        # Cart should be empty
        items = response.data.get("items", response.data.get("cart_items", []))
        assert len(items) == 0

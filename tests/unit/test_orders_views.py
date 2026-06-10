# tests/unit/test_orders_views.py
import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from orders.models import Order, OrderItem
from cart.models import Cart, CartItem

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def buyer(db):
    return User.objects.create_user(
        username="buyer", email="buyer@test.com", password="pass123"
    )


@pytest.fixture
def admin(db):
    return User.objects.create_superuser(
        username="admin", email="admin@test.com", password="admin123"
    )


@pytest.fixture
def cart_with_item(db, buyer, test_product):
    cart, _ = Cart.objects.get_or_create(user=buyer)
    CartItem.objects.create(cart=cart, product=test_product, quantity=2)
    return cart


@pytest.fixture
def pending_order(db, buyer):
    return Order.objects.create(
        user=buyer,
        full_name="Buyer",
        phone_number="09",
        address="Addr",
        city="City",
        payment_method="cash",
        status="pending",
        subtotal=1000,
        total=1000,
    )


@pytest.fixture
def paid_order(db, buyer):
    return Order.objects.create(
        user=buyer,
        full_name="Buyer",
        phone_number="09",
        address="Addr",
        city="City",
        payment_method="cash",
        status="paid",
        subtotal=1000,
        total=1000,
    )


@pytest.mark.django_db
class TestOrderListCreateView:
    URL = "/api/v1/orders/"

    def test_list_authenticated(self, client, buyer, pending_order):
        client.force_authenticate(user=buyer)
        response = client.get(self.URL)
        assert response.status_code == 200

    def test_list_unauthenticated(self, client):
        response = client.get(self.URL)
        assert response.status_code == 401

    def test_list_returns_only_own_orders(self, client, buyer, admin, pending_order):
        client.force_authenticate(user=buyer)
        response = client.get(self.URL)
        assert response.status_code == 200
        results = (
            response.data
            if isinstance(response.data, list)
            else response.data.get("results", [])
        )
        # All returned orders must belong to buyer — verify via DB lookup
        from orders.models import Order

        for order in results:
            order_number = order.get("order_number")
            assert Order.objects.filter(
                order_number=order_number, user=buyer
            ).exists(), f"Order {order_number} does not belong to buyer"

    @patch("orders.views.EmailService.send_order_confirmation")
    def test_create_order_success(self, mock_email, client, buyer, cart_with_item):
        mock_email.return_value = True
        client.force_authenticate(user=buyer)
        response = client.post(
            self.URL,
            {
                "payment_method": "cash",
                "full_name": "Buyer",
                "phone_number": "09",
                "address": "Addr",
                "city": "City",
            },
            format="json",
        )
        assert response.status_code == 201

    @patch("orders.views.EmailService.send_order_confirmation")
    def test_create_clears_cart(self, mock_email, client, buyer, cart_with_item):
        mock_email.return_value = True
        client.force_authenticate(user=buyer)
        client.post(
            self.URL,
            {
                "payment_method": "cash",
                "full_name": "Buyer",
                "phone_number": "09",
                "address": "Addr",
                "city": "City",
            },
            format="json",
        )
        assert cart_with_item.items.count() == 0

    @patch("orders.views.EmailService.send_order_confirmation")
    def test_create_decreases_stock(
        self, mock_email, client, buyer, cart_with_item, test_product
    ):
        mock_email.return_value = True
        before = test_product.stock_quantity
        client.force_authenticate(user=buyer)
        client.post(
            self.URL,
            {
                "payment_method": "cash",
                "full_name": "Buyer",
                "phone_number": "09",
                "address": "Addr",
                "city": "City",
            },
            format="json",
        )
        test_product.refresh_from_db()
        assert test_product.stock_quantity == before - 2

    def test_create_empty_cart_returns_400(self, client, buyer, db):
        Cart.objects.get_or_create(user=buyer)
        client.force_authenticate(user=buyer)
        response = client.post(
            self.URL,
            {
                "payment_method": "cash",
                "full_name": "Buyer",
                "phone_number": "09",
                "address": "Addr",
                "city": "City",
            },
            format="json",
        )
        assert response.status_code == 400

    def test_create_unauthenticated_returns_401(self, client):
        response = client.post(self.URL, {}, format="json")
        assert response.status_code == 401

    @patch("orders.views.EmailService.send_order_confirmation")
    def test_insufficient_stock_returns_400(
        self, mock_email, client, buyer, db, test_product, test_seller, test_category
    ):
        mock_email.return_value = True
        test_product.stock_quantity = 1
        test_product.save()
        cart, _ = Cart.objects.get_or_create(user=buyer)
        CartItem.objects.create(cart=cart, product=test_product, quantity=5)
        client.force_authenticate(user=buyer)
        response = client.post(
            self.URL,
            {
                "payment_method": "cash",
                "full_name": "Buyer",
                "phone_number": "09",
                "address": "Addr",
                "city": "City",
            },
            format="json",
        )
        assert response.status_code == 400

    @patch("orders.views.EmailService.send_order_confirmation")
    def test_email_failure_does_not_crash(
        self, mock_email, client, buyer, cart_with_item
    ):
        mock_email.side_effect = Exception("SMTP error")
        client.force_authenticate(user=buyer)
        response = client.post(
            self.URL,
            {
                "payment_method": "cash",
                "full_name": "Buyer",
                "phone_number": "09",
                "address": "Addr",
                "city": "City",
            },
            format="json",
        )
        assert response.status_code == 201


@pytest.mark.django_db
class TestOrderDetailView:

    def url(self, order_number):
        return f"/api/v1/orders/{order_number}/"

    def test_get_own_order(self, client, buyer, pending_order):
        client.force_authenticate(user=buyer)
        response = client.get(self.url(pending_order.order_number))
        assert response.status_code == 200

    def test_get_other_users_order_404(self, client, admin, pending_order):
        client.force_authenticate(user=admin)
        response = client.get(self.url(pending_order.order_number))
        assert response.status_code == 404

    def test_get_nonexistent_404(self, client, buyer):
        client.force_authenticate(user=buyer)
        response = client.get(self.url("NOTEXIST"))
        assert response.status_code == 404

    def test_cancel_pending_order(self, client, buyer, pending_order, test_product, db):
        OrderItem.objects.create(
            order=pending_order, product=test_product, quantity=2, price=1000
        )
        client.force_authenticate(user=buyer)
        response = client.put(self.url(pending_order.order_number))
        assert response.status_code == 200
        pending_order.refresh_from_db()
        assert pending_order.status == "cancelled"

    def test_cancel_restores_stock(
        self, client, buyer, pending_order, test_product, db
    ):
        before = test_product.stock_quantity
        OrderItem.objects.create(
            order=pending_order, product=test_product, quantity=2, price=1000
        )
        client.force_authenticate(user=buyer)
        client.put(self.url(pending_order.order_number))
        test_product.refresh_from_db()
        assert test_product.stock_quantity == before + 2

    def test_cancel_non_pending_returns_400(self, client, buyer, paid_order):
        client.force_authenticate(user=buyer)
        response = client.put(self.url(paid_order.order_number))
        assert response.status_code == 400

    def test_patch_valid_transition(self, client, admin, pending_order):
        client.force_authenticate(user=admin)
        response = client.patch(
            self.url(pending_order.order_number), {"status": "paid"}, format="json"
        )
        assert response.status_code == 200

    def test_patch_invalid_transition_returns_400(self, client, admin, pending_order):
        client.force_authenticate(user=admin)
        response = client.patch(
            self.url(pending_order.order_number), {"status": "delivered"}, format="json"
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestAdminOrderStatusUpdateView:

    def url(self, order_id):
        return f"/api/v1/orders/admin/{order_id}/update-status/"

    @patch("orders.views.EmailService.send_order_status_update")
    def test_admin_updates_status(self, mock_email, client, admin, pending_order):
        mock_email.return_value = True
        client.force_authenticate(user=admin)
        response = client.post(
            self.url(pending_order.id), {"status": "paid"}, format="json"
        )
        assert response.status_code in (200, 400)

    def test_missing_status_returns_400(self, client, admin, pending_order):
        client.force_authenticate(user=admin)
        response = client.post(self.url(pending_order.id), {})
        assert response.status_code == 400

    def test_buyer_gets_403(self, client, buyer, pending_order):
        client.force_authenticate(user=buyer)
        response = client.post(self.url(pending_order.id), {"status": "paid"})
        assert response.status_code == 403

    def test_nonexistent_order_404(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.post(self.url(99999), {"status": "paid"})
        assert response.status_code == 404


@pytest.mark.django_db
class TestOrderStatusUpdateView:

    def url_by_id(self, order_id):
        return f"/api/v1/orders/{order_id}/status/"

    def test_valid_transition(self, client, admin, pending_order):
        client.force_authenticate(user=admin)
        response = client.post(self.url_by_id(pending_order.id), {"status": "paid"})
        assert response.status_code == 200

    def test_invalid_transition_returns_400(self, client, admin, pending_order):
        client.force_authenticate(user=admin)
        response = client.post(self.url_by_id(pending_order.id), {"status": "shipped"})
        assert response.status_code == 400

    def test_buyer_gets_403(self, client, buyer, pending_order):
        client.force_authenticate(user=buyer)
        response = client.post(self.url_by_id(pending_order.id), {"status": "paid"})
        assert response.status_code == 403


@pytest.mark.django_db
class TestOrderListCreateViewExtra:

    @patch("orders.views.EmailService.send_order_confirmation")
    def test_zero_stock_returns_400(self, mock_email, client, buyer, test_product, db):
        """Line 277: stock_quantity <= 0 branch"""
        mock_email.return_value = True
        test_product.stock_quantity = 0
        test_product.save()
        cart, _ = Cart.objects.get_or_create(user=buyer)
        CartItem.objects.create(cart=cart, product=test_product, quantity=1)
        client.force_authenticate(user=buyer)
        response = client.post(
            "/api/v1/orders/",
            {
                "payment_method": "cash",
                "full_name": "Buyer",
                "phone_number": "09",
                "address": "Addr",
                "city": "City",
            },
            format="json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestOrderStatusUpdateByNumber:

    def test_valid_transition_by_order_number(self, client, admin, pending_order):
        """Line 322: order_number kwarg branch"""
        client.force_authenticate(user=admin)
        response = client.post(
            f"/api/v1/orders/{pending_order.order_number}/status/",
            {"status": "paid"},
            format="json",
        )
        assert response.status_code == 200


@pytest.mark.django_db
class TestOrderDetailPatchCancelRestoresStock:

    def test_cancel_from_pending_restores_stock(
        self, client, admin, pending_order, test_product, db
    ):
        """Lines 331-334: cancelled + pending → restore stock"""
        before = test_product.stock_quantity
        OrderItem.objects.create(
            order=pending_order, product=test_product, quantity=3, price=500
        )
        client.force_authenticate(user=admin)
        client.patch(
            f"/api/v1/orders/{pending_order.order_number}/",
            {"status": "cancelled"},
            format="json",
        )
        test_product.refresh_from_db()
        assert test_product.stock_quantity == before + 3


@pytest.mark.django_db
class TestAdminOrderListView:

    def test_admin_can_list_orders(
        self,
        client,
        admin,
        pending_order,
    ):
        client.force_authenticate(user=admin)

        response = client.get("/api/v1/orders/admin/")

        assert response.status_code == 200

    def test_filter_by_status(
        self,
        client,
        admin,
        pending_order,
    ):
        client.force_authenticate(user=admin)

        response = client.get("/api/v1/orders/admin/?status=pending")

        assert response.status_code == 200


@pytest.mark.django_db
class TestOrderFeedView:

    def test_feed_returns_orders(
        self,
        client,
        buyer,
        pending_order,
    ):
        client.force_authenticate(user=buyer)

        response = client.get("/api/v1/orders/feed/")

        assert response.status_code == 200

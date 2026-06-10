import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from orders.models import Order

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def buyer(db):
    return User.objects.create_user(
        username="tbuyer", email="tbuyer@test.com", password="pass123"
    )


@pytest.fixture
def other_buyer(db):
    return User.objects.create_user(
        username="tother", email="tother@test.com", password="pass123"
    )


@pytest.fixture
def admin(db):
    return User.objects.create_superuser(
        username="tadmin", email="tadmin@test.com", password="admin123"
    )


@pytest.fixture
def tracked_order(db, buyer):
    return Order.objects.create(
        user=buyer,
        full_name="Buyer",
        phone_number="09",
        address="Addr",
        city="City",
        payment_method="cash",
        status="shipped",
        subtotal=1000,
        total=1000,
        tracking_number="TRK-ABC123",
    )


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
        subtotal=500,
        total=500,
    )


@pytest.mark.django_db
class TestTrackOrderView:

    def test_track_by_order_number(self, auth_client, tracked_order):
        response = auth_client.get(
            "/api/v1/orders/track/", {"order_number": tracked_order.order_number}
        )
        assert response.status_code == 200
        assert response.data["order_number"] == tracked_order.order_number

    def test_track_by_tracking_number(self, auth_client, tracked_order):
        response = auth_client.get(
            "/api/v1/orders/track/", {"tracking_number": "TRK-ABC123"}
        )
        assert response.status_code == 200

    def test_no_params_returns_400(self, auth_client):
        response = auth_client.get("/api/v1/orders/track/")
        assert response.status_code == 400
        assert "error" in response.data

    def test_nonexistent_order_number_404(self, auth_client):
        response = auth_client.get(
            "/api/v1/orders/track/", {"order_number": "NOTEXIST"}
        )
        assert response.status_code == 404

    def test_nonexistent_tracking_number_404(self, auth_client):
        response = auth_client.get(
            "/api/v1/orders/track/", {"tracking_number": "TRK-GHOST"}
        )
        assert response.status_code == 404


@pytest.mark.django_db
class TestMyOrderTrackingView:

    def url(self, order_id):
        return f"/api/v1/orders/track/{order_id}/"

    def test_owner_can_track(self, client, buyer, tracked_order):
        client.force_authenticate(user=buyer)
        response = client.get(self.url(tracked_order.id))
        assert response.status_code == 200

    def test_other_user_gets_404(self, client, other_buyer, tracked_order):
        client.force_authenticate(user=other_buyer)
        response = client.get(self.url(tracked_order.id))
        assert response.status_code == 404

    def test_unauthenticated_gets_401(self, client, tracked_order):
        response = client.get(self.url(tracked_order.id))
        assert response.status_code == 401

    def test_nonexistent_order_404(self, client, buyer):
        client.force_authenticate(user=buyer)
        response = client.get(self.url(99999))
        assert response.status_code == 404


@pytest.mark.django_db
class TestAdminTrackingStatusUpdateView:

    def url(self, order_id):
        return f"/api/v1/orders/admin/{order_id}/update-status/"

    @patch("orders.tracking_views.send_mail")
    def test_valid_status_update(self, mock_mail, client, admin, pending_order):
        mock_mail.return_value = 1
        client.force_authenticate(user=admin)
        response = client.post(
            self.url(pending_order.id), {"status": "processing"}, format="json"
        )
        assert response.status_code == 200
        assert response.data["new_status"] == "processing"

    @patch("orders.tracking_views.send_mail")
    def test_sets_tracking_number(self, mock_mail, client, admin, pending_order):
        mock_mail.return_value = 1
        client.force_authenticate(user=admin)
        client.post(
            self.url(pending_order.id),
            {"status": "processing", "tracking_number": "TRK-XYZ"},
            format="json",
        )
        pending_order.refresh_from_db()
        assert pending_order.tracking_number == "TRK-XYZ"

    @patch("orders.tracking_views.send_mail")
    def test_status_history_updated(self, mock_mail, client, admin, pending_order):
        mock_mail.return_value = 1
        client.force_authenticate(user=admin)
        client.post(self.url(pending_order.id), {"status": "processing"}, format="json")
        pending_order.refresh_from_db()
        assert len(pending_order.status_history) >= 1

    @patch("orders.tracking_views.send_mail")
    def test_with_note(self, mock_mail, client, admin, pending_order):
        mock_mail.return_value = 1
        client.force_authenticate(user=admin)
        response = client.post(
            self.url(pending_order.id),
            {"status": "processing", "note": "Payment confirmed"},
            format="json",
        )
        assert response.status_code == 200

    def test_invalid_data_returns_400(self, client, admin, pending_order):
        client.force_authenticate(user=admin)
        response = client.post(self.url(pending_order.id), {}, format="json")
        assert response.status_code == 400

    def test_nonexistent_order_404(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.post(self.url(99999), {"status": "processing"}, format="json")
        assert response.status_code == 404

    def test_buyer_gets_403(self, client, buyer, pending_order):
        client.force_authenticate(user=buyer)
        response = client.post(
            self.url(pending_order.id), {"status": "processing"}, format="json"
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestAdminBulkOrderUpdateView:
    URL = "/api/v1/orders/admin/bulk-update/"

    def _make_orders(self, buyer, n=2):
        return [
            Order.objects.create(
                user=buyer,
                full_name="B",
                phone_number="09",
                address="A",
                city="C",
                payment_method="cash",
                status="pending",
                subtotal=100,
                total=100,
            )
            for _ in range(n)
        ]

    def test_bulk_update_success(self, client, admin, buyer):
        orders = self._make_orders(buyer)
        ids = [o.id for o in orders]
        client.force_authenticate(user=admin)
        response = client.post(
            self.URL, {"order_ids": ids, "status": "paid"}, format="json"
        )
        assert response.status_code == 200
        assert set(response.data["updated_orders"]) == set(ids)

    def test_missing_order_ids_returns_400(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.post(self.URL, {"status": "paid"}, format="json")
        assert response.status_code == 400

    def test_missing_status_returns_400(self, client, admin, buyer):
        orders = self._make_orders(buyer, n=1)
        client.force_authenticate(user=admin)
        response = client.post(self.URL, {"order_ids": [orders[0].id]}, format="json")
        assert response.status_code == 400

    def test_nonexistent_ids_skipped(self, client, admin, buyer):
        orders = self._make_orders(buyer, n=1)
        client.force_authenticate(user=admin)
        response = client.post(
            self.URL,
            {"order_ids": [orders[0].id, 99999], "status": "paid"},
            format="json",
        )
        assert response.status_code == 200
        assert orders[0].id in response.data["updated_orders"]
        assert 99999 not in response.data["updated_orders"]

    def test_buyer_gets_403(self, client, buyer):
        client.force_authenticate(user=buyer)
        response = client.post(
            self.URL, {"order_ids": [], "status": "paid"}, format="json"
        )
        assert response.status_code == 403

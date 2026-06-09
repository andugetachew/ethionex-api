import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from orders.models import Order
from products.models import Product

User = get_user_model()


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def buyer(db):
    return User.objects.create_user(
        username="abuyer", email="abuyer@test.com", password="pass123"
    )


@pytest.fixture
def admin(db):
    return User.objects.create_superuser(
        username="aadmin", email="aadmin@test.com", password="admin123"
    )


@pytest.fixture
def pending_order(db, buyer):
    return Order.objects.create(
        user=buyer, full_name="Buyer", phone_number="09",
        address="Addr", city="City", payment_method="cash",
        status="pending", subtotal=1000, total=1000,
    )


@pytest.fixture
def delivered_order(db, buyer):
    return Order.objects.create(
        user=buyer, full_name="Buyer", phone_number="09",
        address="Addr", city="City", payment_method="cash",
        status="delivered", subtotal=2000, total=2000,
    )


@pytest.mark.django_db
class TestAdminStatsView:
    URL = "/api/v1/admin/stats/"

    def test_admin_gets_stats(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.get(self.URL)
        assert response.status_code == 200
        for key in ("total_users", "total_products", "total_orders", "total_revenue"):
            assert key in response.data

    def test_revenue_counts_delivered(self, client, admin, delivered_order):
        client.force_authenticate(user=admin)
        response = client.get(self.URL)
        assert float(response.data["total_revenue"]) >= 2000

    def test_buyer_gets_403(self, client, buyer):
        client.force_authenticate(user=buyer)
        response = client.get(self.URL)
        assert response.status_code == 403

    def test_unauthenticated_gets_401(self, client):
        response = client.get(self.URL)
        assert response.status_code == 401


@pytest.mark.django_db
class TestAdminUserListView:
    URL = "/api/v1/admin/users/"

    def test_admin_lists_users(self, client, admin, buyer):
        client.force_authenticate(user=admin)
        response = client.get(self.URL)
        assert response.status_code == 200

    def test_filter_is_active_true(self, client, admin, buyer):
        client.force_authenticate(user=admin)
        response = client.get(self.URL, {"is_active": "true"})
        assert response.status_code == 200

    def test_filter_is_active_false(self, client, admin, buyer):
        buyer.is_active = False
        buyer.save()
        client.force_authenticate(user=admin)
        response = client.get(self.URL, {"is_active": "false"})
        assert response.status_code == 200

    def test_search_by_username(self, client, admin, buyer):
        client.force_authenticate(user=admin)
        response = client.get(self.URL, {"search": "abuyer"})
        assert response.status_code == 200

    def test_buyer_gets_403(self, client, buyer):
        client.force_authenticate(user=buyer)
        response = client.get(self.URL)
        assert response.status_code == 403


@pytest.mark.django_db
class TestAdminUserDetailView:

    def url(self, pk):
        return f"/api/v1/admin/users/{pk}/"

    def test_retrieve_user(self, client, admin, buyer):
        client.force_authenticate(user=admin)
        response = client.get(self.url(buyer.pk))
        assert response.status_code == 200

    def test_soft_delete_deactivates_user(self, client, admin, buyer):
        client.force_authenticate(user=admin)
        response = client.delete(self.url(buyer.pk))
        assert response.status_code == 200
        buyer.refresh_from_db()
        assert buyer.is_active is False

    def test_nonexistent_user_404(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.get(self.url(99999))
        assert response.status_code == 404


@pytest.mark.django_db
class TestBlockUnblockUserView:

    def block_url(self, pk):
        return f"/api/v1/admin/users/{pk}/block/"

    def unblock_url(self, pk):
        return f"/api/v1/admin/users/{pk}/unblock/"

    def test_block_sets_inactive(self, client, admin, buyer):
        client.force_authenticate(user=admin)
        response = client.post(self.block_url(buyer.pk))
        assert response.status_code == 200
        buyer.refresh_from_db()
        assert buyer.is_active is False

    def test_block_nonexistent_404(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.post(self.block_url(99999))
        assert response.status_code == 404

    def test_unblock_sets_active(self, client, admin, buyer):
        buyer.is_active = False
        buyer.save()
        client.force_authenticate(user=admin)
        response = client.post(self.unblock_url(buyer.pk))
        assert response.status_code == 200
        buyer.refresh_from_db()
        assert buyer.is_active is True

    def test_unblock_nonexistent_404(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.post(self.unblock_url(99999))
        assert response.status_code == 404

    def test_buyer_cannot_block(self, client, buyer, admin):
        client.force_authenticate(user=buyer)
        response = client.post(self.block_url(admin.pk))
        assert response.status_code == 403


@pytest.mark.django_db
class TestSalesReportView:
    URL = "/api/v1/admin/reports/sales/"

    def test_default_month_period(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.get(self.URL)
        assert response.status_code == 200
        assert isinstance(response.data, list)

    def test_week_period(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.get(self.URL, {"period": "week"})
        assert response.status_code == 200

    def test_year_period(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.get(self.URL, {"period": "year"})
        assert response.status_code == 200

    def test_custom_date_range(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.get(self.URL, {
            "period": "custom",
            "start_date": "2026-01-01",
            "end_date": "2026-01-07",
        })
        assert response.status_code == 200

    def test_buyer_gets_403(self, client, buyer):
        client.force_authenticate(user=buyer)
        response = client.get(self.URL)
        assert response.status_code == 403


@pytest.mark.django_db
class TestTopProductsView:
    URL = "/api/v1/admin/reports/top-products/"

    def test_returns_list(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.get(self.URL)
        assert response.status_code == 200

    def test_custom_limit(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.get(self.URL, {"limit": "5"})
        assert response.status_code == 200

    def test_buyer_gets_403(self, client, buyer):
        client.force_authenticate(user=buyer)
        response = client.get(self.URL)
        assert response.status_code == 403


@pytest.mark.django_db
class TestTopSellersView:
    URL = "/api/v1/admin/reports/top-sellers/"

    def test_returns_list(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.get(self.URL)
        assert response.status_code == 200

    def test_custom_limit(self, client, admin):
        client.force_authenticate(user=admin)
        response = client.get(self.URL, {"limit": "3"})
        assert response.status_code == 200

    def test_buyer_gets_403(self, client, buyer):
        client.force_authenticate(user=buyer)
        response = client.get(self.URL)
        assert response.status_code == 403
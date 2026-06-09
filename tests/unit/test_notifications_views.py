
import pytest
from notifications.models import Notification


@pytest.mark.django_db
class TestNotificationViews:

    BASE = "/api/notifications"

    def test_list_authenticated(self, auth_client):
        response = auth_client.get(f"{self.BASE}/")
        assert response.status_code == 200

    def test_list_unauthenticated(self, api_client):
        response = api_client.get(f"{self.BASE}/")
        assert response.status_code == 401

    def test_mark_read_success(self, auth_client, test_user):
        n = Notification.objects.create(
            user=test_user, message="Hi", is_read=False
        )
        response = auth_client.post(f"{self.BASE}/{n.id}/mark-read/")
        assert response.status_code == 200
        n.refresh_from_db()
        assert n.is_read is True

    def test_mark_read_not_found(self, auth_client):
        response = auth_client.post(f"{self.BASE}/99999/mark-read/")
        assert response.status_code == 404

    def test_mark_all_read(self, auth_client, test_user):
        Notification.objects.create(user=test_user, message="A", is_read=False)
        Notification.objects.create(user=test_user, message="B", is_read=False)
        response = auth_client.post(f"{self.BASE}/mark-all-read/")
        assert response.status_code == 200
        assert Notification.objects.filter(
            user=test_user, is_read=False
        ).count() == 0

    def test_mark_all_read_unauthenticated(self, api_client):
        response = api_client.post(f"{self.BASE}/mark-all-read/")
        assert response.status_code == 401
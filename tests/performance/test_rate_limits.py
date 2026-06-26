import pytest
import redis
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from tests.urls import AUTH_LOGIN, AUTH_REGISTER, ORDERS, PRODUCTS

User = get_user_model()
from django.test import override_settings


def redis_available():
    """
    Check if Redis is running and reachable.
    """
    try:
        r = redis.Redis(host="localhost", port=6379, db=0)
        r.ping()
        return True
    except redis.ConnectionError:
        return False


pytestmark = pytest.mark.skipif(not redis_available(), reason="Redis is not running.")


@pytest.mark.django_db
class TestRateLimits:
    def setup_method(self):
        self.client = APIClient()

        self.user = User.objects.create_user(username="testuser", password="pass123")

    def test_login_rate_limit(self):
        for i in range(6):
            response = self.client.post(
                AUTH_LOGIN, {"username": "wronguser", "password": "wrongpass"}
            )

            if i >= 5:
                assert response.status_code == 429
            else:
                assert response.status_code == 401

    def test_register_rate_limit(self):
        for i in range(4):
            response = self.client.post(
                AUTH_REGISTER,
                {
                    "username": f"user{i}",
                    "email": f"user{i}@example.com",
                    "password": "StrongPass123",
                    "password2": "StrongPass123",
                },
            )

            if i >= 3:
                assert response.status_code == 429
            else:
                assert response.status_code == 201

    def test_order_rate_limit(self):
        self.client.force_authenticate(user=self.user)

        for i in range(12):
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

            if i >= 10:
                assert response.status_code == 429
            else:
                assert response.status_code in [201, 400]

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_CLASSES": [
                "rest_framework.throttling.AnonRateThrottle",
                "rest_framework.throttling.UserRateThrottle",
            ],
            "DEFAULT_THROTTLE_RATES": {
                "search": "30/minute",
            },
        },
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                "LOCATION": "throttle-test",
            }
        },
    )
    def test_search_rate_limit(self):
        """Test that SearchRateThrottle allows 30 requests then blocks"""
        from ethionex_api.throttles import SearchRateThrottle
        from unittest.mock import MagicMock
        from django.core.cache import cache

        cache.clear()

        throttle = SearchRateThrottle()
        throttle.rate = "30/minute"
        throttle.num_requests, throttle.duration = 30, 60

        request = MagicMock()
        request.user.is_authenticated = True
        request.user.id = 9999
        request.META = {"REMOTE_ADDR": "127.0.0.1"}

        view = MagicMock()

        for i in range(30):
            assert throttle.allow_request(request, view) is True

        assert throttle.allow_request(request, view) is False

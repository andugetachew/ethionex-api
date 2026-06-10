# tests/unit/test_throttling.py
import pytest
from django.core.cache import cache
from ethionex_api.throttles import (
    LoginRateThrottle,
    RegisterRateThrottle,
    OrderRateThrottle,
)
from tests.urls import AUTH_LOGIN, AUTH_REGISTER, ORDERS


@pytest.mark.django_db
class TestThrottleConfig:
    """Verify throttle classes have the correct rate and scope configured."""

    def setup_method(self):
        cache.clear()

    def test_login_throttle_rate(self):
        assert LoginRateThrottle().rate == "5/minute"
        assert LoginRateThrottle().scope == "login"

    def test_register_throttle_rate(self):
        assert RegisterRateThrottle().rate == "3/minute"
        assert RegisterRateThrottle().scope == "register"

    def test_order_throttle_rate(self):
        assert OrderRateThrottle().rate == "10/minute"
        assert OrderRateThrottle().scope == "order"


@pytest.mark.django_db
class TestThrottleBehavior:
    """Verify the endpoints actually enforce the limits."""

    def setup_method(self):
        cache.clear()

    def test_login_blocks_after_limit(self, api_client):
        """5 failures → 6th attempt returns 429."""
        for _ in range(5):
            api_client.post(AUTH_LOGIN, {"username": "x", "password": "x"})
        response = api_client.post(AUTH_LOGIN, {"username": "x", "password": "x"})
        assert response.status_code == 429

    def test_register_blocks_after_limit(self, api_client):
        """3 registrations → 4th attempt returns 429."""
        for i in range(3):
            api_client.post(
                AUTH_REGISTER,
                {
                    "username": f"u{i}",
                    "email": f"u{i}@test.com",
                    "password": "Pass123!",
                    "password2": "Pass123!",
                },
            )
        response = api_client.post(
            AUTH_REGISTER,
            {
                "username": "over",
                "email": "over@test.com",
                "password": "Pass123!",
                "password2": "Pass123!",
            },
        )
        assert response.status_code == 429

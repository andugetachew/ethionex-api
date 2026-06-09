# tests/integration/test_auth_flow.py
import pytest
from tests.urls import AUTH_REGISTER, AUTH_LOGIN, AUTH_PROFILE


@pytest.mark.django_db
class TestAuthFlow:
    def test_complete_auth_flow(self, api_client):
        # Step 1: Register
        register_data = {
            "username": "flowuser",
            "email": "flow@test.com",
            "password": "FlowPass123",
            "password2": "FlowPass123",
        }
        response = api_client.post(AUTH_REGISTER, register_data)
        assert response.status_code == 201

        # Step 2: Login
        login_data = {"username": "flowuser", "password": "FlowPass123"}
        response = api_client.post(AUTH_LOGIN, login_data)
        assert response.status_code == 200
        assert "access" in response.data
        token = response.data["access"]

        # Step 3: Access protected endpoint
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = api_client.get(AUTH_PROFILE)
        assert response.status_code == 200
        assert response.data["username"] == "flowuser"

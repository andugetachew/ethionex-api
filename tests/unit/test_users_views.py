# tests/unit/test_users_views.py
import uuid
import pytest
from unittest.mock import patch
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

# Correct URL prefix based on ethionex_api/urls.py
# users.urls is mounted at: /api/v1/auth/
BASE = "/api/v1/auth"


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def verified_user(db):
    user = User.objects.create_user(
        username="verified", email="verified@test.com", password="SecurePass123"
    )
    user.is_email_verified = True
    user.save()
    return user


@pytest.fixture
def unverified_user(db):
    user = User.objects.create_user(
        username="unverified", email="unverified@test.com", password="SecurePass123"
    )
    user.is_email_verified = False
    user.email_verification_token = uuid.uuid4()
    user.token_created_at = timezone.now()
    user.save()
    return user


@pytest.mark.django_db
class TestRegisterView:

    @patch("users.views.send_welcome_email_task.delay")
    @patch("users.views.send_mail")
    def test_register_success(self, mock_mail, mock_task, client):
        mock_mail.return_value = 1
        response = client.post(f"{BASE}/register/", {
            "username": "newuser", "email": "new@test.com",
            "password": "SecurePass123", "password2": "SecurePass123",
        })
        assert response.status_code == 201
        assert User.objects.filter(email="new@test.com").exists()

    @patch("users.views.send_welcome_email_task.delay")
    @patch("users.views.send_mail")
    def test_register_sends_verification_email(self, mock_mail, mock_task, client):
        mock_mail.return_value = 1
        client.post(f"{BASE}/register/", {
            "username": "emailuser", "email": "email@test.com",
            "password": "SecurePass123", "password2": "SecurePass123",
        })
        assert mock_mail.called
        assert "email@test.com" in mock_mail.call_args[0][3]

    @patch("users.views.send_welcome_email_task.delay")
    @patch("users.views.send_mail")
    def test_celery_failure_is_silent(self, mock_mail, mock_task, client):
        mock_mail.return_value = 1
        mock_task.side_effect = Exception("Celery down")
        response = client.post(f"{BASE}/register/", {
            "username": "celery", "email": "celery@test.com",
            "password": "SecurePass123", "password2": "SecurePass123",
        })
        assert response.status_code == 201

    def test_duplicate_email_returns_400(self, client, verified_user):
        response = client.post(f"{BASE}/register/", {
            "username": "other", "email": "verified@test.com",
            "password": "SecurePass123", "password2": "SecurePass123",
        })
        assert response.status_code == 400

    def test_password_mismatch_returns_400(self, client):
        response = client.post(f"{BASE}/register/", {
            "username": "mis", "email": "mis@test.com",
            "password": "Pass123", "password2": "Pass456",
        })
        assert response.status_code == 400


@pytest.mark.django_db
class TestLoginView:

    def test_login_success(self, client, verified_user):
        response = client.post(f"{BASE}/login/", {
            "username": verified_user.username, "password": "SecurePass123"
        })
        assert response.status_code == 200
        assert "access" in response.data

    def test_wrong_password_returns_401(self, client, verified_user):
        response = client.post(f"{BASE}/login/", {
            "username": verified_user.username, "password": "wrong"
        })
        assert response.status_code == 401

    def test_missing_fields_returns_400(self, client):
        response = client.post(f"{BASE}/login/", {})
        assert response.status_code == 400


@pytest.mark.django_db
class TestUserProfileView:

    def test_get_profile_authenticated(self, client, verified_user):
        client.force_authenticate(user=verified_user)
        response = client.get(f"{BASE}/profile/")
        assert response.status_code == 200
        assert response.data["email"] == verified_user.email

    def test_get_profile_unauthenticated(self, client):
        response = client.get(f"{BASE}/profile/")
        assert response.status_code == 401

    def test_update_profile(self, client, verified_user):
        client.force_authenticate(user=verified_user)
        response = client.patch(f"{BASE}/profile/", {"bio": "Hello"})
        assert response.status_code == 200


@pytest.mark.django_db
class TestVerifyEmailView:

    def test_valid_token(self, client, unverified_user):
        token = str(unverified_user.email_verification_token)
        response = client.post(f"{BASE}/verify-email/", {"token": token})
        assert response.status_code == 200
        unverified_user.refresh_from_db()
        assert unverified_user.is_email_verified is True

    def test_invalid_token_returns_400(self, client):
        response = client.post(f"{BASE}/verify-email/", {"token": str(uuid.uuid4())})
        assert response.status_code == 400

    def test_expired_token_returns_400(self, client, db):
        user = User.objects.create_user(
            username="expired", email="expired@test.com", password="pass"
        )
        token = uuid.uuid4()
        user.email_verification_token = token
        user.token_created_at = timezone.now() - timedelta(days=2)
        user.is_email_verified = False
        user.save()
        response = client.post(f"{BASE}/verify-email/", {"token": str(token)})
        assert response.status_code == 400
    def test_clears_token_after_verify(self, client, unverified_user):
        original_token = str(unverified_user.email_verification_token)
        client.post(f"{BASE}/verify-email/", {"token": original_token})
        unverified_user.refresh_from_db()
        assert str(unverified_user.email_verification_token) != original_token
@pytest.mark.django_db
class TestResendVerificationView:

    @patch("users.views.send_mail")
    def test_resend_success(self, mock_mail, client, unverified_user):
        mock_mail.return_value = 1
        response = client.post(f"{BASE}/resend-verification/", {"email": unverified_user.email})
        assert response.status_code == 200
        assert mock_mail.called

    def test_already_verified_returns_400(self, client, verified_user):
        response = client.post(f"{BASE}/resend-verification/", {"email": verified_user.email})
        assert response.status_code == 400

    def test_unknown_email_returns_404(self, client):
        response = client.post(f"{BASE}/resend-verification/", {"email": "ghost@test.com"})
        assert response.status_code == 404


@pytest.mark.django_db
class TestPasswordResetView:

    @patch("users.views.send_mail")
    def test_known_email_returns_200(self, mock_mail, client, verified_user):
        mock_mail.return_value = 1
        response = client.post(f"{BASE}/password-reset/", {"email": verified_user.email})
        assert response.status_code == 200

    def test_unknown_email_still_200(self, client):
        response = client.post(f"{BASE}/password-reset/", {"email": "nobody@test.com"})
        assert response.status_code == 200

    @patch("users.views.send_mail")
    def test_sets_reset_token(self, mock_mail, client, verified_user):
        mock_mail.return_value = 1
        client.post(f"{BASE}/password-reset/", {"email": verified_user.email})
        verified_user.refresh_from_db()
        assert verified_user.reset_token


@pytest.mark.django_db
class TestPasswordResetConfirmView:

    def _set_token(self, user, expired=False):
        token = str(uuid.uuid4())
        user.reset_token = token
        user.reset_token_expires = (
            timezone.now() - timedelta(hours=1)
            if expired else timezone.now() + timedelta(hours=24)
        )
        user.save()
        return token

    def test_valid_token_resets_password(self, client, verified_user):
        token = self._set_token(verified_user)
        response = client.post(f"{BASE}/password-reset/confirm/", {
            "token": token, "password": "NewPass456", "password2": "NewPass456"
        })
        assert response.status_code == 200
        verified_user.refresh_from_db()
        assert verified_user.check_password("NewPass456")

    def test_expired_token_returns_400(self, client, verified_user):
        token = self._set_token(verified_user, expired=True)
        response = client.post(f"{BASE}/password-reset/confirm/", {
            "token": token, "password": "NewPass456", "password2": "NewPass456"
        })
        assert response.status_code == 400

    def test_invalid_token_returns_400(self, client):
        response = client.post(f"{BASE}/password-reset/confirm/", {
            "token": str(uuid.uuid4()), "password": "NewPass456", "password2": "NewPass456"
        })
        assert response.status_code == 400


@pytest.mark.django_db
class TestNewsletterViews:

    def test_subscribe_new(self, client):
        response = client.post(f"{BASE}/newsletter/subscribe/", {"email": "sub@test.com"})
        assert response.status_code == 201

    def test_subscribe_already_active(self, client):
        client.post(f"{BASE}/newsletter/subscribe/", {"email": "dup@test.com"})
        response = client.post(f"{BASE}/newsletter/subscribe/", {"email": "dup@test.com"})
        assert response.status_code == 200

    def test_subscribe_missing_email(self, client):
        response = client.post(f"{BASE}/newsletter/subscribe/", {})
        assert response.status_code == 400

    def test_unsubscribe_existing(self, client, db):
        from users.models import NewsletterSubscriber
        NewsletterSubscriber.objects.create(email="unsub@test.com", is_active=True)
        response = client.post(f"{BASE}/newsletter/unsubscribe/", {"email": "unsub@test.com"})
        assert response.status_code == 200

    def test_unsubscribe_unknown_returns_404(self, client):
        response = client.post(f"{BASE}/newsletter/unsubscribe/", {"email": "ghost@test.com"})
        assert response.status_code == 404

    def test_unsubscribe_missing_email(self, client):
        response = client.post(f"{BASE}/newsletter/unsubscribe/", {})
        assert response.status_code == 400


@pytest.mark.django_db
class TestCustomLoginView:

    def test_valid_credentials(self, client, verified_user):
        response = client.post(f"{BASE}/custom-login/", {
            "username": verified_user.username, "password": "SecurePass123"
        })
        assert response.status_code == 200
        assert "access" in response.data

    def test_invalid_credentials_returns_401(self, client):
        response = client.post(f"{BASE}/custom-login/", {
            "username": "nobody", "password": "wrong"
        })
        assert response.status_code == 401
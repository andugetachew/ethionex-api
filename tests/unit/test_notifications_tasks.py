import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from orders.models import Order

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="notifuser", email="notif@test.com", password="pass123"
    )


@pytest.fixture
def order(db, user):
    return Order.objects.create(
        user=user, full_name="Notif User", phone_number="09",
        address="Addr", city="City", payment_method="cash",
        status="pending", subtotal=200, total=200,
    )


@pytest.mark.django_db
class TestNotificationsWelcomeEmail:

    @patch("notifications.tasks.send_mail")
    def test_sends_to_user(self, mock_mail, user):
        from notifications.tasks import send_welcome_email_task
        mock_mail.return_value = 1
        result = send_welcome_email_task(user.id)
        assert mock_mail.called
        assert user.email in result

    @patch("notifications.tasks.send_mail")
    def test_user_not_found(self, mock_mail):
        from notifications.tasks import send_welcome_email_task
        result = send_welcome_email_task(99999)
        assert not mock_mail.called
        assert "Error" in result

    @patch("notifications.tasks.send_mail")
    def test_error_handled(self, mock_mail, user):
        from notifications.tasks import send_welcome_email_task
        mock_mail.side_effect = Exception("fail")
        result = send_welcome_email_task(user.id)
        assert "Error" in result


@pytest.mark.django_db
class TestNotificationsOrderConfirmation:

    @patch("notifications.tasks.send_mail")
    def test_sends_confirmation(self, mock_mail, order):
        from notifications.tasks import send_order_confirmation_task
        mock_mail.return_value = 1
        result = send_order_confirmation_task(order.id)
        assert mock_mail.called
        assert str(order.id) in result

    @patch("notifications.tasks.send_mail")
    def test_order_not_found(self, mock_mail):
        from notifications.tasks import send_order_confirmation_task
        result = send_order_confirmation_task(99999)
        assert not mock_mail.called
        assert "Error" in result

    @patch("notifications.tasks.send_mail")
    def test_error_handled(self, mock_mail, order):
        from notifications.tasks import send_order_confirmation_task
        mock_mail.side_effect = Exception("fail")
        result = send_order_confirmation_task(order.id)
        assert "Error" in result


@pytest.mark.django_db
class TestNotificationsPasswordReset:

    @patch("notifications.tasks.send_mail")
    def test_reset_link_in_message(self, mock_mail, user):
        from notifications.tasks import send_password_reset_email_task
        mock_mail.return_value = 1
        send_password_reset_email_task(user.id, "reset-tok-xyz")
        assert mock_mail.called
        message = mock_mail.call_args[0][1]
        assert "reset-tok-xyz" in message

    @patch("notifications.tasks.send_mail")
    def test_user_not_found(self, mock_mail):
        from notifications.tasks import send_password_reset_email_task
        result = send_password_reset_email_task(99999, "tok")
        assert not mock_mail.called
        assert "Error" in result

    @patch("notifications.tasks.send_mail")
    def test_error_handled(self, mock_mail, user):
        from notifications.tasks import send_password_reset_email_task
        mock_mail.side_effect = Exception("fail")
        result = send_password_reset_email_task(user.id, "tok")
        assert "Error" in result


@pytest.mark.django_db
class TestNotificationsVerificationEmail:

    @patch("notifications.tasks.send_mail")
    def test_token_in_message(self, mock_mail, user):
        from notifications.tasks import send_verification_email_task
        mock_mail.return_value = 1
        send_verification_email_task(user.id, "verify-tok-abc")
        assert mock_mail.called
        message = mock_mail.call_args[0][1]
        assert "verify-tok-abc" in message

    @patch("notifications.tasks.send_mail")
    def test_user_not_found(self, mock_mail):
        from notifications.tasks import send_verification_email_task
        result = send_verification_email_task(99999, "tok")
        assert not mock_mail.called
        assert "Error" in result

    @patch("notifications.tasks.send_mail")
    def test_error_handled(self, mock_mail, user):
        from notifications.tasks import send_verification_email_task
        mock_mail.side_effect = Exception("fail")
        result = send_verification_email_task(user.id, "tok")
        assert "Error" in result


@pytest.mark.django_db
class TestNotificationsLowStockAlert:

    @patch("notifications.tasks.send_mail")
    def test_sends_alert(self, mock_mail, test_product):
        from notifications.tasks import send_low_stock_alert_task
        mock_mail.return_value = 1
        result = send_low_stock_alert_task(test_product.id)
        assert isinstance(result, str)

    @patch("notifications.tasks.send_mail")
    def test_product_not_found(self, mock_mail):
        from notifications.tasks import send_low_stock_alert_task
        result = send_low_stock_alert_task(99999)
        assert not mock_mail.called
        assert "Error" in result

    @patch("notifications.tasks.send_mail")
    def test_error_handled(self, mock_mail, test_product):
        from notifications.tasks import send_low_stock_alert_task
        mock_mail.side_effect = Exception("fail")
        result = send_low_stock_alert_task(test_product.id)
        assert "Error" in result


@pytest.mark.django_db
class TestNotificationsSellerOrderNotification:

    @patch("notifications.tasks.send_mail")
    def test_sends_to_seller(self, mock_mail, order, test_seller):
        from notifications.tasks import send_seller_order_notification_task
        mock_mail.return_value = 1
        result = send_seller_order_notification_task(order.id, test_seller.id)
        assert mock_mail.called
        assert str(order.id) in result

    @patch("notifications.tasks.send_mail")
    def test_order_not_found(self, mock_mail, test_seller):
        from notifications.tasks import send_seller_order_notification_task
        result = send_seller_order_notification_task(99999, test_seller.id)
        assert not mock_mail.called
        assert "Error" in result

    @patch("notifications.tasks.send_mail")
    def test_seller_not_found(self, mock_mail, order):
        from notifications.tasks import send_seller_order_notification_task
        result = send_seller_order_notification_task(order.id, 99999)
        assert not mock_mail.called
        assert "Error" in result

    @patch("notifications.tasks.send_mail")
    def test_error_handled(self, mock_mail, order, test_seller):
        from notifications.tasks import send_seller_order_notification_task
        mock_mail.side_effect = Exception("fail")
        result = send_seller_order_notification_task(order.id, test_seller.id)
        assert "Error" in result


class TestNotificationsMisc:

    def test_health_check_returns_ok(self):
        from notifications.tasks import health_check
        result = health_check()
        assert result["status"] == "ok"
        assert "Celery" in result["message"]

    def test_backup_returns_string(self):
        from notifications.tasks import automated_database_backup
        result = automated_database_backup()
        assert isinstance(result, str)
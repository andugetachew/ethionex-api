# tests/unit/test_users_tasks.py
import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from orders.models import Order
from cart.models import Cart

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username="taskuser", email="task@test.com", password="pass123"
    )


@pytest.fixture
def order(db, user):
    return Order.objects.create(
        user=user, full_name="Task User", phone_number="09",
        address="Addr", city="City", payment_method="cash",
        status="pending", subtotal=100, total=100,
    )


@pytest.mark.django_db
class TestWelcomeEmailTask:

    @patch("users.tasks.send_mail")
    def test_sends_to_user_email(self, mock_mail, user):
        from users.tasks import send_welcome_email_task
        mock_mail.return_value = 1
        result = send_welcome_email_task(user.id)
        assert mock_mail.called
        assert user.email in mock_mail.call_args[1]["recipient_list"]
        assert user.email in result

    @patch("users.tasks.send_mail")
    def test_user_not_found(self, mock_mail):
        from users.tasks import send_welcome_email_task
        result = send_welcome_email_task(99999)
        assert not mock_mail.called
        assert "99999" in result

    @patch("users.tasks.send_mail")
    def test_smtp_error_handled(self, mock_mail, user):
        from users.tasks import send_welcome_email_task
        mock_mail.side_effect = Exception("SMTP down")
        result = send_welcome_email_task(user.id)
        assert "Error" in result


@pytest.mark.django_db
class TestVerificationEmailTask:

    @patch("users.tasks.send_mail")
    def test_token_in_message_body(self, mock_mail, user):
        from users.tasks import send_verification_email_task
        mock_mail.return_value = 1
        send_verification_email_task(user.id, "verify-tok-abc")
        assert mock_mail.called
        message = mock_mail.call_args[1]["message"]
        assert "verify-tok-abc" in message

    @patch("users.tasks.send_mail")
    def test_user_not_found(self, mock_mail):
        from users.tasks import send_verification_email_task
        result = send_verification_email_task(99999, "tok")
        assert not mock_mail.called
        assert "99999" in result

    @patch("users.tasks.send_mail")
    def test_error_handled(self, mock_mail, user):
        from users.tasks import send_verification_email_task
        mock_mail.side_effect = Exception("fail")
        result = send_verification_email_task(user.id, "tok")
        assert "Error" in result


@pytest.mark.django_db
class TestPasswordResetEmailTask:

    @patch("users.tasks.send_mail")
    def test_reset_link_in_message(self, mock_mail, user):
        from users.tasks import send_password_reset_email_task
        mock_mail.return_value = 1
        send_password_reset_email_task(user.id, "reset-xyz")
        message = mock_mail.call_args[1]["message"]
        assert "reset-xyz" in message

    @patch("users.tasks.send_mail")
    def test_user_not_found(self, mock_mail):
        from users.tasks import send_password_reset_email_task
        result = send_password_reset_email_task(99999, "tok")
        assert not mock_mail.called
        assert "99999" in result

    @patch("users.tasks.send_mail")
    def test_error_handled(self, mock_mail, user):
        from users.tasks import send_password_reset_email_task
        mock_mail.side_effect = Exception("fail")
        result = send_password_reset_email_task(user.id, "tok")
        assert "Error" in result


@pytest.mark.django_db
class TestOrderConfirmationTask:

    @patch("users.tasks.send_mail")
    def test_sends_confirmation(self, mock_mail, order):
        from users.tasks import send_order_confirmation_task
        mock_mail.return_value = 1
        result = send_order_confirmation_task(order.id)
        assert mock_mail.called
        assert order.order_number in result

    @patch("users.tasks.send_mail")
    def test_order_not_found(self, mock_mail):
        from users.tasks import send_order_confirmation_task
        result = send_order_confirmation_task(99999)
        assert not mock_mail.called
        assert "99999" in result

    @patch("users.tasks.send_mail")
    def test_error_handled(self, mock_mail, order):
        from users.tasks import send_order_confirmation_task
        mock_mail.side_effect = Exception("fail")
        result = send_order_confirmation_task(order.id)
        assert "Error" in result


@pytest.mark.django_db
class TestUpdateOrderStatusTask:

    def test_updates_status_in_db(self, order):
        from users.tasks import update_order_status_task
        result = update_order_status_task(order.id, "paid")
        order.refresh_from_db()
        assert order.status == "paid"
        assert "paid" in result

    def test_order_not_found(self):
        from users.tasks import update_order_status_task
        result = update_order_status_task(99999, "paid")
        assert "99999" in result

    def test_error_handled(self, order):
        from users.tasks import update_order_status_task
        with patch("users.tasks.Order.objects.get") as mock_get:
            mock_get.side_effect = Exception("DB error")
            result = update_order_status_task(order.id, "paid")
            assert "Error" in result


@pytest.mark.django_db
class TestLowStockAlertTask:

    @patch("users.tasks.send_mail")
    def test_alert_sent(self, mock_mail, test_product):
        from users.tasks import send_low_stock_alert_task
        mock_mail.return_value = 1
        result = send_low_stock_alert_task(test_product.id)
        assert mock_mail.called
        assert str(test_product.id) in result

    @patch("users.tasks.send_mail")
    def test_no_email_when_no_seller_email(self, mock_mail, test_product, test_seller):
        from users.tasks import send_low_stock_alert_task
        test_seller.email = ""
        test_seller.save()
        send_low_stock_alert_task(test_product.id)
        assert not mock_mail.called

    @patch("users.tasks.send_mail")
    def test_product_not_found(self, mock_mail):
        from users.tasks import send_low_stock_alert_task
        result = send_low_stock_alert_task(99999)
        assert not mock_mail.called
        assert "99999" in result

    @patch("users.tasks.send_mail")
    def test_error_handled(self, mock_mail, test_product):
        from users.tasks import send_low_stock_alert_task
        mock_mail.side_effect = Exception("fail")
        result = send_low_stock_alert_task(test_product.id)
        assert "Error" in result


@pytest.mark.django_db
class TestBulkNewsletterTask:

    @patch("users.tasks.send_mail")
    def test_sends_to_all(self, mock_mail):
        from users.tasks import send_bulk_newsletter_task
        mock_mail.return_value = 1
        result = send_bulk_newsletter_task(
            ["a@test.com", "b@test.com", "c@test.com"], "Sub", "Body"
        )
        assert mock_mail.call_count == 3
        assert "3" in result

    @patch("users.tasks.send_mail")
    def test_partial_failure_counted(self, mock_mail):
        from users.tasks import send_bulk_newsletter_task
        mock_mail.side_effect = [1, Exception("fail"), 1]
        result = send_bulk_newsletter_task(
            ["a@test.com", "b@test.com", "c@test.com"], "S", "M"
        )
        assert "2" in result

    @patch("users.tasks.send_mail")
    def test_empty_list(self, mock_mail):
        from users.tasks import send_bulk_newsletter_task
        result = send_bulk_newsletter_task([], "S", "M")
        assert not mock_mail.called
        assert "0" in result


@pytest.mark.django_db
class TestCleanupExpiredCartsTask:

    def test_deletes_old_carts(self, user):
        from users.tasks import cleanup_expired_carts_task
        cart = Cart.objects.create(user=user)
        Cart.objects.filter(pk=cart.pk).update(
            updated_at=timezone.now() - timedelta(days=31)
        )
        result = cleanup_expired_carts_task()
        assert "Deleted" in result
        assert not Cart.objects.filter(pk=cart.pk).exists()

    def test_keeps_recent_carts(self, user):
        from users.tasks import cleanup_expired_carts_task
        Cart.objects.create(user=user)
        cleanup_expired_carts_task()
        assert Cart.objects.filter(user=user).exists()

    def test_error_handled(self):
        from users.tasks import cleanup_expired_carts_task
        with patch("users.tasks.Cart.objects.filter") as mock_filter:
            mock_filter.side_effect = Exception("DB error")
            result = cleanup_expired_carts_task()
            assert "Error" in result
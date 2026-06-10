import pytest
from unittest.mock import patch
from django.contrib.auth import get_user_model
from orders.models import Order
from notifications.email_service import EmailService

User = get_user_model()


@pytest.fixture(autouse=True)
def mock_email_sending():
    """Override conftest mock — let tests control send_mail directly"""
    yield


@pytest.fixture
def test_order(db, test_user):
    return Order.objects.create(
        user=test_user,
        order_number="TEST-ORDER-001",
        full_name="Test User",
        phone_number="0912345678",
        address="Test Address",
        city="Addis Ababa",
        payment_method="cash",
        status="pending",
        subtotal=1000,
        total=1000,
    )


@patch("notifications.email_service.send_mail")
def test_send_order_confirmation_success(mock_send_mail, test_order):
    mock_send_mail.return_value = 1
    result = EmailService.send_order_confirmation(test_order)
    assert result is True
    mock_send_mail.assert_called_once()


@patch("notifications.email_service.send_mail")
def test_send_order_confirmation_failure(mock_send_mail, test_order):
    mock_send_mail.side_effect = Exception("SMTP error")
    result = EmailService.send_order_confirmation(test_order)
    assert result is False


@patch("notifications.email_service.send_mail")
def test_send_order_confirmation_exception(mock_send_mail, test_order):
    mock_send_mail.side_effect = Exception("SMTP Error")
    result = EmailService.send_order_confirmation(test_order)
    assert result is False


@patch("notifications.email_service.send_mail")
def test_send_order_status_update_success(mock_send_mail, test_order):
    mock_send_mail.return_value = 1
    result = EmailService.send_order_status_update(
        test_order,
        old_status="pending",
        new_status="paid",
    )
    assert result is True
    mock_send_mail.assert_called_once()


@patch("notifications.email_service.send_mail")
def test_send_order_status_update_failure(mock_send_mail, test_order):
    mock_send_mail.side_effect = Exception("SMTP error")
    result = EmailService.send_order_status_update(
        test_order,
        old_status="pending",
        new_status="paid",
    )
    assert result is False


@patch("notifications.email_service.send_mail")
def test_email_service_handles_exception_gracefully(mock_send_mail, test_order):
    mock_send_mail.side_effect = Exception("Unexpected error")
    result1 = EmailService.send_order_confirmation(test_order)
    result2 = EmailService.send_order_status_update(
        test_order,
        old_status="pending",
        new_status="shipped",
    )
    assert result1 is False
    assert result2 is False


@patch("notifications.email_service.send_mail")
def test_send_welcome_email_success(mock_send_mail, test_user):
    mock_send_mail.return_value = 1
    result = EmailService.send_welcome_email(test_user)
    assert result is True
    mock_send_mail.assert_called_once()


@patch("notifications.email_service.send_mail")
def test_send_welcome_email_failure(mock_send_mail, test_user):
    mock_send_mail.side_effect = Exception("SMTP error")
    result = EmailService.send_welcome_email(test_user)
    assert result is False


@patch("notifications.email_service.send_mail")
def test_send_order_status_update_to_shipped(mock_send_mail, test_order):
    mock_send_mail.return_value = 1
    result = EmailService.send_order_status_update(
        test_order,
        old_status="paid",
        new_status="shipped",
    )
    assert result is True
    mock_send_mail.assert_called_once()


@patch("notifications.email_service.send_mail")
def test_send_payment_receipt_success(mock_send_mail, test_order):
    mock_send_mail.return_value = 1
    result = EmailService.send_payment_receipt(test_order, payment_details={})
    assert result is True
    mock_send_mail.assert_called_once()


@patch("notifications.email_service.send_mail")
def test_send_payment_receipt_failure(mock_send_mail, test_order):
    mock_send_mail.side_effect = Exception("SMTP error")
    result = EmailService.send_payment_receipt(test_order, payment_details={})
    assert result is False


@patch("notifications.email_service.send_mail")
def test_send_seller_order_notification_success(mock_send_mail, test_order, test_user):
    mock_send_mail.return_value = 1
    result = EmailService.send_seller_order_notification(test_order, seller=test_user)
    assert result is True
    mock_send_mail.assert_called_once()


@patch("notifications.email_service.send_mail")
def test_send_seller_order_notification_failure(mock_send_mail, test_order, test_user):
    mock_send_mail.side_effect = Exception("SMTP error")
    result = EmailService.send_seller_order_notification(test_order, seller=test_user)
    assert result is False


@patch("notifications.email_service.send_mail")
def test_send_password_reset_email_success(mock_send_mail, test_user):
    mock_send_mail.return_value = 1
    result = EmailService.send_password_reset_email(test_user, token="abc123")
    assert result is True
    mock_send_mail.assert_called_once()


@patch("notifications.email_service.send_mail")
def test_send_password_reset_email_failure(mock_send_mail, test_user):
    mock_send_mail.side_effect = Exception("SMTP error")
    result = EmailService.send_password_reset_email(test_user, token="abc123")
    assert result is False

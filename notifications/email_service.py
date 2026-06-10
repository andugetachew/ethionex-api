from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailService:

    @staticmethod
    def send_welcome_email(user):
        subject = f"Welcome to EthioNex, {user.username}!"
        message = f"""
Welcome to EthioNex!

Hi {user.username},

Thank you for joining EthioNex!
"""
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            return True
        except Exception:
            return False

    @staticmethod
    def send_order_confirmation(order):
        subject = f"Order Confirmation #{order.order_number}"

        items_plain = ""
        for item in order.items.all():
            subtotal = item.quantity * item.price
            items_plain += f"- {item.product.title} x {item.quantity} - ${subtotal}\n"

        message = f"""
Order Confirmation #{order.order_number}

{items_plain}
Total: ${order.total}
"""
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.user.email])
            return True
        except Exception:
            return False

    @staticmethod
    def send_order_status_update(order, old_status, new_status):
        subject = f"Order #{order.order_number} Status Update"

        message = f"""
Order #{order.order_number}

{old_status} -> {new_status}
"""

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.user.email])
            return True
        except Exception:
            return False

    @staticmethod
    def send_payment_receipt(order, payment_details):
        subject = f"Payment Receipt #{order.order_number}"
        message = f"""
Payment received for order {order.order_number}
"""
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [order.user.email])
            return True
        except Exception:
            return False

    @staticmethod
    def send_password_reset_email(user, token):
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        subject = "Password Reset"
        message = f"Reset link: {reset_url}"

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
            return True
        except Exception:
            return False

    @staticmethod
    def send_seller_order_notification(order, seller):
        subject = f"New Order #{order.order_number}"
        message = "New order received"

        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [seller.email])
            return True
        except Exception:
            return False

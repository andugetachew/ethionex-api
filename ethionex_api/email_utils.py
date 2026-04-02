from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_order_confirmation(order):
    """Send order confirmation email to customer"""
    subject = f"Order Confirmation #{order.order_number}"

    context = {
        "order": order,
        "customer_name": order.full_name,
        "order_number": order.order_number,
        "total": order.total,
        "items": order.items.all(),
        "delivery_fee": order.delivery_fee,
    }

    html_message = render_to_string("emails/order_confirmation.html", context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_order_status_update(order, old_status, new_status):
    """Send email when order status changes"""
    subject = f"Order #{order.order_number} Status Update"

    context = {
        "order": order,
        "customer_name": order.full_name,
        "order_number": order.order_number,
        "old_status": old_status,
        "new_status": new_status,
        "total": order.total,
    }

    html_message = render_to_string("emails/order_status_update.html", context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_welcome_email(user):
    """Send welcome email to new user"""
    subject = "Welcome to EthioNex Marketplace!"

    context = {"username": user.username, "is_seller": user.is_seller}

    html_message = render_to_string("emails/welcome.html", context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject,
        plain_message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        html_message=html_message,
        fail_silently=False,
    )

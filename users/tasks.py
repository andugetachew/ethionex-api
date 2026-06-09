from celery import shared_task

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from datetime import timedelta

from orders.models import Order
from products.models import Product
from cart.models import Cart

User = get_user_model()


@shared_task
def send_welcome_email_task(user_id):
    """Send welcome email asynchronously"""

    try:
        user = User.objects.get(id=user_id)

        send_mail(
            subject="Welcome to EthioNex",
            message=f"""
Hi {user.username},

Welcome to EthioNex!

Thank you for joining our marketplace platform.

We are excited to have you with us.

Best regards,
EthioNex Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return f"Welcome email sent to {user.email}"

    except User.DoesNotExist:
        return f"User with id {user_id} not found"

    except Exception as e:
        return f"Error sending welcome email: {str(e)}"


@shared_task
def send_verification_email_task(user_id, verification_token):
    """Send verification email asynchronously"""

    try:
        user = User.objects.get(id=user_id)

        verification_link = (
            f"{settings.FRONTEND_URL}/verify-email" f"?token={verification_token}"
        )

        send_mail(
            subject="Verify Your Email - EthioNex",
            message=f"""
Hi {user.username},

Please verify your email address by clicking the link below:

{verification_link}

This link expires in 24 hours.

Best regards,
EthioNex Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return f"Verification email sent to {user.email}"

    except User.DoesNotExist:
        return f"User with id {user_id} not found"

    except Exception as e:
        return f"Error sending verification email: {str(e)}"


@shared_task
def send_password_reset_email_task(user_id, reset_token):
    """Send password reset email asynchronously"""

    try:
        user = User.objects.get(id=user_id)

        reset_link = f"{settings.FRONTEND_URL}/reset-password" f"?token={reset_token}"

        send_mail(
            subject="Password Reset - EthioNex",
            message=f"""
Hi {user.username},

Click the link below to reset your password:

{reset_link}

This link expires in 24 hours.

If you did not request this reset, ignore this email.

Best regards,
EthioNex Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return f"Password reset email sent to {user.email}"

    except User.DoesNotExist:
        return f"User with id {user_id} not found"

    except Exception as e:
        return f"Error sending password reset email: {str(e)}"


@shared_task
def send_order_confirmation_task(order_id):
    """Send order confirmation email asynchronously"""

    try:
        order = Order.objects.select_related("user").get(id=order_id)

        send_mail(
            subject=f"Order Confirmation #{order.order_number}",
            message=f"""
Hi {order.user.username},

Thank you for your order!

Order Number: {order.order_number}
Total Amount: ${order.total}

Your order has been received and is being processed.

Best regards,
EthioNex Team
""",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            fail_silently=False,
        )

        return f"Order confirmation email sent " f"for order #{order.order_number}"

    except Order.DoesNotExist:
        return f"Order with id {order_id} not found"

    except Exception as e:
        return f"Error sending order confirmation: {str(e)}"


@shared_task
def update_order_status_task(order_id, new_status):
    """Update order status asynchronously"""

    try:
        order = Order.objects.get(id=order_id)

        order.status = new_status
        order.save()

        return f"Order #{order.order_number} " f"status updated to {new_status}"

    except Order.DoesNotExist:
        return f"Order with id {order_id} not found"

    except Exception as e:
        return f"Error updating order status: {str(e)}"


@shared_task
def send_low_stock_alert_task(product_id):
    """Send low stock alert to seller"""

    try:
        product = Product.objects.select_related("seller").get(id=product_id)

        seller_email = product.seller.email

        if seller_email:
            send_mail(
                subject=f"Low Stock Alert: {product.title}",
                message=f"""
Hello {product.seller.username},

Your product "{product.title}" is running low on stock.

Remaining Quantity: {product.stock_quantity}

Please restock soon to avoid missing sales.

Best regards,
EthioNex Team
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[seller_email],
                fail_silently=False,
            )

        return f"Low stock alert sent for product {product.id}"

    except Product.DoesNotExist:
        return f"Product with id {product_id} not found"

    except Exception as e:
        return f"Error sending low stock alert: {str(e)}"


@shared_task
def send_bulk_newsletter_task(email_list, subject, message):
    """Send newsletter emails asynchronously"""

    success_count = 0
    failed_count = 0

    for email in email_list:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )

            success_count += 1

        except Exception:
            failed_count += 1

    return (
        f"Newsletter sent successfully to {success_count} users. "
        f"Failed: {failed_count}"
    )


@shared_task
def cleanup_expired_carts_task():
    """Delete carts inactive for more than 30 days"""

    try:
        cutoff_date = timezone.now() - timedelta(days=30)

        expired_carts = Cart.objects.filter(updated_at__lt=cutoff_date)

        deleted_count = expired_carts.count()

        expired_carts.delete()

        return f"Deleted {deleted_count} expired carts"

    except Exception as e:
        return f"Error cleaning expired carts: {str(e)}"

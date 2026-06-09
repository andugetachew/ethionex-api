from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()
from orders.models import Order
from products.models import Product
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_welcome_email_task(user_id):
    """Send welcome email to new user"""
    try:
        user = User.objects.get(id=user_id)
        subject = "Welcome to EthioNex!"
        message = f"""
        Hi {user.username},
        
        Welcome to EthioNex! We're excited to have you on board.
        
        Get started by exploring our products:
        {settings.FRONTEND_URL}/products
        
        Best regards,
        The EthioNex Team
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return f"Welcome email sent to {user.email}"
    except Exception as e:
        logger.error(f"Failed to send welcome email: {e}")
        return f"Error: {str(e)}"


@shared_task
def send_order_confirmation_task(order_id):
    """Send order confirmation email"""
    try:
        order = Order.objects.select_related("user").get(id=order_id)
        subject = f"Order Confirmation #{order.order_number}"
        message = f"""
        Hi {order.user.username},
        
        Thank you for your order!
        
        Order Number: {order.order_number}
        Total Amount: ${order.total}
        
        Track your order: {settings.FRONTEND_URL}/orders/{order.id}/track
        
        Best regards,
        The EthioNex Team
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.user.email],
            fail_silently=False,
        )
        return f"Order confirmation sent for order {order_id}"
    except Exception as e:
        logger.error(f"Failed to send order confirmation: {e}")
        return f"Error: {str(e)}"


@shared_task
def send_password_reset_email_task(user_id, reset_token):
    """Send password reset email"""
    try:
        user = User.objects.get(id=user_id)
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        subject = "Password Reset Request"
        message = f"""
        Hi {user.username},
        
        You requested a password reset.
        
        Click the link below to reset your password:
        {reset_link}
        
        This link expires in 24 hours.
        
        If you didn't request this, please ignore this email.
        
        Best regards,
        The EthioNex Team
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return f"Password reset email sent to {user.email}"
    except Exception as e:
        logger.error(f"Failed to send password reset email: {e}")
        return f"Error: {str(e)}"


@shared_task
def send_verification_email_task(user_id, verification_token):
    """Send email verification link"""
    try:
        user = User.objects.get(id=user_id)
        verify_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        subject = "Verify Your Email Address"
        message = f"""
        Hi {user.username},
        
        Please verify your email address by clicking the link below:
        {verify_link}
        
        This link expires in 24 hours.
        
        Best regards,
        The EthioNex Team
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return f"Verification email sent to {user.email}"
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")
        return f"Error: {str(e)}"


@shared_task
def send_low_stock_alert_task(product_id):
    """Send low stock alert to seller"""
    try:
        product = Product.objects.select_related("seller").get(id=product_id)
        if product.stock_quantity <= product.reorder_level:
            subject = f"Low Stock Alert: {product.title}"
            message = f"""
            Hi {product.seller.username},
            
            Your product "{product.title}" is running low on stock.
            
            Current Stock: {product.stock_quantity}
            Reorder Level: {product.reorder_level}
            
            Please restock soon to avoid stockouts.
            
            Best regards,
            The EthioNex Team
            """
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [product.seller.email],
                fail_silently=False,
            )
            return f"Low stock alert sent for product {product_id}"
        return f"Product {product_id} has sufficient stock"
    except Exception as e:
        logger.error(f"Failed to send low stock alert: {e}")
        return f"Error: {str(e)}"


@shared_task
def send_seller_order_notification_task(order_id, seller_id):
    """Notify seller about new order"""
    try:
        from orders.models import Order

        order = Order.objects.get(id=order_id)
        seller = User.objects.get(id=seller_id)

        subject = f"New Order Received! #{order.order_number}"
        message = f"""
        Hi {seller.username},
        
        You have received a new order!
        
        Order Number: {order.order_number}
        Total Amount: ${order.total}
        
        Please process this order as soon as possible.
        
        Best regards,
        The EthioNex Team
        """
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [seller.email],
            fail_silently=False,
        )
        return f"Seller notification sent for order {order_id}"
    except Exception as e:
        logger.error(f"Failed to send seller notification: {e}")
        return f"Error: {str(e)}"


@shared_task
def automated_database_backup():
    """Run database backup daily (PostgreSQL only)"""
    try:
        from scripts.backup_db import DatabaseBackup

        backup = DatabaseBackup()
        backup_file = backup.create_backup()

        if backup_file:
            backup.cleanup_local_backups(days=7)
            return f"Backup completed: {backup_file}"
        return "Backup failed: No backup file created"
    except ImportError:
        return "Database backup not configured"
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return f"Backup error: {str(e)}"


@shared_task
def health_check():
    """Check if Celery is working"""
    return {"status": "ok", "message": "Celery worker is active"}

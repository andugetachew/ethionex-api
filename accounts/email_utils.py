from django.core.mail import send_mail
from django.conf import settings
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
import threading


class EmailThread(threading.Thread):
    """Send emails asynchronously in background"""

    def __init__(self, subject, message, from_email, recipient_list, html_message=None):
        self.subject = subject
        self.message = message
        self.from_email = from_email
        self.recipient_list = recipient_list
        self.html_message = html_message
        threading.Thread.__init__(self)

    def run(self):
        try:
            send_mail(
                self.subject,
                self.message,
                self.from_email,
                self.recipient_list,
                fail_silently=True,
                html_message=self.html_message,
            )
        except Exception:
            pass


def send_verification_email(user):
    """Email verification is DISABLED - user auto-verified"""
    # Auto-verify user without sending email
    user.is_email_verified = True
    user.email_verification_token = None
    user.save()
    print(f"User {user.username} auto-verified (email disabled)")


def verify_email_token(token):
    """Email verification is DISABLED"""
    return True, "Email verification is disabled. Account auto-verified."

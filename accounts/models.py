from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_seller = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)  # Add this
    email_verification_token = models.CharField(
        max_length=255, blank=True, null=True
    )  # Add this
    token_created_at = models.DateTimeField(blank=True, null=True)  # Add this
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

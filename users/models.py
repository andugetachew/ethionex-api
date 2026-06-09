import uuid

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta


class User(AbstractUser):

    is_email_verified = models.BooleanField(default=False)

    email_verification_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
    )

    token_created_at = models.DateTimeField(auto_now_add=True)

    reset_token = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
    )

    reset_token_expires = models.DateTimeField(
        null=True,
        blank=True,
    )

    is_seller = models.BooleanField(default=False)

    bio = models.TextField(blank=True)

    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
    )

    phone_number = models.CharField(
        max_length=20,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def is_token_expired(self):
        return self.token_created_at < timezone.now() - timedelta(hours=24)

    def generate_new_verification_token(self):
        self.email_verification_token = uuid.uuid4()
        self.token_created_at = timezone.now()
        self.save()

    def __str__(self):
        return self.username


class NewsletterSubscriber(models.Model):
    email = models.EmailField(
        unique=True,
        db_index=True,
    )

    subscribed_at = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email

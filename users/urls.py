from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenVerifyView,
)
from . import views
from .views import CustomTokenObtainPairView

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("profile/", views.UserProfileView.as_view(), name="user_profile"),
    path("verify-email/", views.VerifyEmailView.as_view(), name="verify_email"),
    path(
        "resend-verification/",
        views.ResendVerificationEmailView.as_view(),
        name="resend-verification",
    ),
    path(
        "password-reset/",
        views.PasswordResetRequestView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "newsletter/subscribe/",
        views.NewsletterSubscribeView.as_view(),
        name="newsletter_subscribe",
    ),
    path(
        "newsletter/unsubscribe/",
        views.NewsletterUnsubscribeView.as_view(),
        name="newsletter_unsubscribe",
    ),
    path("verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
    path("test/", views.TestAPIView.as_view(), name="test"),
    path("custom-login/", views.CustomLoginView.as_view(), name="custom_login"),
]

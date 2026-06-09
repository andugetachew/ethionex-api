import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import NewsletterSubscriber, User
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    LoginSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
    EmailVerifySerializer,
    ResendVerificationSerializer,
)
from ethionex_api.throttles import LoginRateThrottle, RegisterRateThrottle

from notifications.email_service import EmailService
from .tasks import send_welcome_email_task

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle]

    def perform_create(self, serializer):
        user = serializer.save()

        # Send verification email
        self.send_verification_email(user)

        # Optional Celery welcome email task
        try:
            send_welcome_email_task.delay(user.email, user.username)
        except Exception:
            pass

    def send_verification_email(self, user):
        verification_link = (
            f"{settings.FRONTEND_URL}/verify-email"
            f"?token={user.email_verification_token}"
        )

        subject = "welcome to ethionex - verify your email"

        message = f"""
Hi {user.username},

Thank you for registering with EthioNex!

Please click the link below to verify your email address:

{verification_link}

This link expires in 24 hours.

If you didn't create an account, please ignore this email.

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


class CustomTokenObtainPairView(TokenObtainPairView):
    throttle_classes = [LoginRateThrottle]


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]

        try:
            user = User.objects.get(email_verification_token=token)

            if hasattr(user, "is_token_expired"):
                if user.is_token_expired():
                    return Response(
                        {
                            "error": (
                                "Verification link has expired. " "Request a new one."
                            )
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            elif user.token_created_at:
                if timezone.now() > user.token_created_at + timedelta(days=1):
                    return Response(
                        {"error": "Verification token expired"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            user.is_email_verified = True
            user.email_verification_token = uuid.uuid4()   
            user.save()

            return Response(
                {"message": ("Email verified successfully! " "You can now log in.")},
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {"error": "Invalid verification token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)

            if user.is_email_verified:
                return Response(
                    {"message": "Email already verified"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user.email_verification_token = str(uuid.uuid4())
            user.token_created_at = timezone.now()

            user.save()

            verification_link = (
                f"{settings.FRONTEND_URL}/verify-email"
                f"?token={user.email_verification_token}"
            )

            send_mail(
                "Verify Your Email - EthioNex",
                f"""
Click the link below to verify your email:

{verification_link}

This link expires in 24 hours.
""",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )

            return Response(
                {"message": ("Verification email sent. " "Please check your inbox.")},
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {"error": "No user found with this email"},
                status=status.HTTP_404_NOT_FOUND,
            )


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        try:
            user = User.objects.get(email=email)

            token = str(uuid.uuid4())

            user.reset_token = token
            user.reset_token_expires = timezone.now() + timedelta(hours=24)

            user.save()

            reset_url = f"{settings.FRONTEND_URL}/reset-password" f"?token={token}"

            send_mail(
                "Password Reset - EthioNex",
                f"""
Click the link below to reset your password:

{reset_url}

This link expires in 24 hours.
""",
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )

        except User.DoesNotExist:

            pass

        return Response(
            {
                "message": (
                    "If the email exists, a password reset link " "has been sent."
                )
            },
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data["token"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(
                reset_token=token,
                reset_token_expires__gt=timezone.now(),
            )

            user.set_password(password)

            user.reset_token = ""
            user.reset_token_expires = None

            user.email_verification_token = str(uuid.uuid4())

            user.save()

            return Response(
                {"message": "Password reset successfully"},
                status=status.HTTP_200_OK,
            )

        except User.DoesNotExist:
            return Response(
                {"error": "Invalid or expired reset token"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class NewsletterSubscribeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        subscriber, created = NewsletterSubscriber.objects.get_or_create(
            email=email,
            defaults={"is_active": True},
        )

        if created:
            return Response(
                {"message": "Subscribed successfully"},
                status=status.HTTP_201_CREATED,
            )

        elif not subscriber.is_active:
            subscriber.is_active = True
            subscriber.save()

            return Response(
                {"message": "Re-subscribed successfully"},
                status=status.HTTP_200_OK,
            )

        return Response(
            {"message": "Already subscribed"},
            status=status.HTTP_200_OK,
        )


class NewsletterUnsubscribeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            subscriber = NewsletterSubscriber.objects.get(email=email)

            subscriber.is_active = False
            subscriber.save()

            return Response(
                {"message": "Unsubscribed successfully"},
                status=status.HTTP_200_OK,
            )

        except NewsletterSubscriber.DoesNotExist:
            return Response(
                {"error": "Email not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class TestAPIView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"message": "API is working!"})


class CustomLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from django.contrib.auth import authenticate

        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            )
        return Response({"error": "Invalid credentials"}, status=401)

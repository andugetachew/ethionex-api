# users/serializers.py - COMPLETE MERGED VERSION

from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from .models import User

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """User profile serializer"""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone_number",
            "is_seller",
            "is_email_verified",
            "date_joined",
            "bio",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "date_joined",
            "is_email_verified",
            "created_at",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    """User registration serializer"""

    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
    )

    password2 = serializers.CharField(
        write_only=True,
        required=True,
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "phone_number",
            "password",
            "password2",
            "is_seller",
        ]

    def validate(self, attrs):
        """Validate matching passwords"""

        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )
        if User.objects.filter(email=attrs.get("email", "")).exists():
         raise serializers.ValidationError(
            {"email": "A user with this email already exists."}
        )

        return attrs

    def create(self, validated_data):
        """Create new user"""

        validated_data.pop("password2")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
            phone_number=validated_data.get("phone_number", ""),
            is_seller=validated_data.get("is_seller", False),
        )

        return user


class LoginSerializer(serializers.Serializer):
    """User login serializer"""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get("username")
        password = attrs.get("password")

        user = authenticate(
            username=username,
            password=password,
        )

        if not user:
            raise serializers.ValidationError("Invalid username or password.")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        attrs["user"] = user

        return attrs


class EmailVerifySerializer(serializers.Serializer):
    """Email verification serializer"""

    token = serializers.UUIDField()


class ResendVerificationSerializer(serializers.Serializer):
    """Resend verification email serializer"""

    email = serializers.EmailField()


class PasswordResetRequestSerializer(serializers.Serializer):
    """Password reset request serializer"""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Password reset confirmation serializer"""

    token = serializers.CharField()

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )

    password2 = serializers.CharField(
        write_only=True,
    )

    def validate(self, attrs):
        """Validate matching passwords"""

        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."}
            )

        return attrs

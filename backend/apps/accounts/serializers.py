from django.contrib.auth import password_validation
from rest_framework import serializers

from .models import User


class UserPublicSerializer(serializers.ModelSerializer):
    email_verified = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "public_id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "preferred_locale",
            "email_verified",
            "is_staff",
        )

    def get_email_verified(self, obj: User) -> bool:
        return obj.email_verified_at is not None


class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=254)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)
    accept_terms = serializers.BooleanField()
    accept_privacy = serializers.BooleanField()

    def validate_email(self, value: str) -> str:
        email = User.objects.normalize_email(value).lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Un compte existe déjà pour cette adresse.")
        return email

    def validate_password(self, value: str) -> str:
        password_validation.validate_password(value)
        return value

    def validate(self, attrs):
        if not attrs.get("accept_terms") or not attrs.get("accept_privacy"):
            raise serializers.ValidationError(
                "Les conditions et la politique de confidentialité doivent être acceptées."
            )
        return attrs


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, trim_whitespace=False, max_length=128)


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)


class TokenSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=256, trim_whitespace=False)


class PasswordResetConfirmSerializer(TokenSerializer):
    new_password = serializers.CharField(write_only=True, max_length=128, trim_whitespace=False)


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "phone", "preferred_locale")

    def validate_preferred_locale(self, value: str) -> str:
        if value != "fr":
            raise serializers.ValidationError("Seul le français est disponible au lancement.")
        return value


class CsrfSerializer(serializers.Serializer):
    csrf_token = serializers.CharField()


class MessageSerializer(serializers.Serializer):
    message = serializers.CharField()


class RegistrationResponseSerializer(MessageSerializer):
    verification_email_sent = serializers.BooleanField()


class SessionResponseSerializer(serializers.Serializer):
    user = UserPublicSerializer()

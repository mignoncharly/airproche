import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    username = None
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=32, blank=True)
    preferred_locale = models.CharField(max_length=10, default="fr")
    email_verified_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    objects = UserManager()

    def __str__(self) -> str:
        return self.email


class AccountToken(models.Model):
    class Purpose(models.TextChoices):
        VERIFY_EMAIL = "verify_email", "Verify email"
        RESET_PASSWORD = "reset_password", "Reset password"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="account_tokens")
    purpose = models.CharField(max_length=24, choices=Purpose.choices)
    token_digest = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=("user", "purpose", "consumed_at")),
            models.Index(fields=("expires_at",)),
        ]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.purpose}"


class ConsentRecord(models.Model):
    class ConsentType(models.TextChoices):
        TERMS = "terms", "Terms and conditions"
        PRIVACY = "privacy", "Privacy acknowledgement"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name="consent_records")
    consent_type = models.CharField(max_length=24, choices=ConsentType.choices)
    document_version = models.CharField(max_length=32)
    granted_at = models.DateTimeField(auto_now_add=True)
    withdrawn_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("user", "consent_type", "document_version"),
                name="accounts_user_consent_version_unique",
            )
        ]
        indexes = [models.Index(fields=("user", "consent_type", "granted_at"))]

    def __str__(self) -> str:
        return f"{self.user_id}:{self.consent_type}:{self.document_version}"

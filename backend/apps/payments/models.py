from __future__ import annotations

import uuid

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q

from apps.accounts.models import User
from apps.bookings.models import Booking


currency_validator = RegexValidator(r"^[A-Z]{3}$", "Use a three-letter ISO currency code.")


class Payment(models.Model):
    class Provider(models.TextChoices):
        STRIPE = "stripe", "Stripe"

    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELED = "canceled", "Canceled"
        PARTIALLY_REFUNDED = "partially_refunded", "Partially refunded"
        REFUNDED = "refunded", "Refunded"
        MISMATCHED = "mismatched", "Mismatched"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    booking = models.OneToOneField(Booking, on_delete=models.PROTECT, related_name="payment")
    provider = models.CharField(max_length=16, choices=Provider.choices, default=Provider.STRIPE)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.CREATED)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=(MinValueValidator(0),))
    currency = models.CharField(max_length=3, validators=(currency_validator,))
    environment = models.CharField(max_length=12, default="test")
    checkout_session_id = models.CharField(max_length=255, blank=True, unique=True, null=True)
    payment_intent_id = models.CharField(max_length=255, blank=True, unique=True, null=True)
    charge_id = models.CharField(max_length=255, blank=True, unique=True, null=True)
    last_error_code = models.CharField(max_length=80, blank=True)
    last_error_message = models.CharField(max_length=300, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=("status", "updated_at")), models.Index(fields=("environment", "provider"))]
        constraints = [models.CheckConstraint(condition=Q(amount__gte=0), name="payments_amount_nonnegative")]

    def save(self, *args, **kwargs):
        self.currency = self.currency.upper()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.booking.reference} Â· {self.provider}"


class PaymentAttempt(models.Model):
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"
        CANCELED = "canceled", "Canceled"

    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="attempts")
    attempt_number = models.PositiveSmallIntegerField()
    idempotency_key = models.CharField(max_length=128, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.CREATED)
    provider_request_id = models.CharField(max_length=255, blank=True)
    checkout_session_id = models.CharField(max_length=255, blank=True)
    checkout_url = models.URLField(blank=True)
    failure_code = models.CharField(max_length=80, blank=True)
    failure_message = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("attempt_number",)
        constraints = [models.UniqueConstraint(fields=("payment", "attempt_number"), name="payments_attempt_number_unique")]


class Refund(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    requested_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="payment_refund_requests")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=(MinValueValidator(0),))
    currency = models.CharField(max_length=3, validators=(currency_validator,))
    reason = models.CharField(max_length=300, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    provider_refund_id = models.CharField(max_length=255, blank=True, unique=True, null=True)
    idempotency_key = models.CharField(max_length=128, unique=True)
    failure_code = models.CharField(max_length=80, blank=True)
    failure_message = models.CharField(max_length=300, blank=True)
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=("payment", "status"))]

    def save(self, *args, **kwargs):
        self.currency = self.currency.upper()
        return super().save(*args, **kwargs)


class WebhookEvent(models.Model):
    class Status(models.TextChoices):
        RECEIVED = "received", "Received"
        PROCESSED = "processed", "Processed"
        IGNORED = "ignored", "Ignored"
        FAILED = "failed", "Failed"
        QUARANTINED = "quarantined", "Quarantined"

    provider = models.CharField(max_length=16, default="stripe")
    environment = models.CharField(max_length=12)
    provider_event_id = models.CharField(max_length=255)
    event_type = models.CharField(max_length=120)
    signature_valid = models.BooleanField(default=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.RECEIVED)
    attempts = models.PositiveSmallIntegerField(default=1)
    payload = models.JSONField(default=dict)
    payment = models.ForeignKey(Payment, null=True, blank=True, on_delete=models.SET_NULL, related_name="webhook_events")
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    failure_message = models.CharField(max_length=300, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("provider", "environment", "provider_event_id"), name="payments_webhook_provider_environment_event_unique")]
        indexes = [models.Index(fields=("status", "received_at"))]


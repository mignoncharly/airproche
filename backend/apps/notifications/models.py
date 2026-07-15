import uuid

from django.conf import settings
from django.db import models


class EmailNotification(models.Model):
    class Kind(models.TextChoices):
        VERIFY_EMAIL = "verify_email", "Email verification"
        RESET_PASSWORD = "reset_password", "Password reset"
        BOOKING_CREATED = "booking_created", "Booking created"
        BOOKING_STATUS = "booking_status", "Booking status"
        CONTACT_RECEIVED = "contact_received", "Contact received"
        INQUIRY_CUSTOMER_ACK = "inquiry_customer_ack", "Inquiry customer acknowledgement"
        INQUIRY_DRIVER_NEW = "inquiry_driver_new", "New inquiry for driver"
        INQUIRY_STATUS = "inquiry_status", "Inquiry status update"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"
        RETRYING = "retrying", "Retrying"
        PERMANENT_FAILURE = "permanent_failure", "Permanent failure"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    template_key = models.CharField(max_length=64)
    recipient_email = models.EmailField(max_length=254)
    locale = models.CharField(max_length=10, default="fr")
    context = models.JSONField(default=dict)
    related_type = models.CharField(max_length=32, blank=True)
    related_public_id = models.UUIDField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=160, unique=True)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.PENDING)
    retryable = models.BooleanField(default=True)
    max_attempts = models.PositiveSmallIntegerField(default=4)
    next_attempt_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    provider_identifier = models.CharField(max_length=160, blank=True)
    error_category = models.CharField(max_length=80, blank=True)
    safe_error_summary = models.CharField(max_length=300, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("status", "created_at")),
            models.Index(fields=("related_type", "related_public_id")),
        ]

    def __str__(self):
        return f"{self.kind}:{self.status}:{self.public_id}"


class EmailDeliveryAttempt(models.Model):
    class Status(models.TextChoices):
        SENT = "sent", "Sent"
        FAILED = "failed", "Failed"

    notification = models.ForeignKey(
        EmailNotification, on_delete=models.CASCADE, related_name="attempts"
    )
    attempt_number = models.PositiveIntegerField()
    request_key = models.CharField(max_length=160, unique=True)
    status = models.CharField(max_length=16, choices=Status.choices)
    provider_response = models.CharField(max_length=200, blank=True)
    error_code = models.CharField(max_length=80, blank=True)
    error_message = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-attempt_number",)
        constraints = [
            models.UniqueConstraint(
                fields=("notification", "attempt_number"),
                name="notifications_attempt_number_unique",
            )
        ]

    def __str__(self):
        return f"{self.notification_id}:{self.attempt_number}:{self.status}"


class ContactMessage(models.Model):
    class Topic(models.TextChoices):
        BOOKING = "booking", "Booking"
        QUOTE = "quote", "Quote"
        PAYMENT = "payment", "Payment"
        ACCESSIBILITY = "accessibility", "Accessibility"
        OTHER = "other", "Other"

    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLVED = "resolved", "Resolved"
        SPAM = "spam", "Spam"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=254)
    phone = models.CharField(max_length=32, blank=True)
    topic = models.CharField(max_length=24, choices=Topic.choices)
    message = models.TextField(max_length=4000)
    status = models.CharField(max_length=24, choices=Status.choices, default=Status.NEW)
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_contact_messages",
    )
    staff_notes = models.TextField(max_length=4000, blank=True)
    source_fingerprint = models.CharField(max_length=64, blank=True, editable=False)
    idempotency_key = models.CharField(max_length=160, unique=True, null=True, blank=True)
    request_hash = models.CharField(max_length=64, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("status", "created_at"))]

    def __str__(self):
        return f"{self.topic}:{self.public_id}"

from __future__ import annotations

import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.text import slugify

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.locations.models import Airport, ServiceArea


def inquiry_reference():
    return f"AP-{uuid.uuid4().hex[:10].upper()}"


class Driver(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254, blank=True)
    phone = models.CharField(max_length=32)
    max_passengers = models.PositiveSmallIntegerField(default=8, validators=(MinValueValidator(1),))
    active = models.BooleanField(default=True)
    service_areas = models.ManyToManyField(ServiceArea, blank=True, related_name="drivers")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("last_name", "first_name")
        indexes = [models.Index(fields=("active", "last_name"))]

    @property
    def name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self) -> str:
        return self.name


class MarketplaceDriverProfile(models.Model):
    class VerificationStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        CHANGES_REQUESTED = "changes_requested", "Changes requested"
        VERIFIED = "verified", "Verified"
        SUSPENDED = "suspended", "Suspended"
        REJECTED = "rejected", "Rejected"
        ARCHIVED = "archived", "Archived"

    class ContactMethod(models.TextChoices):
        EMAIL = "email", "Email"
        PHONE = "phone", "Phone"
        WHATSAPP = "whatsapp", "WhatsApp"

    class Direction(models.TextChoices):
        AIRPORT_TO_DESTINATION = "airport_to_destination", "Aéroport vers destination"
        DESTINATION_TO_AIRPORT = "destination_to_airport", "Destination vers aéroport"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    slug = models.SlugField(max_length=220, unique=True, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="driver_profile")
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    display_name = models.CharField(max_length=180)
    business_name = models.CharField(max_length=180, blank=True)
    business_identifier = models.CharField(max_length=80, blank=True)
    professional_status = models.CharField(max_length=120, blank=True)
    vtc_card_number = models.CharField(max_length=80, blank=True)
    vtc_issuing_authority = models.CharField(max_length=180, blank=True)
    vtc_valid_until = models.DateField(null=True, blank=True)
    insurance_provider = models.CharField(max_length=180, blank=True)
    insurance_policy_reference = models.CharField(max_length=120, blank=True)
    insurance_valid_until = models.DateField(null=True, blank=True)
    years_experience = models.PositiveSmallIntegerField(default=0)
    certifications = models.JSONField(default=list, blank=True)
    bio = models.TextField(blank=True, max_length=2000)
    profile_photo = models.FileField(upload_to="marketplace/profile-photos/%Y/%m/", blank=True)
    professional_email = models.EmailField(max_length=254, blank=True)
    phone = models.CharField(max_length=32)
    whatsapp_phone = models.CharField(max_length=32, blank=True)
    preferred_contact_method = models.CharField(
        max_length=16, choices=ContactMethod.choices, default=ContactMethod.EMAIL
    )
    show_phone_publicly = models.BooleanField(default=False)
    show_whatsapp_publicly = models.BooleanField(default=False)
    languages = models.JSONField(default=list, blank=True)
    directions = models.JSONField(default=list, blank=True)
    maximum_radius_km = models.PositiveSmallIntegerField(null=True, blank=True)
    accepted_payment_methods = models.JSONField(default=list, blank=True)
    max_passengers = models.PositiveSmallIntegerField(default=4, validators=(MinValueValidator(1),))
    indicative_price_from = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    indicative_price_currency = models.CharField(max_length=3, default="EUR")
    pricing_note = models.CharField(max_length=500, blank=True)
    minimum_notice_hours = models.PositiveSmallIntegerField(default=12)
    typical_response_minutes = models.PositiveIntegerField(null=True, blank=True)
    availability_note = models.CharField(max_length=500, blank=True)
    cancellation_note = models.CharField(max_length=500, blank=True)
    service_areas = models.ManyToManyField(
        ServiceArea, blank=True, related_name="marketplace_drivers"
    )
    airports = models.ManyToManyField(Airport, blank=True, related_name="marketplace_drivers")
    verification_status = models.CharField(
        max_length=24, choices=VerificationStatus.choices, default=VerificationStatus.DRAFT
    )
    is_published = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    status_reason = models.CharField(max_length=500, blank=True)
    accepts_quote_requests = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_name",)
        indexes = [models.Index(fields=("is_published", "verification_status"))]

    def __str__(self) -> str:
        return self.display_name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.display_name or self.business_name)[:180] or "chauffeur"
            candidate = base
            if MarketplaceDriverProfile.objects.filter(slug=candidate).exclude(pk=self.pk).exists():
                candidate = f"{base}-{self.public_id.hex[:8]}"
            self.slug = candidate
        super().save(*args, **kwargs)


class DriverInquiry(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        NOTIFIED = "notified", "Notified"
        VIEWED = "viewed", "Viewed"
        CONTACTED = "contacted", "Contacted"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        CLOSED = "closed", "Closed"
        ARCHIVED = "archived", "Archived"
        SPAM = "spam", "Spam"

    class Direction(models.TextChoices):
        AIRPORT_TO_DESTINATION = "airport_to_destination", "Airport to destination"
        DESTINATION_TO_AIRPORT = "destination_to_airport", "Destination to airport"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reference = models.CharField(
        max_length=24, unique=True, editable=False, default=inquiry_reference
    )
    driver = models.ForeignKey(
        MarketplaceDriverProfile, on_delete=models.PROTECT, related_name="inquiries"
    )
    airport = models.ForeignKey(Airport, null=True, blank=True, on_delete=models.PROTECT)
    customer_name = models.CharField(max_length=180)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=32)
    customer_whatsapp = models.CharField(max_length=32, blank=True)
    preferred_contact_method = models.CharField(
        max_length=16,
        choices=MarketplaceDriverProfile.ContactMethod.choices,
        default=MarketplaceDriverProfile.ContactMethod.EMAIL,
    )
    whatsapp_consent = models.BooleanField(default=False)
    direction = models.CharField(
        max_length=32, choices=Direction.choices, default=Direction.AIRPORT_TO_DESTINATION
    )
    destination = models.CharField(max_length=300)
    pickup_at = models.DateTimeField(null=True, blank=True)
    passenger_count = models.PositiveSmallIntegerField(
        default=1, validators=(MinValueValidator(1),)
    )
    luggage_count = models.PositiveSmallIntegerField(default=0)
    message = models.TextField(blank=True, max_length=2000)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)
    idempotency_key = models.CharField(max_length=128, blank=True, default="")
    request_hash = models.CharField(max_length=64, blank=True, editable=False)
    source_fingerprint = models.CharField(max_length=64, blank=True, editable=False)
    spam_score = models.PositiveSmallIntegerField(default=0)
    anonymized_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("driver", "status", "created_at"))]
        constraints = [
            models.UniqueConstraint(
                fields=("driver", "idempotency_key"),
                condition=~models.Q(idempotency_key=""),
                name="operations_driver_inquiry_idempotency_unique",
            )
        ]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"AP-{self.public_id.hex[:10].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.reference


class MarketplaceVehicle(models.Model):
    class Category(models.TextChoices):
        SEDAN = "sedan", "Berline"
        VAN = "van", "Van"
        PREMIUM = "premium", "Premium"
        ACCESSIBLE = "accessible", "Accessible"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    profile = models.OneToOneField(
        MarketplaceDriverProfile, on_delete=models.CASCADE, related_name="marketplace_vehicle"
    )
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    category = models.CharField(max_length=24, choices=Category.choices, default=Category.SEDAN)
    color = models.CharField(max_length=60, blank=True)
    passenger_capacity = models.PositiveSmallIntegerField(
        default=4, validators=(MinValueValidator(1),)
    )
    luggage_capacity = models.PositiveSmallIntegerField(default=2)
    registration = models.CharField(max_length=32, blank=True)
    public_photo = models.FileField(upload_to="marketplace/vehicle-photos/%Y/%m/", blank=True)
    air_conditioning = models.BooleanField(default=True)
    child_seat = models.BooleanField(default=False)
    wheelchair_accessible = models.BooleanField(default=False)
    pets_allowed = models.BooleanField(default=False)
    non_smoking = models.BooleanField(default=True)
    amenities = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.make} {self.model} — {self.profile.display_name}"


class InquiryConsent(models.Model):
    inquiry = models.OneToOneField(DriverInquiry, on_delete=models.CASCADE, related_name="consent")
    privacy_policy_version = models.CharField(max_length=80)
    consent_text_version = models.CharField(max_length=80)
    consent_granted = models.BooleanField()
    source = models.CharField(max_length=80, default="driver_profile")
    allowed_contact_channels = models.JSONField(default=list)
    granted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.inquiry.reference}:{self.privacy_policy_version}"


class InquiryStatusHistory(models.Model):
    inquiry = models.ForeignKey(
        DriverInquiry, on_delete=models.CASCADE, related_name="status_history"
    )
    from_status = models.CharField(max_length=16, blank=True)
    to_status = models.CharField(max_length=16, choices=DriverInquiry.Status.choices)
    changed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=500, blank=True)
    customer_visible_note = models.CharField(max_length=500, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("changed_at", "id")

    def __str__(self):
        return f"{self.inquiry.reference}:{self.to_status}"


class InquiryNote(models.Model):
    inquiry = models.ForeignKey(DriverInquiry, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    body = models.TextField(max_length=2000)
    customer_visible = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.inquiry.reference}:{self.created_at}"


def private_document_path(instance, filename):
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    return f"private/driver-documents/{instance.profile.public_id}/{uuid.uuid4().hex}.{extension}"


class DriverVerificationDocument(models.Model):
    class DocumentType(models.TextChoices):
        IDENTITY = "identity", "Justificatif d’identité"
        VTC_CARD = "vtc_card", "Carte professionnelle VTC"
        INSURANCE = "insurance", "Attestation d’assurance"
        BUSINESS = "business", "Immatriculation professionnelle"
        VEHICLE = "vehicle", "Carte grise"
        OTHER = "other", "Autre"

    class ReviewStatus(models.TextChoices):
        PENDING_SCAN = "pending_scan", "Analyse en attente"
        PENDING_REVIEW = "pending_review", "Examen en attente"
        APPROVED = "approved", "Approuvé"
        REJECTED = "rejected", "Refusé"
        EXPIRED = "expired", "Expiré"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    profile = models.ForeignKey(
        MarketplaceDriverProfile, on_delete=models.CASCADE, related_name="verification_documents"
    )
    document_type = models.CharField(max_length=24, choices=DocumentType.choices)
    file = models.FileField(upload_to=private_document_path)
    original_name = models.CharField(max_length=255)
    mime_type = models.CharField(max_length=100)
    size_bytes = models.PositiveIntegerField()
    expires_on = models.DateField(null=True, blank=True)
    review_status = models.CharField(
        max_length=24, choices=ReviewStatus.choices, default=ReviewStatus.PENDING_SCAN
    )
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_note = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.display_name}:{self.document_type}"


class DriverVerificationEvent(models.Model):
    profile = models.ForeignKey(
        MarketplaceDriverProfile, on_delete=models.CASCADE, related_name="verification_events"
    )
    actor = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    action = models.CharField(max_length=40)
    reason = models.CharField(max_length=500, blank=True)
    safe_metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.profile.display_name}:{self.action}"


class Vehicle(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    registration = models.CharField(max_length=32, unique=True)
    label = models.CharField(max_length=120)
    seats = models.PositiveSmallIntegerField(default=4, validators=(MinValueValidator(1),))
    luggage_capacity = models.PositiveSmallIntegerField(default=4)
    accessibility_capable = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("label", "registration")
        indexes = [models.Index(fields=("active", "label"))]

    def __str__(self) -> str:
        return f"{self.label} ({self.registration})"


class DriverAssignment(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    booking = models.ForeignKey(
        Booking, on_delete=models.PROTECT, related_name="driver_assignments"
    )
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name="assignments")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="driver_assignments_made",
    )
    unassigned_at = models.DateTimeField(null=True, blank=True)
    unassigned_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="driver_assignments_removed",
    )
    released_to_customer_at = models.DateTimeField(null=True, blank=True)
    override_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ("-assigned_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("booking",),
                condition=models.Q(unassigned_at__isnull=True),
                name="operations_one_active_assignment_per_booking",
            )
        ]
        indexes = [
            models.Index(fields=("driver", "unassigned_at")),
            models.Index(fields=("vehicle", "unassigned_at")),
        ]

    @property
    def active(self) -> bool:
        return self.unassigned_at is None

    def __str__(self) -> str:
        return f"{self.booking.reference} - {self.driver.name}"


class AuditEvent(models.Model):
    actor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="operations_audit_events",
    )
    action = models.CharField(max_length=80)
    content_type = models.ForeignKey(ContentType, on_delete=models.PROTECT)
    object_id = models.CharField(max_length=80)
    content_object = GenericForeignKey("content_type", "object_id")
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    reason = models.CharField(max_length=500, blank=True)
    correlation_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("action", "created_at")),
            models.Index(fields=("content_type", "object_id")),
        ]

    def __str__(self) -> str:
        return f"{self.action}:{self.object_id}"

from __future__ import annotations

import uuid

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.db import models

from apps.accounts.models import User
from apps.bookings.models import Booking
from apps.locations.models import Airport, ServiceArea


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
        PENDING = "pending", "Pending review"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="driver_profile")
    display_name = models.CharField(max_length=180)
    business_name = models.CharField(max_length=180, blank=True)
    business_identifier = models.CharField(max_length=80, blank=True)
    vtc_card_number = models.CharField(max_length=80, blank=True)
    insurance_provider = models.CharField(max_length=180, blank=True)
    bio = models.TextField(blank=True, max_length=2000)
    phone = models.CharField(max_length=32)
    accepted_payment_methods = models.JSONField(default=list, blank=True)
    max_passengers = models.PositiveSmallIntegerField(default=4, validators=(MinValueValidator(1),))
    service_areas = models.ManyToManyField(ServiceArea, blank=True, related_name="marketplace_drivers")
    airports = models.ManyToManyField(Airport, blank=True, related_name="marketplace_drivers")
    verification_status = models.CharField(max_length=16, choices=VerificationStatus.choices, default=VerificationStatus.DRAFT)
    is_published = models.BooleanField(default=False)
    accepts_quote_requests = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_name",)
        indexes = [models.Index(fields=("is_published", "verification_status"))]

    def __str__(self) -> str:
        return self.display_name


class DriverInquiry(models.Model):
    class Status(models.TextChoices):
        NEW = "new", "New"
        CONTACTED = "contacted", "Contacted"
        CLOSED = "closed", "Closed"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    driver = models.ForeignKey(MarketplaceDriverProfile, on_delete=models.PROTECT, related_name="inquiries")
    airport = models.ForeignKey(Airport, null=True, blank=True, on_delete=models.PROTECT)
    customer_name = models.CharField(max_length=180)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=32)
    destination = models.CharField(max_length=300)
    pickup_at = models.DateTimeField(null=True, blank=True)
    passenger_count = models.PositiveSmallIntegerField(default=1, validators=(MinValueValidator(1),))
    message = models.TextField(blank=True, max_length=2000)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("driver", "status", "created_at"))]



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
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, related_name="driver_assignments")
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name="assignments")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.PROTECT, related_name="assignments")
    assigned_at = models.DateTimeField(auto_now_add=True)
    assigned_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="driver_assignments_made")
    unassigned_at = models.DateTimeField(null=True, blank=True)
    unassigned_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="driver_assignments_removed")
    released_to_customer_at = models.DateTimeField(null=True, blank=True)
    override_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ("-assigned_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("booking",), condition=models.Q(unassigned_at__isnull=True), name="operations_one_active_assignment_per_booking"
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
    actor = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="operations_audit_events")
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
        indexes = [models.Index(fields=("action", "created_at")), models.Index(fields=("content_type", "object_id"))]

    def __str__(self) -> str:
        return f"{self.action}:{self.object_id}"


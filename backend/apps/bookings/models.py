from __future__ import annotations

import secrets
import uuid

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q

from apps.accounts.models import User
from apps.locations.models import Airport, ServiceArea
from apps.pricing.models import Quote


currency_validator = RegexValidator(r"^[A-Z]{3}$", "Use a three-letter ISO currency code.")


class Booking(models.Model):
    class Type(models.TextChoices):
        AIRPORT_PICKUP = "airport_pickup", "Airport pickup"
        AIRPORT_DROPOFF = "airport_dropoff", "Airport drop-off"
        POINT_TO_POINT = "point_to_point", "Point to point"

    class Source(models.TextChoices):
        GUEST = "guest", "Guest"
        ACCOUNT = "account", "Account"
        STAFF = "staff", "Staff"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        CONFIRMED = "confirmed", "Confirmed"
        DRIVER_ASSIGNMENT_PENDING = "driver_assignment_pending", "Driver assignment pending"
        DRIVER_ASSIGNED = "driver_assigned", "Driver assigned"
        PASSENGER_CONTACTED = "passenger_contacted", "Passenger contacted"
        DRIVER_EN_ROUTE = "driver_en_route", "Driver en route"
        DRIVER_ARRIVED = "driver_arrived", "Driver arrived"
        PASSENGER_PICKED_UP = "passenger_picked_up", "Passenger picked up"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No show"

    class PaymentMode(models.TextChoices):
        ONLINE_FULL = "online_full", "Online in full"
        PAY_LATER = "pay_later", "Pay later"
        DEPOSIT = "deposit", "Deposit"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    reference = models.CharField(max_length=24, unique=True, editable=False)
    quote = models.ForeignKey(Quote, on_delete=models.PROTECT, related_name="bookings")
    customer = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="bookings"
    )
    source = models.CharField(max_length=12, choices=Source.choices, default=Source.GUEST)
    booking_type = models.CharField(max_length=24, choices=Type.choices)
    airport = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name="bookings")
    service_area = models.ForeignKey(
        ServiceArea, on_delete=models.PROTECT, related_name="bookings"
    )

    pickup_address = models.CharField(max_length=300, blank=True)
    destination_address = models.CharField(max_length=300, blank=True)
    pickup_locality = models.CharField(max_length=120, blank=True)
    destination_locality = models.CharField(max_length=120, blank=True)
    pickup_at = models.DateTimeField()
    scheduled_arrival_at = models.DateTimeField(null=True, blank=True)
    flight_number = models.CharField(max_length=32, blank=True)
    airline = models.CharField(max_length=120, blank=True)
    origin_city_country = models.CharField(max_length=160, blank=True)
    terminal = models.CharField(max_length=80, blank=True)
    meeting_information = models.CharField(max_length=500, blank=True)

    passenger_count = models.PositiveSmallIntegerField(validators=(MinValueValidator(1),))
    adult_count = models.PositiveSmallIntegerField(default=1)
    child_count = models.PositiveSmallIntegerField(default=0)
    luggage_count = models.PositiveSmallIntegerField(default=0)
    oversized_luggage_count = models.PositiveSmallIntegerField(default=0)
    child_seat_quantity = models.PositiveSmallIntegerField(default=0)
    accessibility_request = models.BooleanField(default=False)
    accessibility_details = models.CharField(max_length=500, blank=True)
    additional_requirements = models.TextField(blank=True)
    passenger_same_as_booker = models.BooleanField(default=True)

    booker_first_name = models.CharField(max_length=150)
    booker_last_name = models.CharField(max_length=150)
    booker_email = models.EmailField(max_length=254)
    booker_phone = models.CharField(max_length=32)
    booker_whatsapp = models.CharField(max_length=32, blank=True)
    passenger_first_name = models.CharField(max_length=150)
    passenger_last_name = models.CharField(max_length=150)
    passenger_phone = models.CharField(max_length=32, blank=True)
    passenger_whatsapp = models.CharField(max_length=32, blank=True)
    passenger_locale = models.CharField(max_length=10, default="fr")
    locale = models.CharField(max_length=10, default="fr")

    status = models.CharField(max_length=32, choices=Status.choices, default=Status.DRAFT)
    payment_mode = models.CharField(
        max_length=16, choices=PaymentMode.choices, default=PaymentMode.ONLINE_FULL
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, validators=(currency_validator,))
    cancellation_deadline = models.DateTimeField(null=True, blank=True)
    cancellation_outcome = models.CharField(max_length=32, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.CharField(max_length=300, blank=True)
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    privacy_accepted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("status", "pickup_at")),
            models.Index(fields=("customer", "status", "pickup_at")),
            models.Index(fields=("booker_email", "created_at")),
            models.Index(fields=("airport", "pickup_at")),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(passenger_count__gte=1), name="bookings_passenger_count_positive"
            ),
            models.CheckConstraint(
                condition=Q(currency__regex=r"^[A-Z]{3}$"), name="bookings_currency_iso"
            ),
            models.CheckConstraint(
                condition=Q(total_amount__gte=0), name="bookings_total_nonnegative"
            ),
        ]

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"TR-{uuid.uuid4().hex[:10].upper()}"
        self.currency = self.currency.upper()
        self.booker_email = self.booker_email.lower()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.reference


class AddressSnapshot(models.Model):
    class Kind(models.TextChoices):
        PICKUP = "pickup", "Pickup"
        DESTINATION = "destination", "Destination"

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="address_snapshots")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    formatted_address = models.CharField(max_length=300)
    locality = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country_code = models.CharField(max_length=2, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    provider_place_id = models.CharField(max_length=160, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("booking", "kind"), name="bookings_address_kind_unique")
        ]


class ContactSnapshot(models.Model):
    class Kind(models.TextChoices):
        BOOKER = "booker", "Booker"
        PASSENGER = "passenger", "Passenger"

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="contact_snapshots")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.EmailField(max_length=254, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    whatsapp = models.CharField(max_length=32, blank=True)
    preferred_locale = models.CharField(max_length=10, default="fr")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("booking", "kind"), name="bookings_contact_kind_unique")
        ]


class PriceSnapshot(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="price_snapshot")
    calculation_version = models.CharField(max_length=32)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, validators=(currency_validator,))
    created_at = models.DateTimeField(auto_now_add=True)


class PriceLine(models.Model):
    snapshot = models.ForeignKey(PriceSnapshot, on_delete=models.CASCADE, related_name="lines")
    code = models.SlugField(max_length=80)
    label = models.CharField(max_length=180)
    quantity = models.PositiveSmallIntegerField()
    unit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "id")
        constraints = [
            models.UniqueConstraint(fields=("snapshot", "code"), name="bookings_price_line_code_unique")
        ]


class CancellationPolicySnapshot(models.Model):
    booking = models.OneToOneField(
        Booking, on_delete=models.CASCADE, related_name="cancellation_policy_snapshot"
    )
    version = models.CharField(max_length=32)
    text = models.TextField()
    deadline = models.DateTimeField(null=True, blank=True)
    captured_at = models.DateTimeField(auto_now_add=True)


class BookingStatusHistory(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=32, blank=True)
    to_status = models.CharField(max_length=32, choices=Booking.Status.choices)
    actor = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="booking_status_changes"
    )
    note = models.CharField(max_length=500, blank=True)
    correlation_id = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")


class BookingNote(models.Model):
    class Visibility(models.TextChoices):
        INTERNAL = "internal", "Internal"
        CUSTOMER = "customer", "Customer visible"

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="notes")
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    visibility = models.CharField(max_length=16, choices=Visibility.choices)
    body = models.TextField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")


class GuestAccessToken(models.Model):
    class Purpose(models.TextChoices):
        MANAGE = "manage", "Manage booking"

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="guest_tokens")
    purpose = models.CharField(max_length=16, choices=Purpose.choices, default=Purpose.MANAGE)
    token_digest = models.CharField(max_length=64, unique=True, editable=False)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    failed_attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=("booking", "purpose", "revoked_at"))]


class IdempotencyRecord(models.Model):
    scope = models.CharField(max_length=80)
    key = models.CharField(max_length=128)
    request_hash = models.CharField(max_length=64)
    booking = models.ForeignKey(
        Booking, null=True, blank=True, on_delete=models.SET_NULL, related_name="idempotency_records"
    )
    response_status = models.PositiveSmallIntegerField(default=201)
    response_payload = models.JSONField(default=dict)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("scope", "key"), name="bookings_idempotency_scope_key_unique")
        ]


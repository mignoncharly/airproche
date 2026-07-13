from __future__ import annotations

import uuid
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import F, Q

from apps.locations.models import Airport, ServiceArea


class TripType(models.TextChoices):
    AIRPORT_PICKUP = "airport_pickup", "Airport pickup"
    AIRPORT_DROPOFF = "airport_dropoff", "Airport drop-off"


currency_validator = RegexValidator(r"^[A-Z]{3}$", "Use a three-letter ISO currency code.")


class Tariff(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    airport = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name="tariffs")
    service_area = models.ForeignKey(ServiceArea, on_delete=models.PROTECT, related_name="tariffs")
    trip_type = models.CharField(max_length=24, choices=TripType.choices)
    base_amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=(MinValueValidator(Decimal("0")),)
    )
    currency = models.CharField(max_length=3, default="EUR", validators=(currency_validator,))
    passenger_capacity = models.PositiveSmallIntegerField(default=4)
    luggage_capacity = models.PositiveSmallIntegerField(default=4)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    priority = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-priority", "-valid_from")
        constraints = [
            models.CheckConstraint(
                condition=Q(valid_until__isnull=True) | Q(valid_until__gt=F("valid_from")),
                name="pricing_tariff_valid_window",
            ),
            models.CheckConstraint(
                condition=Q(passenger_capacity__gte=1),
                name="pricing_tariff_passenger_capacity_positive",
            ),
            models.CheckConstraint(
                condition=Q(luggage_capacity__gte=0),
                name="pricing_tariff_luggage_capacity_nonnegative",
            ),
            models.UniqueConstraint(
                fields=("airport", "service_area", "trip_type", "valid_from"),
                name="pricing_tariff_route_start_unique",
            ),
        ]
        indexes = [
            models.Index(fields=("airport", "service_area", "trip_type", "is_active", "valid_from"))
        ]

    def __str__(self) -> str:
        return f"{self.airport.iata_code} · {self.service_area} · {self.get_trip_type_display()}"

    def save(self, *args, **kwargs):
        self.currency = self.currency.upper()
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.valid_until and self.valid_until <= self.valid_from:
            raise ValidationError({"valid_until": "The end must be after the start."})
        if not self.is_active or not self.airport_id or not self.service_area_id:
            return
        overlapping = Tariff.objects.filter(
            airport_id=self.airport_id,
            service_area_id=self.service_area_id,
            trip_type=self.trip_type,
            is_active=True,
        ).exclude(pk=self.pk)
        overlapping = overlapping.filter(
            Q(valid_until__isnull=True) | Q(valid_until__gt=self.valid_from)
        )
        if self.valid_until:
            overlapping = overlapping.filter(valid_from__lt=self.valid_until)
        if overlapping.exists():
            raise ValidationError("An active tariff already covers part of this validity window.")


class TariffOption(models.Model):
    class PricingMethod(models.TextChoices):
        FIXED = "fixed", "Fixed"
        PER_UNIT = "per_unit", "Per unit"

    code = models.SlugField(max_length=80)
    label = models.CharField(max_length=140)
    tariff = models.ForeignKey(
        Tariff, on_delete=models.CASCADE, related_name="options", null=True, blank=True
    )
    pricing_method = models.CharField(
        max_length=16, choices=PricingMethod.choices, default=PricingMethod.PER_UNIT
    )
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=(MinValueValidator(Decimal("0")),)
    )
    currency = models.CharField(max_length=3, default="EUR", validators=(currency_validator,))
    maximum_quantity = models.PositiveSmallIntegerField(default=1)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("display_order", "code")
        constraints = [
            models.CheckConstraint(
                condition=Q(valid_until__isnull=True) | Q(valid_until__gt=F("valid_from")),
                name="pricing_option_valid_window",
            ),
            models.CheckConstraint(
                condition=Q(maximum_quantity__gte=1),
                name="pricing_option_quantity_positive",
            ),
            models.UniqueConstraint(
                fields=("code", "tariff", "valid_from"),
                name="pricing_option_code_tariff_start_unique",
            ),
        ]
        indexes = [models.Index(fields=("code", "is_active", "valid_from"))]

    def __str__(self) -> str:
        return self.label

    def save(self, *args, **kwargs):
        self.currency = self.currency.upper()
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.valid_until and self.valid_until <= self.valid_from:
            raise ValidationError({"valid_until": "The end must be after the start."})
        if self.tariff_id and self.currency != self.tariff.currency:
            raise ValidationError({"currency": "The option and tariff currencies must match."})


class Quote(models.Model):
    class Status(models.TextChoices):
        VALID = "valid", "Valid"
        EXPIRED = "expired", "Expired"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    tariff = models.ForeignKey(Tariff, on_delete=models.PROTECT, related_name="quotes")
    trip_type = models.CharField(max_length=24, choices=TripType.choices)
    airport = models.ForeignKey(Airport, on_delete=models.PROTECT, related_name="quotes")
    service_area = models.ForeignKey(ServiceArea, on_delete=models.PROTECT, related_name="quotes")
    airport_name = models.CharField(max_length=180)
    airport_iata_code = models.CharField(max_length=3)
    service_area_name = models.CharField(max_length=160)
    pickup_at = models.DateTimeField()
    passenger_count = models.PositiveSmallIntegerField()
    luggage_count = models.PositiveSmallIntegerField()
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, validators=(currency_validator,))
    calculation_version = models.CharField(max_length=32, default="fixed-zone-v1")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.VALID)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [models.Index(fields=("public_id", "expires_at"))]
        constraints = [
            models.CheckConstraint(
                condition=Q(passenger_count__gte=1), name="pricing_quote_passengers_positive"
            ),
            models.CheckConstraint(
                condition=Q(luggage_count__gte=0), name="pricing_quote_luggage_nonnegative"
            ),
            models.CheckConstraint(
                condition=Q(total_amount__gte=0), name="pricing_quote_total_nonnegative"
            ),
        ]

    def __str__(self) -> str:
        return str(self.public_id)


class QuoteLine(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="lines")
    code = models.SlugField(max_length=80)
    label = models.CharField(max_length=180)
    quantity = models.PositiveSmallIntegerField()
    unit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "id")
        constraints = [
            models.UniqueConstraint(
                fields=("quote", "code"), name="pricing_quote_line_code_unique"
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=1), name="pricing_quote_line_quantity_positive"
            ),
            models.CheckConstraint(
                condition=Q(unit_amount__gte=0), name="pricing_quote_line_unit_nonnegative"
            ),
            models.CheckConstraint(
                condition=Q(total_amount__gte=0), name="pricing_quote_line_total_nonnegative"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.quote_id}:{self.code}"

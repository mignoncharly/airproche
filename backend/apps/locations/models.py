from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models

from apps.core.models import TimeStampedPublicModel


def validate_string_list(value):
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise ValidationError("Expected a list of non-empty strings.")


class Airport(TimeStampedPublicModel):
    iata_validator = RegexValidator(r"^[A-Za-z]{3}$", "Use a three-letter IATA code.")

    name = models.CharField(max_length=180)
    iata_code = models.CharField(max_length=3, unique=True, validators=(iata_validator,))
    slug = models.SlugField(max_length=140, unique=True)
    city = models.CharField(max_length=120)
    country_code = models.CharField(max_length=2, default="FR")
    address = models.CharField(max_length=300)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=(MinValueValidator(Decimal("-90")), MaxValueValidator(Decimal("90"))),
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=(MinValueValidator(Decimal("-180")), MaxValueValidator(Decimal("180"))),
    )
    timezone = models.CharField(max_length=64, default="Europe/Paris")
    terminal_guidance = models.TextField(blank=True)
    description = models.TextField(blank=True)
    seo_title = models.CharField(max_length=70, blank=True)
    seo_description = models.CharField(max_length=170, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "name")

    def save(self, *args, **kwargs):
        self.iata_code = self.iata_code.upper()
        self.country_code = self.country_code.upper()
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"{self.name} ({self.iata_code})"


class ServiceArea(TimeStampedPublicModel):
    class AreaType(models.TextChoices):
        CITY = "city", "City"
        REGION = "region", "Region"
        POSTAL_ZONE = "postal_zone", "Postal zone"
        CUSTOM = "custom", "Custom area"

    name = models.CharField(max_length=160)
    slug = models.SlugField(max_length=140, unique=True)
    area_type = models.CharField(max_length=20, choices=AreaType.choices)
    country_code = models.CharField(max_length=2, default="FR")
    region = models.CharField(max_length=120, blank=True)
    city = models.CharField(max_length=120, blank=True)
    postal_codes = models.JSONField(default=list, blank=True, validators=(validate_string_list,))
    provider_place_id = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "name")

    def save(self, *args, **kwargs):
        self.country_code = self.country_code.upper()
        self.postal_codes = sorted({code.strip() for code in self.postal_codes})
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name

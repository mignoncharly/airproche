from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.core.models import TimeStampedPublicModel


class BusinessSettings(TimeStampedPublicModel):
    business_name = models.CharField(max_length=160, default="Transfert Privé")
    legal_name = models.CharField(max_length=200, blank=True)
    tagline = models.CharField(
        max_length=200,
        default="Votre transfert aéroport, organisé avec soin.",
    )
    phone = models.CharField(max_length=32, blank=True)
    whatsapp_phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    support_hours = models.CharField(max_length=160, blank=True)
    address = models.CharField(max_length=300, blank=True)
    city = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country_code = models.CharField(max_length=2, default="FR")
    currency = models.CharField(max_length=3, default="EUR")
    minimum_lead_hours = models.PositiveSmallIntegerField(default=12)
    maximum_booking_days = models.PositiveSmallIntegerField(default=365)
    quote_valid_minutes = models.PositiveSmallIntegerField(default=30)
    cancellation_deadline_hours = models.PositiveSmallIntegerField(default=24)
    booking_enabled = models.BooleanField(default=False)

    class Meta:
        verbose_name = "business settings"
        verbose_name_plural = "business settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        return super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> BusinessSettings:
        instance, _ = cls.objects.get_or_create(pk=1)
        return instance

    def __str__(self) -> str:
        return self.business_name


class ServiceContent(TimeStampedPublicModel):
    class Icon(models.TextChoices):
        PLANE = "plane", "Airport transfer"
        LUGGAGE = "luggage", "Luggage assistance"
        HOME = "home", "Home transfer"
        HOTEL = "hotel", "Hotel transfer"
        USERS = "users", "Relatives and groups"
        ROUTE = "route", "Long-distance transfer"

    slug = models.SlugField(max_length=120, unique=True)
    title = models.CharField(max_length=160)
    summary = models.CharField(max_length=260)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=20, choices=Icon.choices, default=Icon.ROUTE)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "title")

    def __str__(self) -> str:
        return self.title


class FAQ(TimeStampedPublicModel):
    question = models.CharField(max_length=260)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "question")

    def __str__(self) -> str:
        return self.question


class Testimonial(TimeStampedPublicModel):
    author_name = models.CharField(max_length=120)
    author_context = models.CharField(max_length=160, blank=True)
    quote = models.TextField(max_length=1000)
    rating = models.PositiveSmallIntegerField(
        validators=(MinValueValidator(1), MaxValueValidator(5))
    )
    source_reference = models.CharField(
        max_length=300,
        help_text="Internal source or consent reference. Never exposed publicly.",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    display_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("display_order", "-verified_at")

    def clean(self):
        super().clean()
        if self.is_active and not self.verified_at:
            raise ValidationError(
                {"is_active": "A testimonial must be verified before publication."}
            )

    def __str__(self) -> str:
        return self.author_name


class LegalDocument(TimeStampedPublicModel):
    class Kind(models.TextChoices):
        PRIVACY = "privacy", "Privacy policy"
        TERMS = "terms", "Terms and conditions"
        CANCELLATION = "cancellation", "Cancellation policy"
        LEGAL_NOTICE = "legal_notice", "Legal notice"
        COOKIES = "cookies", "Cookie policy"
        TRANSPARENCY = "transparency", "Platform transparency"

    kind = models.CharField(max_length=24, choices=Kind.choices)
    version = models.CharField(max_length=32)
    title = models.CharField(max_length=200)
    body = models.TextField()
    effective_at = models.DateTimeField()
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ("kind", "-effective_at")
        constraints = [
            models.UniqueConstraint(
                fields=("kind", "version"), name="content_legal_kind_version_unique"
            )
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()} — {self.version}"

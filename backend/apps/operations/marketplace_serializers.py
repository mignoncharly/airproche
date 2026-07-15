import re
import time

from django.db import models
from django.utils import timezone
from rest_framework import serializers

from apps.content.models import LegalDocument
from apps.locations.models import Airport, ServiceArea
from apps.locations.serializers import AirportListSerializer, ServiceAreaListSerializer
from apps.notifications.models import EmailNotification

from .models import (
    DriverInquiry,
    InquiryNote,
    InquiryStatusHistory,
    MarketplaceDriverProfile,
    MarketplaceVehicle,
)

PAYMENT_METHODS = ("cash", "card_terminal", "bank_transfer", "private_payment_link")
LANGUAGES = ("fr", "en", "de", "es", "it", "pt", "ar")
CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
STATUS_LABELS = {
    "new": "Nouvelle",
    "notified": "Chauffeur informé",
    "viewed": "Consultée",
    "contacted": "Client contacté",
    "accepted": "Acceptée par le chauffeur",
    "declined": "Refusée",
    "closed": "Clôturée",
    "archived": "Archivée",
    "spam": "Indésirable",
}


class MarketplaceVehicleSerializer(serializers.ModelSerializer):
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = MarketplaceVehicle
        fields = (
            "make",
            "model",
            "year",
            "category",
            "color",
            "passenger_capacity",
            "luggage_capacity",
            "photo_url",
            "air_conditioning",
            "child_seat",
            "wheelchair_accessible",
            "pets_allowed",
            "non_smoking",
            "amenities",
        )

    def get_photo_url(self, obj):
        return obj.public_photo.url if obj.public_photo else ""


class DriverDirectorySerializer(serializers.ModelSerializer):
    airports = AirportListSerializer(many=True, read_only=True)
    service_areas = ServiceAreaListSerializer(many=True, read_only=True)
    vehicle = serializers.SerializerMethodField()
    profile_photo_url = serializers.SerializerMethodField()
    public_phone = serializers.SerializerMethodField()
    public_whatsapp = serializers.SerializerMethodField()

    class Meta:
        model = MarketplaceDriverProfile
        fields = (
            "public_id",
            "slug",
            "display_name",
            "business_name",
            "bio",
            "profile_photo_url",
            "years_experience",
            "languages",
            "directions",
            "max_passengers",
            "accepted_payment_methods",
            "airports",
            "service_areas",
            "vehicle",
            "indicative_price_from",
            "indicative_price_currency",
            "pricing_note",
            "minimum_notice_hours",
            "typical_response_minutes",
            "availability_note",
            "accepts_quote_requests",
            "public_phone",
            "public_whatsapp",
            "verified_at",
        )

    def get_vehicle(self, obj):
        vehicle = getattr(obj, "marketplace_vehicle", None)
        return MarketplaceVehicleSerializer(vehicle).data if vehicle else None

    def get_profile_photo_url(self, obj):
        return obj.profile_photo.url if obj.profile_photo else ""

    def get_public_phone(self, obj):
        return obj.phone if obj.show_phone_publicly else ""

    def get_public_whatsapp(self, obj):
        return obj.whatsapp_phone if obj.show_whatsapp_publicly else ""


class DriverProfileSerializer(serializers.ModelSerializer):
    accepted_payment_methods = serializers.ListField(
        child=serializers.ChoiceField(choices=PAYMENT_METHODS), required=False, allow_empty=True
    )
    languages = serializers.ListField(
        child=serializers.ChoiceField(choices=LANGUAGES), required=False, allow_empty=True
    )
    directions = serializers.ListField(
        child=serializers.ChoiceField(choices=MarketplaceDriverProfile.Direction.choices),
        required=False,
        allow_empty=True,
    )
    airport_ids = serializers.SlugRelatedField(
        source="airports",
        slug_field="public_id",
        queryset=Airport.objects.filter(is_active=True),
        many=True,
        required=False,
    )
    service_area_ids = serializers.SlugRelatedField(
        source="service_areas",
        slug_field="public_id",
        queryset=ServiceArea.objects.filter(is_active=True),
        many=True,
        required=False,
    )
    vehicle = MarketplaceVehicleSerializer(source="marketplace_vehicle", required=False)
    completion_percent = serializers.SerializerMethodField()

    class Meta:
        model = MarketplaceDriverProfile
        fields = (
            "public_id",
            "slug",
            "first_name",
            "last_name",
            "display_name",
            "business_name",
            "business_identifier",
            "professional_status",
            "vtc_card_number",
            "vtc_issuing_authority",
            "vtc_valid_until",
            "insurance_provider",
            "insurance_policy_reference",
            "insurance_valid_until",
            "years_experience",
            "certifications",
            "bio",
            "profile_photo",
            "professional_email",
            "phone",
            "whatsapp_phone",
            "preferred_contact_method",
            "show_phone_publicly",
            "show_whatsapp_publicly",
            "languages",
            "directions",
            "maximum_radius_km",
            "max_passengers",
            "accepted_payment_methods",
            "airport_ids",
            "service_area_ids",
            "vehicle",
            "indicative_price_from",
            "indicative_price_currency",
            "pricing_note",
            "minimum_notice_hours",
            "typical_response_minutes",
            "availability_note",
            "cancellation_note",
            "verification_status",
            "is_published",
            "accepts_quote_requests",
            "completion_percent",
        )
        read_only_fields = ("public_id", "slug", "verification_status", "is_published")

    def validate(self, attrs):
        instance = self.instance
        selected_airports = attrs.get("airports")
        if selected_airports is None and instance is not None:
            selected_airports = instance.airports.filter(is_active=True)
        selected_airports = list(selected_airports or [])
        if not selected_airports and self.initial_data.get("airport_ids"):
            selected_airports = list(
                Airport.objects.filter(
                    public_id__in=self.initial_data.get("airport_ids"), is_active=True
                )
            )
        if attrs.get("directions") and not any(airport.is_active for airport in selected_airports):
            raise serializers.ValidationError(
                {"airport_ids": "Sélectionnez au moins un aéroport actif."}
            )
        return attrs

    def _save_vehicle(self, profile, vehicle_data):
        if vehicle_data is None:
            return
        MarketplaceVehicle.objects.update_or_create(profile=profile, defaults=vehicle_data)

    def create(self, validated_data):
        vehicle = validated_data.pop("marketplace_vehicle", None)
        profile = super().create(validated_data)
        self._save_vehicle(profile, vehicle)
        return profile

    def update(self, instance, validated_data):
        vehicle = validated_data.pop("marketplace_vehicle", None)
        profile = super().update(instance, validated_data)
        self._save_vehicle(profile, vehicle)
        return profile

    def get_completion_percent(self, obj):
        checks = [
            obj.display_name,
            obj.bio,
            obj.professional_email or obj.user.email,
            obj.phone,
            obj.languages,
            obj.directions,
            obj.airports.exists(),
            obj.service_areas.exists(),
            hasattr(obj, "marketplace_vehicle"),
            obj.vtc_card_number,
            obj.insurance_provider,
        ]
        return round(sum(bool(value) for value in checks) * 100 / len(checks))


class DriverInquiryCreateSerializer(serializers.Serializer):
    driver_id = serializers.CharField(max_length=220)
    airport_id = serializers.UUIDField()
    customer_name = serializers.CharField(max_length=180, trim_whitespace=True)
    customer_email = serializers.EmailField(max_length=254)
    customer_phone = serializers.CharField(max_length=32, trim_whitespace=True)
    customer_whatsapp = serializers.CharField(max_length=32, required=False, allow_blank=True)
    preferred_contact_method = serializers.ChoiceField(
        choices=MarketplaceDriverProfile.ContactMethod.choices
    )
    whatsapp_consent = serializers.BooleanField(default=False)
    direction = serializers.ChoiceField(choices=DriverInquiry.Direction.choices)
    destination = serializers.CharField(min_length=3, max_length=300, trim_whitespace=True)
    pickup_at = serializers.DateTimeField(required=False, allow_null=True)
    passenger_count = serializers.IntegerField(min_value=1, max_value=30)
    luggage_count = serializers.IntegerField(min_value=0, max_value=60, default=0)
    message = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, trim_whitespace=True
    )
    privacy_consent = serializers.BooleanField()
    privacy_policy_version = serializers.CharField(max_length=80)
    consent_text_version = serializers.CharField(max_length=80)
    allowed_contact_channels = serializers.ListField(
        child=serializers.ChoiceField(choices=MarketplaceDriverProfile.ContactMethod.choices),
        allow_empty=False,
    )
    website = serializers.CharField(required=False, allow_blank=True, max_length=200)
    form_started_at = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        for field in ("customer_name", "customer_email", "customer_phone", "customer_whatsapp"):
            if any(char in attrs.get(field, "") for char in ("\r", "\n", "\x00")):
                raise serializers.ValidationError({field: "Caractères non autorisés."})
        for field in ("destination", "message"):
            if CONTROL_CHARACTERS.search(attrs.get(field, "")):
                raise serializers.ValidationError({field: "Caractères non autorisés."})
        elapsed = int(time.time() * 1000) - attrs["form_started_at"]
        if elapsed < 3000:
            raise serializers.ValidationError(
                {"form_started_at": "Le formulaire a été envoyé trop rapidement."}
            )
        if elapsed > 4 * 60 * 60 * 1000:
            raise serializers.ValidationError(
                {"form_started_at": "Le formulaire a expiré. Rechargez la page."}
            )
        if not attrs["privacy_consent"]:
            raise serializers.ValidationError(
                {"privacy_consent": "Votre accord est nécessaire pour transmettre la demande."}
            )
        privacy = LegalDocument.objects.filter(
            kind=LegalDocument.Kind.PRIVACY,
            version=attrs["privacy_policy_version"],
            is_published=True,
            effective_at__lte=timezone.now(),
        ).first()
        if not privacy:
            raise serializers.ValidationError(
                {
                    "privacy_policy_version": (
                        "La version de confidentialité n’est plus valide. Rechargez la page."
                    )
                }
            )
        if attrs["consent_text_version"] != "marketplace-inquiry-v1":
            raise serializers.ValidationError(
                {"consent_text_version": "La version du consentement est invalide."}
            )
        if attrs["preferred_contact_method"] not in attrs["allowed_contact_channels"]:
            raise serializers.ValidationError(
                {"allowed_contact_channels": "Le canal préféré doit être autorisé."}
            )
        if attrs[
            "preferred_contact_method"
        ] == MarketplaceDriverProfile.ContactMethod.WHATSAPP and (
            not attrs.get("customer_whatsapp") or not attrs["whatsapp_consent"]
        ):
            raise serializers.ValidationError(
                {"customer_whatsapp": "Un numéro et un accord WhatsApp sont requis."}
            )
        driver_key = attrs.pop("driver_id")
        driver = (
            MarketplaceDriverProfile.objects.filter(
                is_published=True,
                verification_status=MarketplaceDriverProfile.VerificationStatus.VERIFIED,
                accepts_quote_requests=True,
            )
            .filter(
                models.Q(slug=driver_key) | models.Q(public_id=driver_key)
                if self._is_uuid(driver_key)
                else models.Q(slug=driver_key)
            )
            .first()
        )
        if not driver:
            raise serializers.ValidationError(
                {"driver_id": "Ce chauffeur n’accepte pas de demandes."}
            )
        airport = Airport.objects.filter(public_id=attrs.pop("airport_id"), is_active=True).first()
        if not airport or not driver.airports.filter(pk=getattr(airport, "pk", None)).exists():
            raise serializers.ValidationError(
                {"airport_id": "Cet aéroport n’est pas desservi par ce chauffeur."}
            )
        if attrs["direction"] not in (
            driver.directions
            or [choice for choice, _ in MarketplaceDriverProfile.Direction.choices]
        ):
            raise serializers.ValidationError(
                {"direction": "Cette direction n’est pas proposée par ce chauffeur."}
            )
        attrs["driver"] = driver
        attrs["airport"] = airport
        return attrs

    @staticmethod
    def _is_uuid(value):
        try:
            import uuid

            uuid.UUID(str(value))
            return True
        except ValueError:
            return False


class InquiryHistorySerializer(serializers.ModelSerializer):
    status_label = serializers.SerializerMethodField()

    class Meta:
        model = InquiryStatusHistory
        fields = ("from_status", "to_status", "status_label", "customer_visible_note", "changed_at")

    def get_status_label(self, obj):
        return STATUS_LABELS.get(obj.to_status, obj.to_status)


class InquiryNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = InquiryNote
        fields = ("body", "customer_visible", "created_at")


class DriverInquirySerializer(serializers.ModelSerializer):
    airport_name = serializers.CharField(source="airport.name", read_only=True)
    airport_code = serializers.CharField(source="airport.iata_code", read_only=True)
    status_label = serializers.SerializerMethodField()
    history = InquiryHistorySerializer(source="status_history", many=True, read_only=True)
    notes = InquiryNoteSerializer(many=True, read_only=True)
    notification_status = serializers.SerializerMethodField()
    consent = serializers.SerializerMethodField()

    class Meta:
        model = DriverInquiry
        fields = (
            "public_id",
            "reference",
            "airport_name",
            "airport_code",
            "direction",
            "customer_name",
            "customer_email",
            "customer_phone",
            "customer_whatsapp",
            "preferred_contact_method",
            "whatsapp_consent",
            "destination",
            "pickup_at",
            "passenger_count",
            "luggage_count",
            "message",
            "status",
            "status_label",
            "created_at",
            "updated_at",
            "history",
            "notes",
            "notification_status",
            "consent",
        )

    def get_status_label(self, obj):
        return STATUS_LABELS.get(obj.status, obj.status)

    def get_notification_status(self, obj):
        records = EmailNotification.objects.filter(
            related_type="driver_inquiry", related_public_id=obj.public_id
        )
        return {item.kind: item.status for item in records}

    def get_consent(self, obj):
        consent = getattr(obj, "consent", None)
        return (
            {
                "privacy_policy_version": consent.privacy_policy_version,
                "granted_at": consent.granted_at,
                "allowed_contact_channels": consent.allowed_contact_channels,
            }
            if consent
            else None
        )


class InquiryTransitionSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=DriverInquiry.Status.choices)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)
    customer_visible_note = serializers.CharField(max_length=500, required=False, allow_blank=True)


class InquiryNoteCreateSerializer(serializers.Serializer):
    body = serializers.CharField(min_length=1, max_length=2000, trim_whitespace=True)
    customer_visible = serializers.BooleanField(default=False)

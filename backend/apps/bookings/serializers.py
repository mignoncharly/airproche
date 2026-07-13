from __future__ import annotations

from django.utils import timezone
from rest_framework import serializers

from .models import Booking, BookingNote, BookingStatusHistory, PriceLine


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError(
                    {key: "Ce champ nâ€™est pas acceptÃ©." for key in sorted(unknown)}
                )
        return super().to_internal_value(data)


class BookingCreateSerializer(StrictSerializer):
    quote_id = serializers.UUIDField()
    booking_type = serializers.ChoiceField(choices=Booking.Type.choices)
    pickup_address = serializers.CharField(max_length=300, required=False, allow_blank=True)
    destination_address = serializers.CharField(max_length=300, required=False, allow_blank=True)
    pickup_locality = serializers.CharField(max_length=120, required=False, allow_blank=True)
    destination_locality = serializers.CharField(max_length=120, required=False, allow_blank=True)
    flight_number = serializers.CharField(max_length=32, required=False, allow_blank=True)
    airline = serializers.CharField(max_length=120, required=False, allow_blank=True)
    origin_city_country = serializers.CharField(max_length=160, required=False, allow_blank=True)
    terminal = serializers.CharField(max_length=80, required=False, allow_blank=True)
    meeting_information = serializers.CharField(max_length=500, required=False, allow_blank=True)
    adult_count = serializers.IntegerField(min_value=0, max_value=50, default=1)
    child_count = serializers.IntegerField(min_value=0, max_value=50, default=0)
    oversized_luggage_count = serializers.IntegerField(min_value=0, max_value=20, default=0)
    accessibility_request = serializers.BooleanField(default=False)
    accessibility_details = serializers.CharField(max_length=500, required=False, allow_blank=True)
    additional_requirements = serializers.CharField(max_length=4000, required=False, allow_blank=True)
    passenger_same_as_booker = serializers.BooleanField(default=True)
    booker_first_name = serializers.CharField(max_length=150)
    booker_last_name = serializers.CharField(max_length=150)
    booker_email = serializers.EmailField(max_length=254)
    booker_phone = serializers.CharField(max_length=32)
    booker_whatsapp = serializers.CharField(max_length=32, required=False, allow_blank=True)
    passenger_first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    passenger_last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    passenger_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    passenger_whatsapp = serializers.CharField(max_length=32, required=False, allow_blank=True)
    passenger_locale = serializers.CharField(max_length=10, default="fr")
    accept_terms = serializers.BooleanField()
    accept_privacy = serializers.BooleanField()

    def validate(self, attrs):
        if not attrs["accept_terms"] or not attrs["accept_privacy"]:
            raise serializers.ValidationError(
                "Les conditions et la politique de confidentialitÃ© doivent Ãªtre acceptÃ©es."
            )
        if attrs["adult_count"] + attrs["child_count"] == 0:
            raise serializers.ValidationError({"adult_count": "Indiquez au moins un passager."})
        if not attrs.get("passenger_same_as_booker") and not (
            attrs.get("passenger_first_name") and attrs.get("passenger_last_name")
        ):
            raise serializers.ValidationError(
                {"passenger_first_name": "Les coordonnÃ©es du passager sont nÃ©cessaires."}
            )
        return attrs


class PriceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceLine
        fields = ("code", "label", "quantity", "unit_amount", "total_amount")


class BookingStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingStatusHistory
        fields = ("from_status", "to_status", "note", "created_at")


class BookingNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingNote
        fields = ("visibility", "body", "created_at")


class BookingSerializer(serializers.ModelSerializer):
    airport = serializers.SerializerMethodField()
    service_area = serializers.SerializerMethodField()
    lines = serializers.SerializerMethodField()
    history = BookingStatusHistorySerializer(source="status_history", many=True)
    notes = serializers.SerializerMethodField()
    cancellation_eligible = serializers.SerializerMethodField()
    management_token = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = Booking
        fields = (
            "public_id", "reference", "booking_type", "status", "payment_mode",
            "airport", "service_area", "pickup_address", "destination_address",
            "pickup_locality", "destination_locality", "pickup_at", "flight_number",
            "airline", "origin_city_country", "terminal", "meeting_information",
            "passenger_count", "adult_count", "child_count", "luggage_count",
            "oversized_luggage_count", "child_seat_quantity", "accessibility_request",
            "additional_requirements", "booker_first_name", "booker_last_name",
            "booker_email", "booker_phone", "passenger_first_name", "passenger_last_name",
            "passenger_phone", "passenger_locale", "total_amount", "currency",
            "cancellation_deadline", "cancellation_eligible", "lines", "history", "notes",
            "created_at", "updated_at", "management_token",
        )

    def get_airport(self, obj):
        return {"name": obj.airport.name, "iata_code": obj.airport.iata_code}

    def get_service_area(self, obj):
        return {"name": obj.service_area.name, "slug": obj.service_area.slug}

    def get_lines(self, obj):
        snapshot = getattr(obj, "price_snapshot", None)
        return PriceLineSerializer(snapshot.lines.all(), many=True).data if snapshot else []

    def get_notes(self, obj):
        notes = obj.notes.all()
        if not self.context.get("is_staff"):
            notes = notes.filter(visibility=BookingNote.Visibility.CUSTOMER)
        return BookingNoteSerializer(notes, many=True).data

    def get_cancellation_eligible(self, obj):
        return (
            obj.status in {
                Booking.Status.PENDING_PAYMENT, Booking.Status.CONFIRMED,
                Booking.Status.DRIVER_ASSIGNMENT_PENDING, Booking.Status.DRIVER_ASSIGNED,
            }
            and (obj.cancellation_deadline is None or obj.cancellation_deadline > timezone.now())
        )


class GuestAccessSerializer(StrictSerializer):
    reference = serializers.CharField(max_length=24)
    management_token = serializers.CharField(max_length=256, trim_whitespace=False)


class CancellationSerializer(StrictSerializer):
    reason = serializers.CharField(max_length=300, required=False, allow_blank=True)


class TransitionSerializer(StrictSerializer):
    to_status = serializers.ChoiceField(choices=Booking.Status.choices)
    note = serializers.CharField(max_length=500, required=False, allow_blank=True)

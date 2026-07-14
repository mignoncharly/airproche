from rest_framework import serializers

from apps.locations.models import Airport, ServiceArea
from apps.locations.serializers import AirportListSerializer, ServiceAreaListSerializer

from .models import DriverInquiry, MarketplaceDriverProfile


PAYMENT_METHODS = ("cash", "card_terminal", "bank_transfer", "private_payment_link")


class DriverDirectorySerializer(serializers.ModelSerializer):
    airports = AirportListSerializer(many=True, read_only=True)
    service_areas = ServiceAreaListSerializer(many=True, read_only=True)

    class Meta:
        model = MarketplaceDriverProfile
        fields = ("public_id", "display_name", "business_name", "bio", "max_passengers", "accepted_payment_methods", "airports", "service_areas", "accepts_quote_requests")


class DriverProfileSerializer(serializers.ModelSerializer):
    accepted_payment_methods = serializers.ListField(child=serializers.ChoiceField(choices=PAYMENT_METHODS), required=False, allow_empty=True)
    airport_ids = serializers.SlugRelatedField(source="airports", slug_field="public_id", queryset=Airport.objects.filter(is_active=True), many=True, required=False)
    service_area_ids = serializers.SlugRelatedField(source="service_areas", slug_field="public_id", queryset=ServiceArea.objects.filter(is_active=True), many=True, required=False)

    class Meta:
        model = MarketplaceDriverProfile
        fields = ("public_id", "display_name", "business_name", "business_identifier", "vtc_card_number", "insurance_provider", "bio", "phone", "max_passengers", "accepted_payment_methods", "airport_ids", "service_area_ids", "verification_status", "is_published", "accepts_quote_requests")
        read_only_fields = ("public_id", "verification_status", "is_published")


class DriverInquiryCreateSerializer(serializers.ModelSerializer):
    driver_id = serializers.UUIDField(write_only=True)
    airport_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = DriverInquiry
        fields = ("driver_id", "airport_id", "customer_name", "customer_email", "customer_phone", "destination", "pickup_at", "passenger_count", "message")

    def validate(self, attrs):
        driver_id = attrs.pop("driver_id")
        airport_id = attrs.pop("airport_id", None)
        driver = MarketplaceDriverProfile.objects.filter(public_id=driver_id, is_published=True, verification_status=MarketplaceDriverProfile.VerificationStatus.VERIFIED, accepts_quote_requests=True).first()
        if not driver:
            raise serializers.ValidationError({"driver_id": "Ce chauffeur n'accepte pas de demandes."})
        attrs["driver"] = driver
        if airport_id:
            airport = Airport.objects.filter(public_id=airport_id, is_active=True).first()
            if not airport or not driver.airports.filter(pk=airport.pk).exists():
                raise serializers.ValidationError({"airport_id": "Cet aeroport n'est pas publie par ce chauffeur."})
            attrs["airport"] = airport
        return attrs


class DriverInquirySerializer(serializers.ModelSerializer):
    airport_name = serializers.CharField(source="airport.name", read_only=True, allow_null=True)

    class Meta:
        model = DriverInquiry
        fields = ("public_id", "airport_name", "customer_name", "customer_email", "customer_phone", "destination", "pickup_at", "passenger_count", "message", "status", "created_at")

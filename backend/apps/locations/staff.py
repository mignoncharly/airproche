from rest_framework import serializers

from apps.core.staff import AuditedStaffModelViewSet

from .models import Airport, ServiceArea


class AirportStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = (
            "public_id",
            "name",
            "iata_code",
            "slug",
            "city",
            "country_code",
            "address",
            "latitude",
            "longitude",
            "timezone",
            "terminal_guidance",
            "description",
            "seo_title",
            "seo_description",
            "is_active",
            "display_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("public_id", "created_at", "updated_at")


class ServiceAreaStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceArea
        fields = (
            "public_id",
            "name",
            "slug",
            "area_type",
            "country_code",
            "region",
            "city",
            "postal_codes",
            "provider_place_id",
            "description",
            "is_active",
            "display_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("public_id", "created_at", "updated_at")


class AirportStaffViewSet(AuditedStaffModelViewSet):
    queryset = Airport.objects.all()
    serializer_class = AirportStaffSerializer
    lookup_field = "public_id"


class ServiceAreaStaffViewSet(AuditedStaffModelViewSet):
    queryset = ServiceArea.objects.all()
    serializer_class = ServiceAreaStaffSerializer
    lookup_field = "public_id"

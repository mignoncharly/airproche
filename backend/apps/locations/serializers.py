from rest_framework import serializers

from .models import Airport, ServiceArea


class AirportListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = ("public_id", "name", "iata_code", "slug", "city", "country_code")


class AirportDetailSerializer(AirportListSerializer):
    class Meta(AirportListSerializer.Meta):
        fields = AirportListSerializer.Meta.fields + (
            "address",
            "latitude",
            "longitude",
            "timezone",
            "terminal_guidance",
            "description",
            "seo_title",
            "seo_description",
        )


class ServiceAreaListSerializer(serializers.ModelSerializer):
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
            "description",
        )


class ServiceAreaDetailSerializer(ServiceAreaListSerializer):
    class Meta(ServiceAreaListSerializer.Meta):
        fields = ServiceAreaListSerializer.Meta.fields + ("postal_codes",)

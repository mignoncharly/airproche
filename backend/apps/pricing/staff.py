from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.core.staff import AuditedStaffModelViewSet
from apps.locations.models import Airport, ServiceArea

from .models import Tariff, TariffOption


class TariffStaffSerializer(serializers.ModelSerializer):
    airport_id = serializers.SlugRelatedField(
        source="airport", slug_field="public_id", queryset=Airport.objects.all()
    )
    service_area_id = serializers.SlugRelatedField(
        source="service_area", slug_field="public_id", queryset=ServiceArea.objects.all()
    )

    class Meta:
        model = Tariff
        fields = (
            "public_id",
            "airport_id",
            "service_area_id",
            "trip_type",
            "base_amount",
            "currency",
            "passenger_capacity",
            "luggage_capacity",
            "valid_from",
            "valid_until",
            "priority",
            "is_active",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("public_id", "created_at", "updated_at")

    def validate(self, attrs):
        instance = self.instance or Tariff()
        for key, value in attrs.items():
            setattr(instance, key, value)
        try:
            instance.full_clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                getattr(error, "message_dict", {"non_field_errors": error.messages})
            ) from error
        return attrs


class TariffOptionStaffSerializer(serializers.ModelSerializer):
    tariff_id = serializers.SlugRelatedField(
        source="tariff",
        slug_field="public_id",
        queryset=Tariff.objects.all(),
        allow_null=True,
        required=False,
    )

    class Meta:
        model = TariffOption
        fields = (
            "id",
            "code",
            "label",
            "tariff_id",
            "pricing_method",
            "amount",
            "currency",
            "maximum_quantity",
            "valid_from",
            "valid_until",
            "is_active",
            "display_order",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        instance = self.instance or TariffOption()
        for key, value in attrs.items():
            setattr(instance, key, value)
        try:
            instance.full_clean()
        except DjangoValidationError as error:
            raise serializers.ValidationError(
                getattr(error, "message_dict", {"non_field_errors": error.messages})
            ) from error
        return attrs


class TariffStaffViewSet(AuditedStaffModelViewSet):
    queryset = Tariff.objects.select_related("airport", "service_area")
    serializer_class = TariffStaffSerializer
    lookup_field = "public_id"


class TariffOptionStaffViewSet(AuditedStaffModelViewSet):
    queryset = TariffOption.objects.select_related("tariff")
    serializer_class = TariffOptionStaffSerializer

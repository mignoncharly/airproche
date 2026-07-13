from django.utils import timezone
from rest_framework import serializers

from .models import Quote, QuoteLine, TariffOption, TripType


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError(
                    {key: "Ce champ n’est pas accepté." for key in sorted(unknown)}
                )
        return super().to_internal_value(data)


class QuoteOptionRequestSerializer(StrictSerializer):
    code = serializers.SlugField(max_length=80)
    quantity = serializers.IntegerField(min_value=1, max_value=20)


class QuoteRequestSerializer(StrictSerializer):
    trip_type = serializers.ChoiceField(choices=TripType.choices)
    airport_id = serializers.UUIDField()
    service_area_id = serializers.UUIDField()
    pickup_at = serializers.DateTimeField()
    passenger_count = serializers.IntegerField(min_value=1, max_value=50)
    luggage_count = serializers.IntegerField(min_value=0, max_value=100)
    options = QuoteOptionRequestSerializer(many=True, required=False, default=list)

    def validate_options(self, value):
        codes = [item["code"] for item in value]
        if len(codes) != len(set(codes)):
            raise serializers.ValidationError("Une option ne peut apparaître qu’une fois.")
        return value


class QuoteLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuoteLine
        fields = ("code", "label", "quantity", "unit_amount", "total_amount")


class QuoteSerializer(serializers.ModelSerializer):
    lines = QuoteLineSerializer(many=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Quote
        fields = (
            "public_id",
            "trip_type",
            "airport_name",
            "airport_iata_code",
            "service_area_name",
            "pickup_at",
            "passenger_count",
            "luggage_count",
            "total_amount",
            "currency",
            "calculation_version",
            "status",
            "expires_at",
            "lines",
        )

    def get_status(self, obj: Quote) -> str:
        return Quote.Status.EXPIRED if obj.expires_at <= timezone.now() else obj.status


class CoverageOptionSerializer(serializers.Serializer):
    code = serializers.CharField()
    label = serializers.CharField()
    pricing_method = serializers.ChoiceField(choices=TariffOption.PricingMethod.choices)
    maximum_quantity = serializers.IntegerField()


class CoverageRouteSerializer(serializers.Serializer):
    airport_id = serializers.UUIDField()
    service_area_id = serializers.UUIDField()
    trip_type = serializers.ChoiceField(choices=TripType.choices)
    options = CoverageOptionSerializer(many=True)


class CoverageSerializer(serializers.Serializer):
    routes = CoverageRouteSerializer(many=True)

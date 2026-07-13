from __future__ import annotations

from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status, serializers
from rest_framework.views import APIView

from apps.pricing.serializers import QuoteSerializer
from apps.pricing.services import create_quote

from .models import Booking
from .services import can_access


class RepeatBookingSerializer(serializers.Serializer):
    pickup_at = serializers.DateTimeField()
    passenger_count = serializers.IntegerField(min_value=1, max_value=50, required=False)
    luggage_count = serializers.IntegerField(min_value=0, max_value=100, required=False)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError({key: "Ce champ n’est pas accepté." for key in unknown})
        return super().to_internal_value(data)


class RepeatBookingView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "booking_create"

    def post(self, request, public_id):
        serializer = RepeatBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = Booking.objects.select_related("quote", "airport", "service_area").prefetch_related("quote__lines").get(public_id=public_id)
        except Booking.DoesNotExist:
            return Response({"detail": "Réservation introuvable."}, status=404)
        if not can_access(booking, user=request.user, raw_token=request.headers.get("X-Booking-Token", "")):
            return Response({"detail": "Réservation introuvable."}, status=404)
        values = serializer.validated_data
        quote = create_quote({
            "trip_type": booking.booking_type,
            "airport_id": booking.airport.public_id,
            "service_area_id": booking.service_area.public_id,
            "pickup_at": values["pickup_at"],
            "passenger_count": values.get("passenger_count", booking.passenger_count),
            "luggage_count": values.get("luggage_count", booking.luggage_count),
            "options": [
                {"code": line.code, "quantity": line.quantity}
                for line in booking.quote.lines.all() if line.code != "base-fare"
            ],
        })
        return Response(QuoteSerializer(quote).data, status=status.HTTP_201_CREATED)

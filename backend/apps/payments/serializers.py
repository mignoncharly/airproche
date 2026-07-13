from __future__ import annotations

from decimal import Decimal

from rest_framework import serializers

from .models import Payment, Refund


class RefundRequestSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=Decimal("0.01"), required=False)
    reason = serializers.CharField(max_length=300, required=False, allow_blank=True)

    def to_internal_value(self, data):
        if isinstance(data, dict):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError({key: "Ce champ n’est pas accepté." for key in unknown})
        return super().to_internal_value(data)


class PaymentSerializer(serializers.ModelSerializer):
    booking_reference = serializers.CharField(source="booking.reference", read_only=True)
    booking_status = serializers.CharField(source="booking.status", read_only=True)
    paid_at = serializers.DateTimeField(allow_null=True, read_only=True)

    class Meta:
        model = Payment
        fields = (
            "public_id", "booking_reference", "booking_status", "provider", "status", "amount",
            "currency", "environment", "paid_at", "last_error_code", "last_error_message",
        )


class CheckoutResponseSerializer(serializers.Serializer):
    checkout_url = serializers.URLField()
    payment = PaymentSerializer()
    payment_attempt_id = serializers.IntegerField()
    idempotent_replay = serializers.BooleanField()


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ("id", "amount", "currency", "reason", "status", "provider_refund_id", "failure_code", "failure_message", "requested_at", "completed_at")


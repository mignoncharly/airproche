from __future__ import annotations

from rest_framework import serializers

from apps.bookings.models import Booking, BookingNote
from apps.bookings.serializers import BookingSerializer
from apps.locations.models import ServiceArea
from apps.payments.models import Payment
from apps.payments.serializers import PaymentSerializer

from .models import AuditEvent, Driver, DriverAssignment, Vehicle


class DriverStaffSerializer(serializers.ModelSerializer):
    service_area_ids = serializers.SlugRelatedField(
        source="service_areas", slug_field="public_id", queryset=ServiceArea.objects.all(), many=True, required=False
    )
    name = serializers.CharField(read_only=True)

    class Meta:
        model = Driver
        fields = ("public_id", "name", "first_name", "last_name", "email", "phone", "max_passengers", "active", "service_area_ids", "notes", "created_at", "updated_at")
        read_only_fields = ("public_id", "name", "created_at", "updated_at")


class VehicleStaffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ("public_id", "registration", "label", "seats", "luggage_capacity", "accessibility_capable", "active", "notes", "created_at", "updated_at")
        read_only_fields = ("public_id", "created_at", "updated_at")


class DriverAssignmentSerializer(serializers.ModelSerializer):
    driver = DriverStaffSerializer(read_only=True)
    vehicle = VehicleStaffSerializer(read_only=True)
    active = serializers.BooleanField(read_only=True)

    class Meta:
        model = DriverAssignment
        fields = ("public_id", "driver", "vehicle", "assigned_at", "assigned_by", "unassigned_at", "unassigned_by", "released_to_customer_at", "override_reason", "active")
        read_only_fields = fields


class OperationsBookingSerializer(BookingSerializer):
    customer_email = serializers.CharField(source="customer.email", read_only=True, allow_null=True)
    payment = serializers.SerializerMethodField()
    assignment = serializers.SerializerMethodField()

    class Meta(BookingSerializer.Meta):
        fields = BookingSerializer.Meta.fields + ("customer_email", "source", "assignment", "payment")

    def get_payment(self, obj):
        try:
            return PaymentSerializer(obj.payment).data
        except Payment.DoesNotExist:
            return None

    def get_assignment(self, obj):
        assignments = getattr(obj, "active_assignments", None)
        if assignments is None:
            assignments = obj.driver_assignments.filter(unassigned_at__isnull=True).select_related("driver", "vehicle")
        assignment = next(iter(assignments), None)
        return DriverAssignmentSerializer(assignment).data if assignment else None


class AssignmentRequestSerializer(serializers.Serializer):
    driver_id = serializers.UUIDField()
    vehicle_id = serializers.UUIDField()
    allow_override = serializers.BooleanField(default=False)
    override_reason = serializers.CharField(max_length=500, required=False, allow_blank=True)

    def validate(self, attrs):
        if attrs["allow_override"] and not attrs.get("override_reason", "").strip():
            raise serializers.ValidationError({"override_reason": "Une raison est obligatoire pour un remplacement."})
        return attrs


class UnassignmentRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)


class BookingNoteRequestSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=4000)
    visibility = serializers.ChoiceField(choices=BookingNote.Visibility.choices, default=BookingNote.Visibility.INTERNAL)


class AuditEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.CharField(source="actor.email", read_only=True, allow_null=True)

    class Meta:
        model = AuditEvent
        fields = ("id", "action", "actor_email", "before", "after", "reason", "correlation_id", "created_at")


class OperationsSummarySerializer(serializers.Serializer):
    period = serializers.DictField()
    has_data = serializers.BooleanField()
    total_bookings = serializers.IntegerField()
    pending_assignment = serializers.IntegerField()
    unassigned_upcoming = serializers.IntegerField()
    active_trips = serializers.IntegerField()
    payment_attention = serializers.IntegerField()
    confirmed_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.CharField()


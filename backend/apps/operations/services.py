from __future__ import annotations

from datetime import timedelta

from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, ValidationError

from apps.bookings.models import Booking, BookingStatusHistory

from .models import AuditEvent, Driver, DriverAssignment, Vehicle


class AssignmentConflict(APIException):
    status_code = 409
    default_code = "assignment_conflict"
    default_detail = "Cette affectation entre en conflit avec une autre course."


def audit(*, actor, action, instance, before=None, after=None, reason="", correlation_id=""):
    return AuditEvent.objects.create(
        actor=actor,
        action=action,
        content_type=ContentType.objects.get_for_model(instance, for_concrete_model=False),
        object_id=str(instance.pk),
        before=before or {},
        after=after or {},
        reason=reason,
        correlation_id=correlation_id,
    )


def assignment_snapshot(assignment: DriverAssignment) -> dict:
    return {
        "booking": assignment.booking.reference,
        "driver": assignment.driver.name,
        "vehicle": assignment.vehicle.registration,
        "active": assignment.active,
        "override_reason": assignment.override_reason,
    }


def _overlapping_assignments(booking: Booking, *, driver: Driver, vehicle: Vehicle, exclude_id=None):
    start = booking.pickup_at - timedelta(hours=2)
    end = booking.pickup_at + timedelta(hours=2)
    queryset = DriverAssignment.objects.filter(
        unassigned_at__isnull=True,
        booking__pickup_at__gte=start,
        booking__pickup_at__lte=end,
    ).exclude(booking_id=booking.pk).select_related("booking", "driver", "vehicle")
    if exclude_id:
        queryset = queryset.exclude(pk=exclude_id)
    return queryset.filter(driver=driver) | queryset.filter(vehicle=vehicle)


@transaction.atomic
def assign_driver(*, booking_id, driver_id, vehicle_id, actor, allow_override=False, override_reason="", correlation_id=""):
    booking = Booking.objects.select_for_update().select_related("service_area").get(pk=booking_id)
    driver = Driver.objects.select_for_update().prefetch_related("service_areas").get(pk=driver_id)
    vehicle = Vehicle.objects.select_for_update().get(pk=vehicle_id)
    if not driver.active:
        raise ValidationError({"driver_id": "Le conducteur est inactif."})
    if not vehicle.active:
        raise ValidationError({"vehicle_id": "Le véhicule est inactif."})
    if driver.service_areas.exists() and not driver.service_areas.filter(pk=booking.service_area_id).exists() and not allow_override:
        raise AssignmentConflict("Le conducteur ne couvre pas cette zone.")
    capacity_errors = []
    if booking.passenger_count > driver.max_passengers:
        capacity_errors.append("driver_capacity")
    if booking.passenger_count > vehicle.seats:
        capacity_errors.append("vehicle_seats")
    if booking.luggage_count > vehicle.luggage_capacity:
        capacity_errors.append("vehicle_luggage")
    if booking.accessibility_request and not vehicle.accessibility_capable:
        capacity_errors.append("accessibility")
    if capacity_errors and not allow_override:
        raise AssignmentConflict(",".join(capacity_errors))
    conflicts = list(_overlapping_assignments(booking, driver=driver, vehicle=vehicle)[:5])
    if conflicts and not allow_override:
        raise AssignmentConflict("driver_or_vehicle_overlap")
    existing = DriverAssignment.objects.select_for_update().filter(booking=booking, unassigned_at__isnull=True).first()
    before = assignment_snapshot(existing) if existing else {}
    if existing:
        existing.unassigned_at = timezone.now()
        existing.unassigned_by = actor
        existing.save(update_fields=("unassigned_at", "unassigned_by"))
    assignment = DriverAssignment.objects.create(
        booking=booking,
        driver=driver,
        vehicle=vehicle,
        assigned_by=actor,
        override_reason=override_reason if allow_override else "",
    )
    old_status = booking.status
    if old_status != Booking.Status.DRIVER_ASSIGNED:
        booking.status = Booking.Status.DRIVER_ASSIGNED
        booking.save(update_fields=("status", "updated_at"))
        BookingStatusHistory.objects.create(booking=booking, from_status=old_status, to_status=booking.status, actor=actor, note="Driver assignment created.", correlation_id=correlation_id)
    audit(actor=actor, action="driver_assignment_created", instance=assignment, before=before, after=assignment_snapshot(assignment), reason=override_reason, correlation_id=correlation_id)
    return assignment


@transaction.atomic
def unassign_driver(*, assignment_id, actor, reason="", correlation_id=""):
    assignment = DriverAssignment.objects.select_for_update().select_related("booking", "driver", "vehicle").get(pk=assignment_id)
    if not assignment.active:
        return assignment
    before = assignment_snapshot(assignment)
    assignment.unassigned_at = timezone.now()
    assignment.unassigned_by = actor
    assignment.save(update_fields=("unassigned_at", "unassigned_by"))
    if assignment.booking.status == Booking.Status.DRIVER_ASSIGNED:
        old_status = assignment.booking.status
        assignment.booking.status = Booking.Status.DRIVER_ASSIGNMENT_PENDING
        assignment.booking.save(update_fields=("status", "updated_at"))
        BookingStatusHistory.objects.create(booking=assignment.booking, from_status=old_status, to_status=assignment.booking.status, actor=actor, note=reason, correlation_id=correlation_id)
    audit(actor=actor, action="driver_assignment_removed", instance=assignment, before=before, after=assignment_snapshot(assignment), reason=reason, correlation_id=correlation_id)
    return assignment


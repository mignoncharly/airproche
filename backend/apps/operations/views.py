from __future__ import annotations

from datetime import datetime, time, timedelta
from decimal import Decimal

from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Q, Sum
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.bookings.models import Booking, BookingNote, BookingStatusHistory
from apps.bookings.serializers import TransitionSerializer
from apps.bookings.services import transition_booking

from .models import AuditEvent, Driver, DriverAssignment, Vehicle
from .permissions import StaffOperationPermission
from .serializers import (
    AssignmentRequestSerializer, AuditEventSerializer, BookingNoteRequestSerializer,
    DriverAssignmentSerializer, DriverStaffSerializer, OperationsBookingSerializer,
    OperationsSummarySerializer, UnassignmentRequestSerializer, VehicleStaffSerializer,
)
from .services import assign_driver, audit, unassign_driver


class DriverStaffViewSet(ModelViewSet):
    queryset = Driver.objects.prefetch_related("service_areas")
    serializer_class = DriverStaffSerializer
    lookup_field = "public_id"
    permission_classes = (StaffOperationPermission,)
    required_permission = "operations.view_driver"

    def get_permissions(self):
        self.required_permission = "operations.view_driver" if self.action in {"list", "retrieve"} else "operations.change_driver"
        if self.action == "create":
            self.required_permission = "operations.add_driver"
        if self.action == "destroy":
            self.required_permission = "operations.delete_driver"
        return super().get_permissions()


class VehicleStaffViewSet(ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleStaffSerializer
    lookup_field = "public_id"
    permission_classes = (StaffOperationPermission,)
    required_permission = "operations.view_vehicle"

    def get_permissions(self):
        self.required_permission = "operations.view_vehicle" if self.action in {"list", "retrieve"} else "operations.change_vehicle"
        if self.action == "create":
            self.required_permission = "operations.add_vehicle"
        if self.action == "destroy":
            self.required_permission = "operations.delete_vehicle"
        return super().get_permissions()


def operation_booking_queryset():
    return Booking.objects.select_related("airport", "service_area", "customer", "payment").prefetch_related(
        "price_snapshot__lines", "status_history", "notes",
        Prefetch("driver_assignments", queryset=DriverAssignment.objects.filter(unassigned_at__isnull=True).select_related("driver", "vehicle"), to_attr="active_assignments"),
    )


def parse_boundary(value: str | None, *, end=False):
    if not value:
        return None
    parsed = parse_datetime(value)
    if parsed:
        return timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed
    parsed_date = parse_date(value)
    if not parsed_date:
        return None
    boundary = datetime.combine(parsed_date, time.max if end else time.min)
    return timezone.make_aware(boundary, timezone.get_current_timezone())


class OperationsSummaryView(APIView):
    permission_classes = (StaffOperationPermission,)
    required_permission = "bookings.view_booking"
    throttle_scope = "operations_read"

    def get(self, request):
        start = parse_boundary(request.query_params.get("from")) or timezone.now()
        end = parse_boundary(request.query_params.get("to"), end=True) or start + timedelta(days=7)
        bookings = Booking.objects.filter(pickup_at__gte=start, pickup_at__lte=end)
        active_statuses = {Booking.Status.CONFIRMED, Booking.Status.DRIVER_ASSIGNMENT_PENDING, Booking.Status.DRIVER_ASSIGNED, Booking.Status.PASSENGER_CONTACTED, Booking.Status.DRIVER_EN_ROUTE, Booking.Status.DRIVER_ARRIVED, Booking.Status.PASSENGER_PICKED_UP, Booking.Status.IN_PROGRESS}
        revenue_statuses = active_statuses | {Booking.Status.COMPLETED}
        revenue = bookings.filter(status__in=revenue_statuses).aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
        payload = {
            "period": {"from": start.isoformat(), "to": end.isoformat(), "timezone": str(timezone.get_current_timezone())},
            "has_data": bookings.exists(),
            "total_bookings": bookings.exclude(status=Booking.Status.CANCELLED).count(),
            "pending_assignment": bookings.filter(status=Booking.Status.DRIVER_ASSIGNMENT_PENDING).count(),
            "unassigned_upcoming": bookings.filter(status__in=(Booking.Status.CONFIRMED, Booking.Status.DRIVER_ASSIGNMENT_PENDING)).annotate(active_assignment_count=Count("driver_assignments", filter=Q(driver_assignments__unassigned_at__isnull=True))).filter(active_assignment_count=0).count(),
            "active_trips": bookings.filter(status__in=(Booking.Status.DRIVER_EN_ROUTE, Booking.Status.DRIVER_ARRIVED, Booking.Status.PASSENGER_PICKED_UP, Booking.Status.IN_PROGRESS)).count(),
            "payment_attention": bookings.filter(Q(payment__isnull=True) | ~Q(payment__status="succeeded")).exclude(status=Booking.Status.CANCELLED).count(),
            "confirmed_revenue": revenue,
            "currency": "EUR",
        }
        return Response(OperationsSummarySerializer(payload).data)


class OperationsBookingListView(APIView):
    permission_classes = (StaffOperationPermission,)
    required_permission = "bookings.view_booking"
    throttle_scope = "operations_read"

    def get(self, request):
        bookings = operation_booking_queryset()
        query = request.query_params.get("q", "").strip()
        if query:
            bookings = bookings.filter(Q(reference__icontains=query) | Q(booker_email__icontains=query) | Q(booker_phone__icontains=query) | Q(passenger_last_name__icontains=query))
        if request.query_params.get("status"):
            bookings = bookings.filter(status=request.query_params["status"])
        start = parse_boundary(request.query_params.get("from"))
        end = parse_boundary(request.query_params.get("to"), end=True)
        if start:
            bookings = bookings.filter(pickup_at__gte=start)
        if end:
            bookings = bookings.filter(pickup_at__lte=end)
        if request.query_params.get("assigned") in {"true", "false"}:
            bookings = bookings.annotate(active_assignment_count=Count("driver_assignments", filter=Q(driver_assignments__unassigned_at__isnull=True)))
            bookings = bookings.filter(active_assignment_count=1 if request.query_params["assigned"] == "true" else 0)
        if request.query_params.get("payment") == "attention":
            bookings = bookings.filter(Q(payment__isnull=True) | ~Q(payment__status="succeeded"))
        ordering = request.query_params.get("ordering", "pickup_at")
        if ordering not in {"pickup_at", "-pickup_at", "created_at", "-created_at", "status"}:
            ordering = "pickup_at"
        bookings = bookings.order_by(ordering).distinct()[:200]
        return Response(OperationsBookingSerializer(bookings, many=True, context={"is_staff": True}).data)


class OperationsBookingDetailView(APIView):
    permission_classes = (StaffOperationPermission,)
    required_permission = "bookings.view_booking"
    throttle_scope = "operations_read"

    def get(self, request, public_id):
        booking = operation_booking_queryset().filter(public_id=public_id).first()
        if not booking:
            return Response({"detail": "Réservation introuvable."}, status=404)
        return Response(OperationsBookingSerializer(booking, context={"is_staff": True}).data)


@method_decorator(csrf_protect, name="dispatch")
class BookingTransitionActionView(APIView):
    permission_classes = (StaffOperationPermission,)
    required_permission = "bookings.change_booking"
    throttle_scope = "operations_mutation"

    def post(self, request, public_id):
        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = Booking.objects.filter(public_id=public_id).first()
        if not booking:
            return Response({"detail": "Réservation introuvable."}, status=404)
        before = {"status": booking.status}
        booking = transition_booking(booking.pk, serializer.validated_data["to_status"], actor=request.user, note=serializer.validated_data.get("note", ""), correlation_id=getattr(request, "correlation_id", ""))
        audit(actor=request.user, action="booking_status_transition", instance=booking, before=before, after={"status": booking.status}, reason=serializer.validated_data.get("note", ""), correlation_id=getattr(request, "correlation_id", ""))
        return Response(OperationsBookingSerializer(operation_booking_queryset().get(pk=booking.pk), context={"is_staff": True}).data)


@method_decorator(csrf_protect, name="dispatch")
class BookingNoteActionView(APIView):
    permission_classes = (StaffOperationPermission,)
    required_permission = "bookings.add_bookingnote"
    throttle_scope = "operations_mutation"

    def post(self, request, public_id):
        serializer = BookingNoteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = Booking.objects.filter(public_id=public_id).first()
        if not booking:
            return Response({"detail": "Réservation introuvable."}, status=404)
        note = BookingNote.objects.create(booking=booking, author=request.user, **serializer.validated_data)
        audit(actor=request.user, action="booking_note_created", instance=booking, after={"note_id": note.pk, "visibility": note.visibility}, reason="Operational note", correlation_id=getattr(request, "correlation_id", ""))
        return Response({"id": note.pk, "body": note.body, "visibility": note.visibility, "created_at": note.created_at}, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class AssignmentActionView(APIView):
    permission_classes = (StaffOperationPermission,)
    required_permission = "operations.change_driverassignment"
    throttle_scope = "operations_mutation"

    def post(self, request, public_id):
        serializer = AssignmentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = Booking.objects.filter(public_id=public_id).first()
        if not booking:
            return Response({"detail": "Réservation introuvable."}, status=404)
        driver = Driver.objects.filter(public_id=serializer.validated_data["driver_id"]).first()
        vehicle = Vehicle.objects.filter(public_id=serializer.validated_data["vehicle_id"]).first()
        if not driver or not vehicle:
            return Response({"detail": "Conducteur ou véhicule introuvable."}, status=404)
        assignment = assign_driver(booking_id=booking.pk, driver_id=driver.pk, vehicle_id=vehicle.pk, actor=request.user, allow_override=serializer.validated_data["allow_override"], override_reason=serializer.validated_data.get("override_reason", ""), correlation_id=getattr(request, "correlation_id", ""))
        return Response(DriverAssignmentSerializer(assignment).data, status=status.HTTP_201_CREATED)


@method_decorator(csrf_protect, name="dispatch")
class UnassignmentActionView(APIView):
    permission_classes = (StaffOperationPermission,)
    required_permission = "operations.change_driverassignment"
    throttle_scope = "operations_mutation"

    def post(self, request, public_id):
        serializer = UnassignmentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = DriverAssignment.objects.filter(public_id=public_id).first()
        if not assignment:
            return Response({"detail": "Affectation introuvable."}, status=404)
        assignment = unassign_driver(assignment_id=assignment.pk, actor=request.user, reason=serializer.validated_data.get("reason", ""), correlation_id=getattr(request, "correlation_id", ""))
        return Response(DriverAssignmentSerializer(assignment).data)


class BookingAuditView(APIView):
    permission_classes = (StaffOperationPermission,)
    required_permission = "operations.view_auditevent"
    throttle_scope = "operations_read"

    def get(self, request, public_id):
        booking = Booking.objects.filter(public_id=public_id).first()
        if not booking:
            return Response({"detail": "Réservation introuvable."}, status=404)
        content_type = ContentType.objects.get_for_model(booking, for_concrete_model=False)
        events = AuditEvent.objects.filter(content_type=content_type, object_id=str(booking.pk))
        return Response(AuditEventSerializer(events[:200], many=True).data)


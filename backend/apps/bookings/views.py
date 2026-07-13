from __future__ import annotations

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Booking
from .serializers import (
    BookingCreateSerializer, BookingSerializer, CancellationSerializer,
    GuestAccessSerializer, TransitionSerializer,
)
from .services import (
    BookingUnavailable, can_access, cancel_booking, create_booking,
    transition_booking, verify_guest_access,
)


class BookingCreateView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "booking_create"

    @extend_schema(request=BookingCreateSerializer, responses={201: BookingSerializer})
    def post(self, request):
        serializer = BookingCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking, token, duplicate = create_booking(
            serializer.validated_data, user=request.user if request.user.is_authenticated else None,
            idempotency_key=request.headers.get("Idempotency-Key", ""),
            correlation_id=getattr(request, "correlation_id", ""),
        )
        payload = BookingSerializer(booking).data
        payload["management_token"] = token
        payload["idempotent_replay"] = duplicate
        return Response(payload, status=status.HTTP_200_OK if duplicate else status.HTTP_201_CREATED)


class BookingGuestAccessView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "booking_access"

    @extend_schema(request=GuestAccessSerializer, responses=BookingSerializer)
    def post(self, request):
        serializer = GuestAccessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = verify_guest_access(serializer.validated_data["reference"], serializer.validated_data["management_token"])
        return Response(BookingSerializer(booking).data)


class MyBookingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(customer=request.user).select_related("airport", "service_area").prefetch_related("price_snapshot__lines", "status_history")
        return Response(BookingSerializer(bookings, many=True).data)


class BookingDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, public_id):
        try:
            booking = Booking.objects.select_related("airport", "service_area", "customer").prefetch_related("price_snapshot__lines", "status_history", "notes").get(public_id=public_id)
        except Booking.DoesNotExist:
            return Response({"detail": "Réservation introuvable."}, status=404)
        token = request.headers.get("X-Booking-Token", "")
        if not can_access(booking, user=request.user, raw_token=token):
            return Response({"detail": "Réservation introuvable."}, status=404)
        return Response(BookingSerializer(booking, context={"is_staff": request.user.is_staff}).data)


@method_decorator(csrf_protect, name="dispatch")
class BookingCancelView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "booking_mutation"

    @extend_schema(request=CancellationSerializer, responses=BookingSerializer)
    def post(self, request, public_id):
        serializer = CancellationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = Booking.objects.get(public_id=public_id)
        except Booking.DoesNotExist:
            return Response({"detail": "Réservation introuvable."}, status=404)
        booking = cancel_booking(
            booking.pk, actor=request.user if request.user.is_authenticated else None,
            raw_token=request.headers.get("X-Booking-Token", ""), reason=serializer.validated_data.get("reason", ""),
            idempotency_key=request.headers.get("Idempotency-Key", ""), correlation_id=getattr(request, "correlation_id", ""),
        )
        return Response(BookingSerializer(booking).data)


@method_decorator(csrf_protect, name="dispatch")
class BookingTransitionView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=TransitionSerializer, responses=BookingSerializer)
    def post(self, request, public_id):
        serializer = TransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            booking = Booking.objects.get(public_id=public_id)
            booking = transition_booking(booking.pk, serializer.validated_data["to_status"], actor=request.user, note=serializer.validated_data.get("note", ""), correlation_id=getattr(request, "correlation_id", ""))
        except Booking.DoesNotExist:
            return Response({"detail": "Réservation introuvable."}, status=404)
        return Response(BookingSerializer(booking, context={"is_staff": True}).data)

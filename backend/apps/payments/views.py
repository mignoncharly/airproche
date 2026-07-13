from __future__ import annotations

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.bookings.models import Booking
from apps.operations.permissions import StaffOperationPermission

from .serializers import CheckoutResponseSerializer, PaymentSerializer, RefundRequestSerializer, RefundSerializer
from .services import (
    PaymentUnavailable, create_checkout, payment_for_booking, process_stripe_event,
    reconcile_payment, request_refund,
)
from .stripe_adapter import StripeConfigurationError, StripeProviderError, verify_signature


class PaymentCheckoutView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "payment_create"

    @method_decorator(csrf_protect)
    @extend_schema(responses={201: CheckoutResponseSerializer})
    def post(self, request, booking_public_id):
        payment, attempt, checkout_url = create_checkout(
            booking_public_id,
            user=request.user if request.user.is_authenticated else None,
            raw_token=request.headers.get("X-Booking-Token", ""),
            idempotency_key=request.headers.get("Idempotency-Key", ""),
        )
        return Response({"checkout_url": checkout_url, "payment": PaymentSerializer(payment).data, "payment_attempt_id": attempt.pk, "idempotent_replay": False}, status=status.HTTP_201_CREATED)


class BookingPaymentStatusView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "payment_status"

    def get(self, request, booking_public_id):
        try:
            booking = Booking.objects.get(public_id=booking_public_id)
        except Booking.DoesNotExist:
            return Response({"detail": "Réservation introuvable."}, status=404)
        payment = payment_for_booking(
            booking, user=request.user if request.user.is_authenticated else None,
            raw_token=request.headers.get("X-Booking-Token", ""), session_id=request.headers.get("X-Checkout-Session", ""),
        )
        return Response(PaymentSerializer(payment).data)


class PaymentReconcileView(APIView):
    permission_classes = [StaffOperationPermission]
    required_permission = "payments.change_payment"
    throttle_scope = "payment_staff"

    @method_decorator(csrf_protect)
    def post(self, request, public_id):
        payment = reconcile_payment(public_id, actor=request.user)
        return Response(PaymentSerializer(payment).data)


class PaymentRefundView(APIView):
    permission_classes = [StaffOperationPermission]
    required_permission = "payments.add_refund"
    throttle_scope = "payment_staff"

    @method_decorator(csrf_protect)
    @extend_schema(request=RefundRequestSerializer, responses=RefundSerializer)
    def post(self, request, public_id):
        serializer = RefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        refund = request_refund(
            public_id, amount=serializer.validated_data.get("amount"), reason=serializer.validated_data.get("reason", ""),
            idempotency_key=request.headers.get("Idempotency-Key", ""), actor=request.user,
        )
        return Response(RefundSerializer(refund).data, status=status.HTTP_201_CREATED)


class StripeWebhookView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_scope = "payment_webhook"

    def post(self, request):
        try:
            event = verify_signature(request.body, request.headers.get("Stripe-Signature", ""))
            outcome = process_stripe_event(event)
        except (StripeConfigurationError, StripeProviderError) as exc:
            if getattr(exc, "code", "") == "invalid_signature":
                return Response({"error": {"code": "invalid_signature", "message": "Signature invalide."}}, status=400)
            return Response({"error": {"code": getattr(exc, "code", "stripe_webhook_error"), "message": "Webhook Stripe non traité."}}, status=503)
        return Response({"received": True, "outcome": outcome})

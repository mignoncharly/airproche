from __future__ import annotations

from html import escape

from django.http import HttpResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.serializers import SerializerMethodField
from rest_framework.views import APIView

from apps.payments.models import Payment

from .models import Booking
from .serializers import BookingSerializer
from .services import can_access


class CustomerBookingSerializer(BookingSerializer):
    payment_status = SerializerMethodField()
    payment_environment = SerializerMethodField()
    is_upcoming = SerializerMethodField()

    class Meta(BookingSerializer.Meta):
        fields = BookingSerializer.Meta.fields + (
            "payment_status", "payment_environment", "is_upcoming",
        )

    def _payment(self, obj):
        try:
            return obj.payment
        except Payment.DoesNotExist:
            return None

    def get_payment_status(self, obj):
        payment = self._payment(obj)
        return payment.status if payment else "not_created"

    def get_payment_environment(self, obj):
        payment = self._payment(obj)
        return payment.environment if payment else None

    def get_is_upcoming(self, obj):
        return obj.pickup_at >= timezone.now() and obj.status not in {
            Booking.Status.CANCELLED, Booking.Status.COMPLETED, Booking.Status.NO_SHOW,
        }


class CustomerBookingListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=CustomerBookingSerializer(many=True))
    def get(self, request):
        bookings = Booking.objects.filter(customer=request.user).select_related(
            "airport", "service_area", "payment"
        ).prefetch_related("price_snapshot__lines", "status_history", "notes")
        status_filter = request.query_params.get("status")
        if status_filter:
            bookings = bookings.filter(status=status_filter)
        return Response(CustomerBookingSerializer(bookings, many=True, context={"is_staff": False}).data)


@method_decorator(never_cache, name="dispatch")
class BookingReceiptView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, public_id):
        try:
            booking = Booking.objects.select_related("airport", "service_area", "customer", "payment").get(public_id=public_id)
        except (Booking.DoesNotExist, Payment.DoesNotExist):
            try:
                booking = Booking.objects.select_related("airport", "service_area", "customer").get(public_id=public_id)
            except Booking.DoesNotExist:
                return HttpResponse("Not found", status=404, content_type="text/plain")
        token = request.headers.get("X-Booking-Token", "")
        if not can_access(
            booking, user=request.user, raw_token=token,
            staff_permission="bookings.view_booking",
        ):
            return HttpResponse("Not found", status=404, content_type="text/plain")
        payment = getattr(booking, "payment", None)
        payment_status = payment.status if payment else "not_created"
        payment_reference = payment.payment_intent_id if payment and payment.payment_intent_id else ""
        date = timezone.localtime(booking.pickup_at).strftime("%d/%m/%Y %H:%M")
        body = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>Reçu {escape(booking.reference)}</title>
<style>body{{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;padding:0 20px;color:#0f172a}}header{{border-bottom:2px solid #0f172a;margin-bottom:28px}}dl{{display:grid;grid-template-columns:180px 1fr;gap:10px;border-top:1px solid #cbd5e1;padding-top:18px}}dt{{color:#475569}}dd{{margin:0;font-weight:700}}.notice{{background:#f1f5f9;padding:14px;margin-top:28px;font-size:14px}}</style></head>
<body><header><h1>Reçu de réservation</h1><p>Référence : <strong>{escape(booking.reference)}</strong></p></header>
<dl><dt>Trajet</dt><dd>{escape(booking.airport.iata_code)} · {escape(booking.service_area.name)}</dd>
<dt>Prise en charge</dt><dd>{escape(date)}</dd><dt>Passager</dt><dd>{escape(booking.passenger_first_name)} {escape(booking.passenger_last_name)}</dd>
<dt>Contact</dt><dd>{escape(booking.booker_email)}</dd><dt>Statut réservation</dt><dd>{escape(booking.get_status_display())}</dd>
<dt>Statut paiement</dt><dd>{escape(payment_status)}</dd><dt>Total</dt><dd>{escape(str(booking.total_amount))} {escape(booking.currency)}</dd>
<dt>Référence paiement</dt><dd>{escape(payment_reference or "—")}</dd></dl>
<p class="notice">Ce document est un reçu de réservation et de paiement, pas une facture fiscale. Les informations de TVA et de facturation restent soumises à la décision comptable de l’entreprise.</p></body></html>"""
        response = HttpResponse(body, content_type="text/html; charset=utf-8")
        response["Content-Disposition"] = f'inline; filename="receipt-{booking.reference}.html"'
        response["X-Robots-Tag"] = "noindex, nofollow"
        response["Cache-Control"] = "no-store"
        return response

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, PermissionDenied

from apps.content.models import BusinessSettings, LegalDocument
from apps.notifications.services import enqueue_booking_notification

from .models import (
    AddressSnapshot, Booking, BookingStatusHistory, CancellationPolicySnapshot,
    ContactSnapshot, GuestAccessToken, IdempotencyRecord, PriceLine, PriceSnapshot,
)

logger = logging.getLogger(__name__)


class BookingUnavailable(APIException):
    status_code = 422
    default_detail = "La rÃ©servation nâ€™est pas disponible pour le moment."
    default_code = "booking_unavailable"


class BookingConflict(APIException):
    status_code = 409
    default_detail = "Cette demande de rÃ©servation est en conflit avec une autre demande."
    default_code = "booking_conflict"


def token_digest(raw: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), raw.encode(), hashlib.sha256).hexdigest()


def _reference() -> str:
    return f"TR-{secrets.token_hex(5).upper()}"


def _policy(now, pickup_at):
    document = (
        LegalDocument.objects.filter(
            kind=LegalDocument.Kind.CANCELLATION,
            is_published=True,
            effective_at__lte=now,
        ).order_by("-effective_at").first()
    )
    deadline = pickup_at - timedelta(hours=BusinessSettings.load().cancellation_deadline_hours)
    if document:
        return document.version, document.body, deadline
    return "unpublished", "La politique dâ€™annulation doit Ãªtre confirmÃ©e par lâ€™opÃ©rateur.", deadline


def _canonical_hash(data: dict) -> str:
    encoded = json.dumps(data, sort_keys=True, default=str, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def _booking_queryset():
    return Booking.objects.select_related("airport", "service_area", "customer").prefetch_related(
        "price_snapshot__lines", "status_history", "notes"
    )


@transaction.atomic
def create_booking(data: dict, *, user=None, idempotency_key: str = "", correlation_id: str = ""):
    now = timezone.now()
    request_hash = _canonical_hash(data)
    if idempotency_key:
        if len(idempotency_key) > 128:
            raise BookingConflict("La clÃ© dâ€™idempotence est trop longue.")
        existing = IdempotencyRecord.objects.select_for_update().filter(
            scope="booking-create", key=idempotency_key, expires_at__gt=now
        ).first()
        if existing:
            if existing.request_hash != request_hash:
                raise BookingConflict("Cette clÃ© dâ€™idempotence a dÃ©jÃ  Ã©tÃ© utilisÃ©e avec une autre demande.")
            booking = _booking_queryset().get(pk=existing.booking_id)
            return booking, None, True

    business = BusinessSettings.load()
    if not business.booking_enabled:
        raise BookingUnavailable("Les rÃ©servations en ligne ne sont pas encore ouvertes.", code="booking_closed")

    try:
        quote = (
            data.get("quote")
            or __import__("apps.pricing.models", fromlist=["Quote"]).Quote.objects.select_for_update()
            .select_related("airport", "service_area").prefetch_related("lines")
            .get(public_id=data["quote_id"])
        )
    except Exception as exc:
        raise BookingUnavailable("Le devis demandÃ© nâ€™existe plus.", code="quote_not_found") from exc
    if quote.expires_at <= now or quote.status != "valid":
        raise BookingUnavailable("Le devis a expirÃ©. Demandez une nouvelle estimation.", code="quote_expired")
    if data["booking_type"] != quote.trip_type:
        raise BookingConflict("Le type de trajet ne correspond plus au devis.", code="quote_mismatch")

    total_people = data["adult_count"] + data["child_count"]
    if total_people != quote.passenger_count or data.get("luggage_count", quote.luggage_count) != quote.luggage_count:
        raise BookingConflict("Les capacitÃ©s ne correspondent plus au devis.", code="quote_mismatch")
    passenger_same = data.get("passenger_same_as_booker", True)
    passenger_first = data.get("passenger_first_name") or data["booker_first_name"]
    passenger_last = data.get("passenger_last_name") or data["booker_last_name"]
    raw_token = secrets.token_urlsafe(32)
    booking = Booking.objects.create(
        reference=_reference(), quote=quote, customer=user,
        source=Booking.Source.ACCOUNT if user else Booking.Source.GUEST,
        booking_type=data["booking_type"], airport=quote.airport, service_area=quote.service_area,
        pickup_address=data.get("pickup_address", ""), destination_address=data.get("destination_address", ""),
        pickup_locality=data.get("pickup_locality", ""), destination_locality=data.get("destination_locality", ""),
        pickup_at=quote.pickup_at, flight_number=data.get("flight_number", ""), airline=data.get("airline", ""),
        origin_city_country=data.get("origin_city_country", ""), terminal=data.get("terminal", ""),
        meeting_information=data.get("meeting_information", ""), passenger_count=quote.passenger_count,
        adult_count=data["adult_count"], child_count=data["child_count"], luggage_count=quote.luggage_count,
        oversized_luggage_count=data.get("oversized_luggage_count", 0), accessibility_request=data.get("accessibility_request", False),
        accessibility_details=data.get("accessibility_details", ""), additional_requirements=data.get("additional_requirements", ""),
        passenger_same_as_booker=passenger_same, booker_first_name=data["booker_first_name"], booker_last_name=data["booker_last_name"],
        booker_email=data["booker_email"], booker_phone=data["booker_phone"], booker_whatsapp=data.get("booker_whatsapp", ""),
        passenger_first_name=passenger_first, passenger_last_name=passenger_last,
        passenger_phone=data.get("passenger_phone") or data["booker_phone"], passenger_whatsapp=data.get("passenger_whatsapp", ""),
        passenger_locale=data.get("passenger_locale", "fr"), status=Booking.Status.PENDING_PAYMENT,
        total_amount=quote.total_amount, currency=quote.currency, terms_accepted_at=now, privacy_accepted_at=now,
        cancellation_deadline=_policy(now, quote.pickup_at)[2],
    )
    AddressSnapshot.objects.bulk_create([
        AddressSnapshot(booking=booking, kind=AddressSnapshot.Kind.PICKUP, formatted_address=booking.pickup_address, locality=booking.pickup_locality),
        AddressSnapshot(booking=booking, kind=AddressSnapshot.Kind.DESTINATION, formatted_address=booking.destination_address, locality=booking.destination_locality),
    ])
    ContactSnapshot.objects.bulk_create([
        ContactSnapshot(booking=booking, kind=ContactSnapshot.Kind.BOOKER, first_name=booking.booker_first_name, last_name=booking.booker_last_name, email=booking.booker_email, phone=booking.booker_phone, whatsapp=booking.booker_whatsapp),
        ContactSnapshot(booking=booking, kind=ContactSnapshot.Kind.PASSENGER, first_name=booking.passenger_first_name, last_name=booking.passenger_last_name, phone=booking.passenger_phone, whatsapp=booking.passenger_whatsapp, preferred_locale=booking.passenger_locale),
    ])
    snapshot = PriceSnapshot.objects.create(booking=booking, calculation_version=quote.calculation_version, total_amount=quote.total_amount, currency=quote.currency)
    PriceLine.objects.bulk_create([PriceLine(snapshot=snapshot, code=line.code, label=line.label, quantity=line.quantity, unit_amount=line.unit_amount, total_amount=line.total_amount, display_order=line.display_order) for line in quote.lines.all()])
    policy_version, policy_text, deadline = _policy(now, quote.pickup_at)
    CancellationPolicySnapshot.objects.create(booking=booking, version=policy_version, text=policy_text, deadline=deadline)
    BookingStatusHistory.objects.create(booking=booking, to_status=booking.status, actor=user, correlation_id=correlation_id)
    GuestAccessToken.objects.create(booking=booking, token_digest=token_digest(raw_token), expires_at=now + timedelta(days=30))
    if idempotency_key:
        IdempotencyRecord.objects.create(scope="booking-create", key=idempotency_key, request_hash=request_hash, booking=booking, response_status=201, expires_at=now + timedelta(days=2))
    enqueue_booking_notification(booking.pk, "created", created=True)
    return _booking_queryset().get(pk=booking.pk), raw_token, False


@transaction.atomic
def verify_guest_access(reference: str, raw_token: str):
    try:
        token = GuestAccessToken.objects.select_for_update().select_related("booking").get(
            booking__reference=reference.upper(), purpose=GuestAccessToken.Purpose.MANAGE,
            token_digest=token_digest(raw_token),
        )
    except GuestAccessToken.DoesNotExist as exc:
        raise NotFound("Cette rÃ©servation nâ€™est pas accessible avec ces informations.") from exc
    now = timezone.now()
    if token.revoked_at or token.expires_at <= now:
        raise NotFound("Cette rÃ©servation nâ€™est pas accessible avec ces informations.")
    token.last_used_at = now
    token.save(update_fields=("last_used_at",))
    return _booking_queryset().get(pk=token.booking_id)


def can_access(booking, *, user=None, raw_token="") -> bool:
    if user and user.is_authenticated and (user.is_staff or booking.customer_id == user.pk):
        return True
    if not raw_token:
        return False
    try:
        verify_guest_access(booking.reference, raw_token)
        return True
    except (NotFound, PermissionDenied):
        return False


ALLOWED_TRANSITIONS = {
    Booking.Status.DRAFT: {Booking.Status.PENDING_PAYMENT},
    Booking.Status.PENDING_PAYMENT: {Booking.Status.CONFIRMED, Booking.Status.CANCELLED},
    Booking.Status.CONFIRMED: {Booking.Status.DRIVER_ASSIGNMENT_PENDING, Booking.Status.CANCELLED},
    Booking.Status.DRIVER_ASSIGNMENT_PENDING: {Booking.Status.DRIVER_ASSIGNED, Booking.Status.CANCELLED},
    Booking.Status.DRIVER_ASSIGNED: {Booking.Status.PASSENGER_CONTACTED, Booking.Status.DRIVER_EN_ROUTE, Booking.Status.CANCELLED},
    Booking.Status.PASSENGER_CONTACTED: {Booking.Status.DRIVER_EN_ROUTE, Booking.Status.CANCELLED},
    Booking.Status.DRIVER_EN_ROUTE: {Booking.Status.DRIVER_ARRIVED},
    Booking.Status.DRIVER_ARRIVED: {Booking.Status.PASSENGER_PICKED_UP, Booking.Status.NO_SHOW},
    Booking.Status.PASSENGER_PICKED_UP: {Booking.Status.IN_PROGRESS},
    Booking.Status.IN_PROGRESS: {Booking.Status.COMPLETED},
}


@transaction.atomic
def transition_booking(booking_id, to_status: str, *, actor=None, note="", correlation_id=""):
    booking = Booking.objects.select_for_update().get(pk=booking_id)
    if to_status not in ALLOWED_TRANSITIONS.get(booking.status, set()):
        raise BookingConflict("Cette transition de rÃ©servation nâ€™est pas autorisÃ©e.", code="invalid_transition")
    old_status = booking.status
    booking.status = to_status
    if to_status == Booking.Status.CANCELLED:
        booking.cancelled_at = timezone.now()
    booking.save(update_fields=("status", "cancelled_at", "updated_at"))
    history = BookingStatusHistory.objects.create(booking=booking, from_status=old_status, to_status=to_status, actor=actor, note=note, correlation_id=correlation_id)
    enqueue_booking_notification(booking.pk, f"status:{history.pk}")
    return _booking_queryset().get(pk=booking.pk)


@transaction.atomic
def cancel_booking(booking_id, *, actor=None, raw_token="", reason="", idempotency_key="", correlation_id=""):
    booking = Booking.objects.select_for_update().get(pk=booking_id)
    if not can_access(booking, user=actor, raw_token=raw_token):
        raise PermissionDenied("Vous nâ€™Ãªtes pas autorisÃ© Ã  gÃ©rer cette rÃ©servation.")
    if booking.status not in {Booking.Status.PENDING_PAYMENT, Booking.Status.CONFIRMED, Booking.Status.DRIVER_ASSIGNMENT_PENDING, Booking.Status.DRIVER_ASSIGNED}:
        raise BookingConflict("Cette rÃ©servation ne peut plus Ãªtre annulÃ©e.", code="cancellation_unavailable")
    if not (actor and actor.is_staff) and booking.cancellation_deadline and timezone.now() >= booking.cancellation_deadline:
        raise BookingConflict("Le dÃ©lai dâ€™annulation est dÃ©passÃ©.", code="cancellation_deadline")
    old_status = booking.status
    booking.status = Booking.Status.CANCELLED
    booking.cancelled_at = timezone.now()
    booking.cancellation_reason = reason
    booking.cancellation_outcome = "eligible"
    booking.save(update_fields=("status", "cancelled_at", "cancellation_reason", "cancellation_outcome", "updated_at"))
    history = BookingStatusHistory.objects.create(booking=booking, from_status=old_status, to_status=booking.status, actor=actor, note=reason, correlation_id=correlation_id)
    enqueue_booking_notification(booking.pk, f"status:{history.pk}")
    return _booking_queryset().get(pk=booking.pk)

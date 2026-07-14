from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from urllib.parse import quote

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound

from apps.bookings.models import Booking, BookingStatusHistory
from apps.bookings.services import can_access
from apps.notifications.services import enqueue_booking_notification

from .models import Payment, PaymentAttempt, Refund, WebhookEvent
from .stripe_adapter import (
    StripeConfigurationError, StripeProviderError, create_checkout_session,
    create_refund, redacted_event_payload, retrieve_checkout_session,
)


CENT = Decimal("0.01")


class PaymentUnavailable(APIException):
    status_code = 422
    default_detail = "Le paiement en ligne n’est pas disponible pour le moment."
    default_code = "payment_unavailable"


class PaymentConflict(APIException):
    status_code = 409
    default_detail = "Cette opération de paiement est en conflit avec un autre état."
    default_code = "payment_conflict"


class PaymentMismatch(Exception):
    pass


def _environment() -> str:
    from .stripe_adapter import configuration
    try:
        return configuration()["environment"]
    except StripeConfigurationError as exc:
        raise PaymentUnavailable(str(exc), code="stripe_not_configured") from exc


def _minor(amount: Decimal) -> int:
    return int((amount.quantize(CENT, rounding=ROUND_HALF_UP) * 100).to_integral_value())


def _payment_queryset():
    return Payment.objects.select_related("booking", "booking__airport", "booking__service_area").prefetch_related("attempts", "refunds")


def _payment_payload(payment: Payment) -> dict:
    return {
        "public_id": str(payment.public_id), "booking_public_id": str(payment.booking.public_id),
        "booking_reference": payment.booking.reference, "status": payment.status,
        "amount": str(payment.amount), "currency": payment.currency,
        "provider": payment.provider, "environment": payment.environment,
        "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        "last_error_code": payment.last_error_code or None,
        "last_error_message": payment.last_error_message or None,
    }


def payment_for_booking(booking, *, user=None, raw_token="", session_id="") -> Payment:
    if not can_access(booking, user=user, raw_token=raw_token, staff_permission="payments.view_payment"):
        if session_id:
            payment = Payment.objects.filter(booking=booking, checkout_session_id=session_id).first()
            if payment:
                return payment
        raise NotFound("Paiement introuvable.")
    try:
        return _payment_queryset().get(booking=booking)
    except Payment.DoesNotExist as exc:
        raise NotFound("Aucun paiement n’est associé à cette réservation.") from exc


@transaction.atomic
def create_checkout(booking_public_id, *, user=None, raw_token="", idempotency_key="") -> tuple[Payment, PaymentAttempt, str]:
    if not idempotency_key or len(idempotency_key) > 128:
        raise PaymentConflict("Une clé d’idempotence est obligatoire pour créer un paiement.", code="idempotency_required")
    try:
        existing_attempt = PaymentAttempt.objects.select_related("payment", "payment__booking").get(idempotency_key=idempotency_key)
    except PaymentAttempt.DoesNotExist:
        existing_attempt = None
    if existing_attempt:
        if existing_attempt.checkout_session_id and existing_attempt.payment.checkout_session_id:
            return existing_attempt.payment, existing_attempt, existing_attempt.checkout_url
        raise PaymentConflict("Cette clé d’idempotence correspond à une tentative incomplète.", code="idempotency_conflict")

    try:
        booking = Booking.objects.select_for_update().select_related("airport", "service_area").get(public_id=booking_public_id)
    except Booking.DoesNotExist as exc:
        raise NotFound("Réservation introuvable.") from exc
    if not can_access(booking, user=user, raw_token=raw_token, staff_permission="payments.add_payment"):
        raise NotFound("Réservation introuvable.")
    if booking.status != Booking.Status.PENDING_PAYMENT:
        raise PaymentConflict("Cette réservation n’attend pas un paiement en ligne.", code="booking_not_payable")

    environment = _environment()
    payment, _ = Payment.objects.select_for_update().get_or_create(
        booking=booking,
        defaults={"amount": booking.total_amount, "currency": booking.currency, "environment": environment},
    )
    if payment.amount != booking.total_amount or payment.currency != booking.currency or payment.environment != environment:
        payment.status = Payment.Status.MISMATCHED
        payment.save(update_fields=("status", "updated_at"))
        raise PaymentConflict("Le montant ou l’environnement du paiement ne correspond pas à la réservation.", code="payment_snapshot_mismatch")
    if payment.status == Payment.Status.PENDING and payment.checkout_session_id:
        latest = payment.attempts.order_by("-attempt_number").first()
        if latest and latest.checkout_url:
            return payment, latest, latest.checkout_url
    if payment.status == Payment.Status.SUCCEEDED:
        raise PaymentConflict("Cette réservation est déjà payée.", code="already_paid")
    if payment.status == Payment.Status.MISMATCHED:
        raise PaymentConflict("Ce paiement est isolé pour vérification opérateur.", code="payment_quarantined")
    attempt_number = (payment.attempts.order_by("-attempt_number").first().attempt_number if payment.attempts.exists() else 0) + 1
    attempt = PaymentAttempt.objects.create(payment=payment, attempt_number=attempt_number, idempotency_key=idempotency_key, status=PaymentAttempt.Status.CREATED)
    base = settings.APP_BASE_URL.rstrip("/")
    success_url = f"{base}/paiement/retour#booking={quote(str(booking.public_id))}&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{base}/paiement/retour#booking={quote(str(booking.public_id))}&cancelled=1"
    try:
        session = create_checkout_session(
            amount_minor=_minor(payment.amount), currency=payment.currency,
            booking_reference=booking.reference, booking_public_id=str(booking.public_id), payment_public_id=str(payment.public_id),
            customer_email=booking.booker_email, success_url=success_url, cancel_url=cancel_url,
            idempotency_key=idempotency_key,
        )
        session_id = session.get("id")
        checkout_url = session.get("url")
        if not session_id or not checkout_url:
            raise StripeProviderError("Stripe n’a pas renvoyé de session Checkout valide.", "invalid_checkout_response")
    except (StripeProviderError, StripeConfigurationError) as exc:
        attempt.status = PaymentAttempt.Status.FAILED
        attempt.failure_code = getattr(exc, "code", "stripe_error")
        attempt.failure_message = str(exc)[:300]
        attempt.save(update_fields=("status", "failure_code", "failure_message", "updated_at"))
        payment.status = Payment.Status.FAILED
        payment.last_error_code = attempt.failure_code
        payment.last_error_message = attempt.failure_message
        payment.save(update_fields=("status", "last_error_code", "last_error_message", "updated_at"))
        raise PaymentUnavailable("Le paiement n’a pas pu être initialisé.", code=attempt.failure_code) from exc
    attempt.status = PaymentAttempt.Status.PENDING
    attempt.checkout_session_id = session_id
    attempt.checkout_url = checkout_url
    attempt.save(update_fields=("status", "checkout_session_id", "checkout_url", "updated_at"))
    payment.status = Payment.Status.PENDING
    payment.checkout_session_id = session_id
    payment.payment_intent_id = session.get("payment_intent") or payment.payment_intent_id
    payment.last_error_code = ""
    payment.last_error_message = ""
    payment.save(update_fields=("status", "checkout_session_id", "payment_intent_id", "last_error_code", "last_error_message", "updated_at"))
    return _payment_queryset().get(pk=payment.pk), attempt, checkout_url


def _find_payment_for_event(obj: dict) -> Payment:
    metadata = obj.get("metadata") or {}
    payment_id = metadata.get("payment_public_id")
    session_id = obj.get("id")
    intent_id = obj.get("payment_intent") or obj.get("id")
    query = Payment.objects.select_for_update().select_related("booking")
    if payment_id:
        try:
            return query.get(public_id=payment_id)
        except (Payment.DoesNotExist, ValueError):
            pass
    payment = query.filter(checkout_session_id=session_id).first() or query.filter(payment_intent_id=intent_id).first()
    if not payment:
        raise PaymentMismatch("Événement Stripe sans paiement local correspondant.")
    return payment


@transaction.atomic
def apply_checkout_session(session: dict) -> tuple[Payment, str]:
    payment = _find_payment_for_event(session)
    expected_minor = _minor(payment.amount)
    actual_minor = session.get("amount_total")
    actual_currency = str(session.get("currency") or "").upper()
    metadata = session.get("metadata") or {}
    if session.get("id") != payment.checkout_session_id or actual_minor != expected_minor or actual_currency != payment.currency or metadata.get("booking_reference") != payment.booking.reference or metadata.get("environment") != payment.environment:
        payment.status = Payment.Status.MISMATCHED
        payment.last_error_code = "amount_currency_or_metadata_mismatch"
        payment.last_error_message = "Stripe event does not match the locked payment snapshot."
        payment.save(update_fields=("status", "last_error_code", "last_error_message", "updated_at"))
        raise PaymentMismatch("Le paiement Stripe ne correspond pas à la réservation.")
    if session.get("payment_status") != "paid":
        payment.status = Payment.Status.PENDING
        payment.save(update_fields=("status", "updated_at"))
        return payment, "pending"
    if payment.status in {
        Payment.Status.SUCCEEDED,
        Payment.Status.PARTIALLY_REFUNDED,
        Payment.Status.REFUNDED,
    }:
        return payment, "duplicate"
    if payment.status == Payment.Status.MISMATCHED:
        raise PaymentMismatch("Un paiement isolé nécessite une réconciliation opérateur.")
    now = timezone.now()
    payment.status = Payment.Status.SUCCEEDED
    payment.payment_intent_id = session.get("payment_intent") or payment.payment_intent_id
    payment.paid_at = now
    payment.last_error_code = ""
    payment.last_error_message = ""
    payment.save(update_fields=("status", "payment_intent_id", "paid_at", "last_error_code", "last_error_message", "updated_at"))
    payment.attempts.filter(checkout_session_id=session.get("id"), status=PaymentAttempt.Status.PENDING).update(status=PaymentAttempt.Status.SUCCEEDED, updated_at=now)
    booking = Booking.objects.select_for_update().get(pk=payment.booking_id)
    if booking.status == Booking.Status.PENDING_PAYMENT:
        old_status = booking.status
        booking.status = Booking.Status.CONFIRMED
        booking.save(update_fields=("status", "updated_at"))
        history = BookingStatusHistory.objects.create(booking=booking, from_status=old_status, to_status=booking.status, note="Paiement Stripe vérifié.")
        enqueue_booking_notification(booking.pk, f"status:{history.pk}")
        return payment, "confirmed"
    if booking.status == Booking.Status.CANCELLED:
        return payment, "paid_cancelled_booking"
    return payment, "paid_without_transition"


@transaction.atomic
def process_stripe_event(event: dict) -> str:
    from .stripe_adapter import configuration
    environment = configuration()["environment"]
    safe_payload = redacted_event_payload(event)
    webhook, created = WebhookEvent.objects.get_or_create(
        provider="stripe", environment=environment, provider_event_id=event["id"],
        defaults={"event_type": event["type"], "signature_valid": True, "payload": safe_payload},
    )
    if not created:
        webhook.attempts += 1
        webhook.save(update_fields=("attempts",))
        return "duplicate"
    obj = event.get("data", {}).get("object", {})
    try:
        if event["type"] == "checkout.session.completed":
            payment, outcome = apply_checkout_session(obj)
            webhook.payment = payment
            webhook.status = WebhookEvent.Status.QUARANTINED if outcome == "paid_cancelled_booking" else WebhookEvent.Status.PROCESSED
        elif event["type"] == "checkout.session.expired":
            payment = _find_payment_for_event(obj)
            webhook.payment = payment
            if payment.status in {
                Payment.Status.SUCCEEDED,
                Payment.Status.PARTIALLY_REFUNDED,
                Payment.Status.REFUNDED,
                Payment.Status.MISMATCHED,
            }:
                webhook.status = WebhookEvent.Status.IGNORED
            else:
                payment.status = Payment.Status.CANCELED
                payment.save(update_fields=("status", "updated_at"))
                payment.attempts.filter(
                    checkout_session_id=obj.get("id"),
                    status=PaymentAttempt.Status.PENDING,
                ).update(status=PaymentAttempt.Status.CANCELED, updated_at=timezone.now())
                webhook.status = WebhookEvent.Status.PROCESSED
        elif event["type"] == "payment_intent.payment_failed":
            payment = _find_payment_for_event(obj)
            webhook.payment = payment
            if payment.status in {
                Payment.Status.SUCCEEDED,
                Payment.Status.PARTIALLY_REFUNDED,
                Payment.Status.REFUNDED,
                Payment.Status.MISMATCHED,
            }:
                webhook.status = WebhookEvent.Status.IGNORED
            else:
                payment.status = Payment.Status.FAILED
                payment.last_error_code = (obj.get("last_payment_error") or {}).get("code", "payment_failed")
                payment.last_error_message = (
                    (obj.get("last_payment_error") or {}).get("message")
                    or "Le paiement Stripe a échoué."
                )[:300]
                payment.save(
                    update_fields=("status", "last_error_code", "last_error_message", "updated_at")
                )
                webhook.status = WebhookEvent.Status.PROCESSED
        elif event["type"] in {"charge.refunded", "refund.updated"}:
            webhook.status = WebhookEvent.Status.IGNORED
        else:
            webhook.status = WebhookEvent.Status.IGNORED
        webhook.processed_at = timezone.now()
        webhook.save(update_fields=("payment", "status", "processed_at"))
    except PaymentMismatch as exc:
        metadata = obj.get("metadata") or {}
        payment_id = metadata.get("payment_public_id")
        if payment_id:
            Payment.objects.filter(public_id=payment_id).update(
                status=Payment.Status.MISMATCHED,
                last_error_code="amount_currency_or_metadata_mismatch",
                last_error_message="Stripe event does not match the locked payment snapshot.",
                updated_at=timezone.now(),
            )
        webhook.status = WebhookEvent.Status.QUARANTINED
        webhook.failure_message = str(exc)[:300]
        webhook.processed_at = timezone.now()
        webhook.save(update_fields=("status", "failure_message", "processed_at"))
        return "quarantined"
    return webhook.status


@transaction.atomic
def reconcile_payment(payment_public_id, *, actor=None):
    try:
        payment = Payment.objects.select_for_update().select_related("booking").get(public_id=payment_public_id)
    except Payment.DoesNotExist as exc:
        raise NotFound("Paiement introuvable.") from exc
    if not payment.checkout_session_id:
        raise PaymentConflict("Aucune session Stripe n’est associée à ce paiement.", code="session_missing")
    try:
        session = retrieve_checkout_session(payment.checkout_session_id)
        payment, _ = apply_checkout_session(session)
    except (StripeProviderError, StripeConfigurationError) as exc:
        raise PaymentUnavailable("Stripe n’a pas pu être interrogé.", code=getattr(exc, "code", "stripe_error")) from exc
    return _payment_queryset().get(pk=payment.pk)


@transaction.atomic
def request_refund(payment_public_id, *, amount=None, reason="", idempotency_key="", actor=None) -> Refund:
    if not idempotency_key or len(idempotency_key) > 128:
        raise PaymentConflict("Une clé d’idempotence est obligatoire pour un remboursement.", code="idempotency_required")
    existing = Refund.objects.filter(idempotency_key=idempotency_key).select_related("payment").first()
    if existing:
        return existing
    try:
        payment = Payment.objects.select_for_update().get(public_id=payment_public_id)
    except Payment.DoesNotExist as exc:
        raise NotFound("Paiement introuvable.") from exc
    if payment.status not in {Payment.Status.SUCCEEDED, Payment.Status.PARTIALLY_REFUNDED} or not payment.payment_intent_id:
        raise PaymentConflict("Seul un paiement confirmé peut être remboursé.", code="payment_not_refundable")
    captured = payment.amount
    already_reserved = sum((refund.amount for refund in payment.refunds.select_for_update().filter(status__in=[Refund.Status.PENDING, Refund.Status.SUCCEEDED])), Decimal("0"))
    remaining = (captured - already_reserved).quantize(CENT)
    requested = remaining if amount is None else Decimal(str(amount)).quantize(CENT, rounding=ROUND_HALF_UP)
    if requested <= 0 or requested > remaining:
        raise PaymentConflict("Le montant du remboursement dépasse le montant disponible.", code="refund_amount_invalid")
    refund = Refund.objects.create(payment=payment, requested_by=actor, amount=requested, currency=payment.currency, reason=reason, idempotency_key=idempotency_key)
    try:
        response = create_refund(payment_intent_id=payment.payment_intent_id, amount_minor=_minor(requested), reason=reason, idempotency_key=idempotency_key)
        refund.provider_refund_id = response.get("id")
        if response.get("status") == "succeeded":
            refund.status = Refund.Status.SUCCEEDED
            refund.completed_at = timezone.now()
            new_total = already_reserved + requested
            payment.status = Payment.Status.REFUNDED if new_total >= captured else Payment.Status.PARTIALLY_REFUNDED
            payment.save(update_fields=("status", "updated_at"))
        else:
            refund.status = Refund.Status.PENDING
        refund.save(update_fields=("provider_refund_id", "status", "completed_at"))
    except (StripeProviderError, StripeConfigurationError) as exc:
        refund.status = Refund.Status.FAILED
        refund.failure_code = getattr(exc, "code", "stripe_error")
        refund.failure_message = str(exc)[:300]
        refund.save(update_fields=("status", "failure_code", "failure_message"))
        raise PaymentUnavailable("Stripe n’a pas pu créer le remboursement.", code=refund.failure_code) from exc
    return refund

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from collections.abc import Callable
from datetime import timedelta
from urllib.parse import quote

from django.conf import settings
from django.core.mail import send_mail
from django.core.validators import validate_email
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import APIException

from apps.bookings.models import Booking

from .models import ContactMessage, EmailDeliveryAttempt, EmailNotification

logger = logging.getLogger(__name__)


class IdempotencyConflict(APIException):
    status_code = 409
    default_code = "idempotency_conflict"
    default_detail = "Cette clé d’idempotence a déjà été utilisée pour une autre demande."


def _clean_line(value: object, limit: int = 200) -> str:
    text = str(value or "").strip()
    if any(character in text for character in ("\r", "\n", "\x00")):
        raise ValueError("Header control characters are forbidden.")
    return text[:limit]


def _booking_created(context: dict) -> tuple[str, str]:
    first_name = _clean_line(context.get("first_name"), 100)
    reference = _clean_line(context.get("reference"), 24)
    return (
        f"Réservation {reference} enregistrée",
        (
            f"Bonjour {first_name},\n\n"
            f"Votre réservation {reference} a bien été enregistrée. "
            "Vous pouvez suivre son statut depuis votre espace ou avec votre lien de gestion.\n\n"
            "L’équipe Airproche"
        ),
    )


def _booking_status(context: dict) -> tuple[str, str]:
    first_name = _clean_line(context.get("first_name"), 100)
    reference = _clean_line(context.get("reference"), 24)
    status_label = _clean_line(context.get("status_label"), 100)
    return (
        f"Mise à jour de la réservation {reference}",
        (
            f"Bonjour {first_name},\n\n"
            f"Le statut de votre réservation {reference} est maintenant : {status_label}.\n\n"
            "L’équipe Airproche"
        ),
    )


def _contact_received(context: dict) -> tuple[str, str]:
    first_name = _clean_line(context.get("first_name"), 100)
    return (
        "Nous avons reçu votre message",
        (
            f"Bonjour {first_name},\n\n"
            "Votre message a bien été transmis à notre équipe. "
            "Nous vous répondrons par les coordonnées fournies.\n\n"
            "L’équipe Airproche"
        ),
    )


def _inquiry_customer_ack(context: dict) -> tuple[str, str]:
    name = _clean_line(context.get("customer_name"), 180)
    driver = _clean_line(context.get("driver_name"), 180)
    reference = _clean_line(context.get("reference"), 24)
    airport = _clean_line(context.get("airport"), 180)
    destination = _clean_line(context.get("destination"), 300)
    travel_date = _clean_line(context.get("travel_date"), 80)
    return (
        f"Votre demande {reference} a été reçue par AirProche",
        f"Bonjour {name},\n\nVotre demande a été enregistrée et transmise à {driver}. "
        "Le trajet n’est pas encore confirmé. Le chauffeur vous contactera directement "
        "pour confirmer sa disponibilité, le tarif et les modalités.\n\n"
        f"Aéroport : {airport}\nTrajet : {destination}\nDate : {travel_date}\n"
        f"Référence : {reference}\n\nNe communiquez jamais de données bancaires par e-mail. "
        f"Consultez notre politique de confidentialité : {settings.APP_BASE_URL}/confidentialite\n"
        f"Signaler un abus : {settings.APP_BASE_URL}/contact\n\nL’équipe AirProche",
    )


def _inquiry_driver_new(context: dict) -> tuple[str, str]:
    driver = _clean_line(context.get("driver_name"), 180)
    reference = _clean_line(context.get("reference"), 24)
    airport = _clean_line(context.get("airport"), 180)
    destination = _clean_line(context.get("destination"), 300)
    return (
        f"Nouvelle demande AirProche {reference}",
        f"Bonjour {driver},\n\nUne nouvelle demande est disponible dans votre espace chauffeur.\n"
        f"Aéroport : {airport}\nTrajet : {destination}\nRéférence : {reference}\n\n"
        f"Consultez-la depuis {settings.APP_BASE_URL}/compte. Le tarif et la disponibilité "
        "doivent être confirmés directement avec le client.\n\nL’équipe AirProche",
    )


def _inquiry_status(context: dict) -> tuple[str, str]:
    name = _clean_line(context.get("customer_name"), 180)
    reference = _clean_line(context.get("reference"), 24)
    status_label = _clean_line(context.get("status_label"), 120)
    return (
        f"Mise à jour de votre demande {reference}",
        f"Bonjour {name},\n\nLe chauffeur a mis à jour votre demande : {status_label}. "
        "Cette mise à jour ne remplace pas la confirmation directe du tarif et des modalités.\n\n"
        "L’équipe AirProche",
    )


def _single_use_link_unavailable(context: dict) -> tuple[str, str]:
    raise ValueError("Single-use links are only rendered during their initial delivery.")


RENDERERS: dict[str, Callable[[dict], tuple[str, str]]] = {
    "account.verify.fr": _single_use_link_unavailable,
    "account.reset.fr": _single_use_link_unavailable,
    "booking.created.fr": _booking_created,
    "booking.status.fr": _booking_status,
    "contact.received.fr": _contact_received,
    "inquiry.customer_ack.fr": _inquiry_customer_ack,
    "inquiry.driver_new.fr": _inquiry_driver_new,
    "inquiry.status.fr": _inquiry_status,
}
TEMPLATE_KINDS = {
    "account.verify.fr": EmailNotification.Kind.VERIFY_EMAIL,
    "account.reset.fr": EmailNotification.Kind.RESET_PASSWORD,
    "booking.created.fr": EmailNotification.Kind.BOOKING_CREATED,
    "booking.status.fr": EmailNotification.Kind.BOOKING_STATUS,
    "contact.received.fr": EmailNotification.Kind.CONTACT_RECEIVED,
    "inquiry.customer_ack.fr": EmailNotification.Kind.INQUIRY_CUSTOMER_ACK,
    "inquiry.driver_new.fr": EmailNotification.Kind.INQUIRY_DRIVER_NEW,
    "inquiry.status.fr": EmailNotification.Kind.INQUIRY_STATUS,
}


def create_notification(
    *,
    kind: str,
    template_key: str,
    recipient_email: str,
    context: dict,
    idempotency_key: str,
    related_type: str = "",
    related_public_id=None,
    retryable: bool = True,
) -> tuple[EmailNotification, bool]:
    if template_key not in RENDERERS or TEMPLATE_KINDS[template_key] != kind:
        raise ValueError("Unknown notification template.")
    recipient = _clean_line(recipient_email, 254).lower()
    validate_email(recipient)
    notification, created = EmailNotification.objects.get_or_create(
        idempotency_key=idempotency_key,
        defaults={
            "kind": kind,
            "template_key": template_key,
            "recipient_email": recipient,
            "context": context,
            "related_type": related_type,
            "related_public_id": related_public_id,
            "retryable": retryable,
        },
    )
    return notification, created


def deliver_notification(
    notification_id: int,
    *,
    request_key: str,
    content_override: tuple[str, str] | None = None,
) -> EmailDeliveryAttempt:
    with transaction.atomic():
        notification = EmailNotification.objects.select_for_update().get(pk=notification_id)
        existing = EmailDeliveryAttempt.objects.filter(request_key=request_key).first()
        if existing:
            return existing
        attempt_number = notification.attempts.count() + 1
        now = timezone.now()
        try:
            subject, body = (
                content_override
                if content_override is not None
                else RENDERERS[notification.template_key](notification.context)
            )
            sent = send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [notification.recipient_email],
                fail_silently=False,
            )
            if sent != 1:
                raise RuntimeError("Email backend did not confirm one delivery.")
        except Exception as exc:
            logger.warning(
                "Email delivery failed",
                extra={
                    "event": "email_delivery_failed",
                    "notification_id": str(notification.public_id),
                    "error_code": type(exc).__name__,
                },
            )
            attempt = EmailDeliveryAttempt.objects.create(
                notification=notification,
                attempt_number=attempt_number,
                request_key=request_key,
                status=EmailDeliveryAttempt.Status.FAILED,
                error_code=type(exc).__name__[:80],
                error_message="The email provider did not accept the delivery."[:300],
            )
            notification.status = (
                EmailNotification.Status.FAILED
                if notification.retryable and attempt_number < notification.max_attempts
                else EmailNotification.Status.PERMANENT_FAILURE
            )
            notification.last_attempt_at = now
            notification.next_attempt_at = (
                now + timedelta(minutes=2**attempt_number)
                if notification.status == EmailNotification.Status.RETRYING
                else None
            )
            notification.error_category = type(exc).__name__[:80]
            notification.safe_error_summary = (
                "Le fournisseur de messagerie n’a pas accepté l’envoi."
            )
            notification.save(
                update_fields=(
                    "status",
                    "last_attempt_at",
                    "next_attempt_at",
                    "error_category",
                    "safe_error_summary",
                    "updated_at",
                )
            )
            return attempt

        attempt = EmailDeliveryAttempt.objects.create(
            notification=notification,
            attempt_number=attempt_number,
            request_key=request_key,
            status=EmailDeliveryAttempt.Status.SENT,
            provider_response="accepted",
        )
        notification.status = EmailNotification.Status.SENT
        notification.sent_at = now
        notification.delivered_at = now
        notification.last_attempt_at = now
        notification.next_attempt_at = None
        notification.provider_identifier = attempt.request_key
        notification.error_category = ""
        notification.safe_error_summary = ""
        notification.save(
            update_fields=(
                "status",
                "sent_at",
                "delivered_at",
                "last_attempt_at",
                "next_attempt_at",
                "provider_identifier",
                "error_category",
                "safe_error_summary",
                "updated_at",
            )
        )
        return attempt


def create_and_deliver(**kwargs) -> tuple[EmailNotification, bool]:
    notification, created = create_notification(**kwargs)
    if created:
        deliver_notification(notification.pk, request_key=f"initial:{notification.public_id}")
        notification.refresh_from_db()
    return notification, not created


def send_account_notification(user, raw_token: str, *, purpose: str) -> bool:
    first_name = _clean_line(user.first_name, 100)
    token_key = hmac.new(
        settings.SECRET_KEY.encode(), raw_token.encode(), hashlib.sha256
    ).hexdigest()
    if purpose == "verify_email":
        kind = EmailNotification.Kind.VERIFY_EMAIL
        template_key = "account.verify.fr"
        link = f"{settings.APP_BASE_URL}/verification-email#token={quote(raw_token)}"
        content = (
            "Bienvenue sur AirProche — confirmez votre adresse e-mail",
            (
                f"Bonjour {first_name},\n\n"
                "Bienvenue sur AirProche, la plateforme qui vous permet de trouver et de contacter des chauffeurs indépendants pour vos transferts depuis ou vers l’aéroport.\n\n"
                "Pour activer votre compte, confirmez votre adresse e-mail en cliquant sur le lien suivant. Ce lien est valable 24 heures et ne peut être utilisé qu’une seule fois :\n"
                f"{link}\n\n"
                "Après confirmation, vous pourrez gérer votre compte et, si vous êtes chauffeur, préparer votre profil public pour examen. AirProche ne confirme pas les trajets et ne perçoit pas le paiement du transport : ces éléments sont convenus directement avec le chauffeur.\n\n"
                "Si vous n’êtes pas à l’origine de cette inscription, aucune action n’est requise. Contactez-nous depuis la page Contact d’AirProche si nécessaire.\n\nL’équipe AirProche."
            ),
        )
    elif purpose == "reset_password":
        kind = EmailNotification.Kind.RESET_PASSWORD
        template_key = "account.reset.fr"
        link = f"{settings.APP_BASE_URL}/reinitialiser-mot-de-passe#token={quote(raw_token)}"
        content = (
            "Réinitialisez votre mot de passe",
            (
                f"Bonjour {first_name},\n\n"
                "Bienvenue sur AirProche, la plateforme qui vous permet de trouver et de contacter des chauffeurs indépendants pour vos transferts depuis ou vers l’aéroport.\n\n"
                "Choisissez un nouveau mot de passe avec ce lien valable une heure :\n"
                f"{link}\n\n"
                "Si vous n’avez pas demandé ce changement, ignorez ce message."
            ),
        )
    else:
        raise ValueError("Unknown account notification purpose.")
    notification, created = create_notification(
        kind=kind,
        template_key=template_key,
        recipient_email=user.email,
        context={"first_name": first_name},
        idempotency_key=f"account:{user.public_id}:{purpose}:{token_key}",
        related_type="account",
        related_public_id=user.public_id,
        retryable=False,
    )
    if created:
        deliver_notification(
            notification.pk,
            request_key=f"initial:{notification.public_id}",
            content_override=content,
        )
        notification.refresh_from_db()
    return notification.status == EmailNotification.Status.SENT


def retry_notification(notification: EmailNotification, *, idempotency_key: str):
    if not idempotency_key or len(idempotency_key) > 128:
        raise IdempotencyConflict("Une clé d’idempotence valide est obligatoire.")
    if not notification.retryable:
        raise IdempotencyConflict(
            "Ce message contient un lien à usage unique. Demandez plutôt un nouveau lien."
        )
    return deliver_notification(
        notification.pk,
        request_key=f"retry:{notification.public_id}:{idempotency_key}",
    )


def enqueue_inquiry_notifications(inquiry_id: int) -> None:
    def callback():
        from apps.operations.models import DriverInquiry, InquiryStatusHistory

        inquiry = DriverInquiry.objects.select_related("driver__user", "airport").get(pk=inquiry_id)
        context = {
            "customer_name": inquiry.customer_name,
            "driver_name": inquiry.driver.display_name,
            "reference": inquiry.reference,
            "airport": inquiry.airport.name,
            "destination": inquiry.destination,
            "travel_date": inquiry.pickup_at.isoformat() if inquiry.pickup_at else "À convenir",
        }
        customer, _ = create_and_deliver(
            kind=EmailNotification.Kind.INQUIRY_CUSTOMER_ACK,
            template_key="inquiry.customer_ack.fr",
            recipient_email=inquiry.customer_email,
            context=context,
            idempotency_key=f"inquiry:{inquiry.public_id}:customer-ack",
            related_type="driver_inquiry",
            related_public_id=inquiry.public_id,
        )
        driver_email = inquiry.driver.professional_email or inquiry.driver.user.email
        driver, _ = create_and_deliver(
            kind=EmailNotification.Kind.INQUIRY_DRIVER_NEW,
            template_key="inquiry.driver_new.fr",
            recipient_email=driver_email,
            context=context,
            idempotency_key=f"inquiry:{inquiry.public_id}:driver-new",
            related_type="driver_inquiry",
            related_public_id=inquiry.public_id,
        )
        if (
            driver.status == EmailNotification.Status.SENT
            and inquiry.status == DriverInquiry.Status.NEW
        ):
            inquiry.status = DriverInquiry.Status.NOTIFIED
            inquiry.save(update_fields=("status", "updated_at"))
            InquiryStatusHistory.objects.create(
                inquiry=inquiry,
                from_status=DriverInquiry.Status.NEW,
                to_status=DriverInquiry.Status.NOTIFIED,
            )
        logger.info(
            "Marketplace inquiry delivery completed",
            extra={
                "event": "marketplace_inquiry_delivery",
                "inquiry_id": str(inquiry.public_id),
                "customer_status": customer.status,
                "driver_status": driver.status,
            },
        )

    transaction.on_commit(callback, robust=True)


def enqueue_booking_notification(booking_id: int, event_key: str, *, created=False) -> None:
    def callback():
        booking = Booking.objects.get(pk=booking_id)
        status_label = Booking.Status(booking.status).label
        create_and_deliver(
            kind=(
                EmailNotification.Kind.BOOKING_CREATED
                if created
                else EmailNotification.Kind.BOOKING_STATUS
            ),
            template_key="booking.created.fr" if created else "booking.status.fr",
            recipient_email=booking.booker_email,
            context={
                "first_name": booking.booker_first_name,
                "reference": booking.reference,
                "status": booking.status,
                "status_label": status_label,
            },
            idempotency_key=f"booking:{booking.public_id}:{event_key}",
            related_type="booking",
            related_public_id=booking.public_id,
        )

    transaction.on_commit(callback, robust=True)


def _canonical_hash(data: dict) -> str:
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def source_fingerprint(remote_addr: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(),
        (remote_addr or "unknown").encode(),
        hashlib.sha256,
    ).hexdigest()


@transaction.atomic
def create_contact_message(
    data: dict, *, idempotency_key: str = "", remote_addr: str = ""
) -> tuple[ContactMessage, bool]:
    if idempotency_key and len(idempotency_key) > 128:
        raise IdempotencyConflict("La clé d’idempotence est trop longue.")
    persisted = {
        key: data.get(key, "")
        for key in ("first_name", "last_name", "email", "phone", "topic", "message")
    }
    request_hash = _canonical_hash(persisted)
    if idempotency_key:
        existing = ContactMessage.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            if existing.request_hash != request_hash:
                raise IdempotencyConflict()
            return existing, True
    message = ContactMessage.objects.create(
        **persisted,
        idempotency_key=idempotency_key or None,
        request_hash=request_hash,
        source_fingerprint=source_fingerprint(remote_addr),
    )

    def confirmation():
        create_and_deliver(
            kind=EmailNotification.Kind.CONTACT_RECEIVED,
            template_key="contact.received.fr",
            recipient_email=message.email,
            context={"first_name": message.first_name},
            idempotency_key=f"contact:{message.public_id}:received",
            related_type="contact",
            related_public_id=message.public_id,
        )

    transaction.on_commit(confirmation, robust=True)
    return message, False

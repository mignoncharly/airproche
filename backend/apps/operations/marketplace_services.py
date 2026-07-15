from __future__ import annotations

import hashlib
import hmac
import json

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.notifications.models import EmailNotification
from apps.notifications.services import IdempotencyConflict, enqueue_inquiry_notifications

from .models import AuditEvent, DriverInquiry, InquiryConsent, InquiryStatusHistory

ALLOWED_TRANSITIONS = {
    DriverInquiry.Status.NEW: {DriverInquiry.Status.VIEWED, DriverInquiry.Status.SPAM},
    DriverInquiry.Status.NOTIFIED: {
        DriverInquiry.Status.VIEWED,
        DriverInquiry.Status.CONTACTED,
        DriverInquiry.Status.SPAM,
    },
    DriverInquiry.Status.VIEWED: {DriverInquiry.Status.CONTACTED, DriverInquiry.Status.SPAM},
    DriverInquiry.Status.CONTACTED: {
        DriverInquiry.Status.ACCEPTED,
        DriverInquiry.Status.DECLINED,
        DriverInquiry.Status.SPAM,
    },
    DriverInquiry.Status.ACCEPTED: {DriverInquiry.Status.CLOSED, DriverInquiry.Status.SPAM},
    DriverInquiry.Status.DECLINED: {DriverInquiry.Status.CLOSED, DriverInquiry.Status.SPAM},
    DriverInquiry.Status.CLOSED: {DriverInquiry.Status.ARCHIVED},
}


def _canonical_hash(data: dict) -> str:
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode()
    return hashlib.sha256(encoded).hexdigest()


def _fingerprint(remote_addr: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode(), (remote_addr or "unknown").encode(), hashlib.sha256
    ).hexdigest()


@transaction.atomic
def create_inquiry(
    *, driver, airport, data: dict, idempotency_key: str, remote_addr: str
) -> tuple[DriverInquiry, bool]:
    if not idempotency_key or len(idempotency_key) > 128:
        raise IdempotencyConflict("Une clé d’idempotence valide est obligatoire.")
    persisted = {
        key: data.get(key)
        for key in (
            "customer_name",
            "customer_email",
            "customer_phone",
            "customer_whatsapp",
            "preferred_contact_method",
            "whatsapp_consent",
            "direction",
            "destination",
            "pickup_at",
            "passenger_count",
            "luggage_count",
            "message",
        )
    }
    request_hash = _canonical_hash(persisted)
    existing = DriverInquiry.objects.filter(driver=driver, idempotency_key=idempotency_key).first()
    if existing:
        if existing.request_hash != request_hash:
            raise IdempotencyConflict()
        return existing, True

    inquiry = DriverInquiry.objects.create(
        driver=driver,
        airport=airport,
        **persisted,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        source_fingerprint=_fingerprint(remote_addr),
    )
    InquiryConsent.objects.create(
        inquiry=inquiry,
        privacy_policy_version=data["privacy_policy_version"],
        consent_text_version=data["consent_text_version"],
        consent_granted=True,
        source="driver_profile",
        allowed_contact_channels=data["allowed_contact_channels"],
    )
    InquiryStatusHistory.objects.create(inquiry=inquiry, to_status=DriverInquiry.Status.NEW)
    AuditEvent.objects.create(
        action="marketplace.inquiry.created",
        content_type=ContentType.objects.get_for_model(inquiry),
        object_id=str(inquiry.public_id),
        before={},
        after={"status": inquiry.status, "driver_public_id": str(driver.public_id)},
    )
    enqueue_inquiry_notifications(inquiry.pk)
    return inquiry, False


@transaction.atomic
def transition_inquiry(
    *,
    inquiry: DriverInquiry,
    actor,
    to_status: str,
    note: str = "",
    customer_visible_note: str = "",
) -> DriverInquiry:
    inquiry = DriverInquiry.objects.select_for_update().get(pk=inquiry.pk)
    allowed = ALLOWED_TRANSITIONS.get(inquiry.status, set())
    if to_status not in allowed:
        raise ValueError("Cette transition de statut n’est pas autorisée.")
    previous = inquiry.status
    inquiry.status = to_status
    inquiry.save(update_fields=("status", "updated_at"))
    InquiryStatusHistory.objects.create(
        inquiry=inquiry,
        from_status=previous,
        to_status=to_status,
        changed_by=actor,
        note=note,
        customer_visible_note=customer_visible_note,
    )
    AuditEvent.objects.create(
        actor=actor,
        action="marketplace.inquiry.status_changed",
        content_type=ContentType.objects.get_for_model(inquiry),
        object_id=str(inquiry.public_id),
        before={"status": previous},
        after={"status": to_status},
        reason=note,
    )
    if to_status in {
        DriverInquiry.Status.CONTACTED,
        DriverInquiry.Status.ACCEPTED,
        DriverInquiry.Status.DECLINED,
    }:
        from apps.notifications.services import create_and_deliver

        labels = {
            DriverInquiry.Status.CONTACTED: "Le chauffeur indique vous avoir contacté",
            DriverInquiry.Status.ACCEPTED: (
                "Demande acceptée par le chauffeur, sous réserve de confirmation "
                "directe des détails et du tarif"
            ),
            DriverInquiry.Status.DECLINED: "Demande refusée par le chauffeur",
        }
        transaction.on_commit(
            lambda: create_and_deliver(
                kind=EmailNotification.Kind.INQUIRY_STATUS,
                template_key="inquiry.status.fr",
                recipient_email=inquiry.customer_email,
                context={
                    "customer_name": inquiry.customer_name,
                    "reference": inquiry.reference,
                    "status_label": labels[to_status],
                },
                idempotency_key=f"inquiry:{inquiry.public_id}:status:{to_status}",
                related_type="driver_inquiry",
                related_public_id=inquiry.public_id,
            ),
            robust=True,
        )
    return inquiry

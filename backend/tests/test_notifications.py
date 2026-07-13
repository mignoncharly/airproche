import json
import time

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.cache import cache
from django.urls import reverse

from apps.notifications.models import (
    ContactMessage,
    EmailDeliveryAttempt,
    EmailNotification,
)
from apps.notifications.services import (
    create_and_deliver,
    create_contact_message,
    create_notification,
    retry_notification,
    send_account_notification,
)

User = get_user_model()


def contact_payload(**changes):
    payload = {
        "first_name": "Alice",
        "last_name": "Martin",
        "email": "alice@example.test",
        "phone": "+33102030405",
        "topic": "booking",
        "message": "Je prépare une réservation entièrement fictive.",
        "website": "",
        "form_started_at": int(time.time() * 1000) - 5000,
    }
    payload.update(changes)
    return payload


def notification():
    item, _ = create_notification(
        kind=EmailNotification.Kind.CONTACT_RECEIVED,
        template_key="contact.received.fr",
        recipient_email="alice@example.test",
        context={"first_name": "Alice"},
        idempotency_key="notification-test-1",
    )
    return item


@pytest.mark.django_db
def test_successful_and_failed_delivery_are_persisted(monkeypatch):
    monkeypatch.setattr("apps.notifications.services.send_mail", lambda *args, **kwargs: 1)
    sent, duplicate = create_and_deliver(
        kind=EmailNotification.Kind.CONTACT_RECEIVED,
        template_key="contact.received.fr",
        recipient_email="alice@example.test",
        context={"first_name": "Alice"},
        idempotency_key="delivery-success",
    )
    assert duplicate is False
    assert sent.status == EmailNotification.Status.SENT
    assert sent.attempts.get().status == EmailDeliveryAttempt.Status.SENT

    def fail(*args, **kwargs):
        raise OSError("provider details must not be persisted")

    monkeypatch.setattr("apps.notifications.services.send_mail", fail)
    failed, _ = create_and_deliver(
        kind=EmailNotification.Kind.CONTACT_RECEIVED,
        template_key="contact.received.fr",
        recipient_email="bob@example.test",
        context={"first_name": "Bob"},
        idempotency_key="delivery-failure",
    )
    attempt = failed.attempts.get()
    assert failed.status == EmailNotification.Status.FAILED
    assert attempt.status == EmailDeliveryAttempt.Status.FAILED
    assert "provider details" not in attempt.error_message


@pytest.mark.django_db
def test_retry_is_idempotent(monkeypatch):
    item = notification()
    monkeypatch.setattr("apps.notifications.services.send_mail", lambda *args, **kwargs: 0)
    first = retry_notification(item, idempotency_key="retry-1")
    assert first.status == EmailDeliveryAttempt.Status.FAILED

    monkeypatch.setattr("apps.notifications.services.send_mail", lambda *args, **kwargs: 1)
    second = retry_notification(item, idempotency_key="retry-2")
    replay = retry_notification(item, idempotency_key="retry-2")
    assert second.status == EmailDeliveryAttempt.Status.SENT
    assert replay.pk == second.pk
    assert item.attempts.count() == 2


@pytest.mark.django_db
def test_template_and_header_injection_are_rejected():
    with pytest.raises(ValueError):
        create_notification(
            kind=EmailNotification.Kind.CONTACT_RECEIVED,
            template_key="arbitrary-template",
            recipient_email="alice@example.test",
            context={},
            idempotency_key="bad-template",
        )
    with pytest.raises(ValueError):
        create_notification(
            kind=EmailNotification.Kind.CONTACT_RECEIVED,
            template_key="contact.received.fr",
            recipient_email="alice@example.test\r\nBcc: attacker@example.test",
            context={"first_name": "Alice"},
            idempotency_key="bad-header",
        )


@pytest.mark.django_db
def test_contact_honeypot_time_trap_and_idempotency(client):
    too_fast = client.post(
        reverse("contact-submit"),
        contact_payload(form_started_at=int(time.time() * 1000)),
        content_type="application/json",
    )
    assert too_fast.status_code == 400

    honeypot = client.post(
        reverse("contact-submit"),
        contact_payload(website="https://spam.example"),
        content_type="application/json",
    )
    assert honeypot.status_code == 202
    assert not ContactMessage.objects.exists()

    first = client.post(
        reverse("contact-submit"),
        contact_payload(),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="contact-1",
    )
    replay = client.post(
        reverse("contact-submit"),
        contact_payload(),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="contact-1",
    )
    conflict = client.post(
        reverse("contact-submit"),
        contact_payload(message="Une autre demande fictive suffisamment longue."),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="contact-1",
    )
    assert first.status_code == 201
    assert replay.status_code == 200
    assert replay.json()["idempotent_replay"] is True
    assert conflict.status_code == 409
    assert ContactMessage.objects.count() == 1


@pytest.mark.django_db
def test_contact_rate_limit(client):
    cache.clear()
    for index in range(5):
        response = client.post(
            reverse("contact-submit"),
            contact_payload(email=f"person{index}@example.test"),
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY=f"rate-{index}",
        )
        assert response.status_code == 201
    blocked = client.post(
        reverse("contact-submit"),
        contact_payload(email="blocked@example.test"),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="rate-blocked",
    )
    assert blocked.status_code == 429
    cache.clear()


@pytest.mark.django_db
def test_staff_communications_permissions(client):
    item = notification()
    assert client.get(reverse("communications:notification-list")).status_code in {401, 403}

    staff = User.objects.create_user(
        email="staff@example.test",
        password="Long-unique-passphrase-729!",
        is_staff=True,
    )
    client.force_login(staff)
    assert client.get(reverse("communications:notification-list")).status_code == 403

    staff.user_permissions.add(Permission.objects.get(codename="view_emailnotification"))
    assert client.get(reverse("communications:notification-list")).status_code == 200
    retry_url = reverse("communications:notification-retry", args=[item.public_id])
    assert (
        client.post(
            retry_url,
            {},
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="staff-retry",
        ).status_code
        == 403
    )

    staff.user_permissions.add(Permission.objects.get(codename="change_emailnotification"))
    response = client.post(
        retry_url,
        {},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="staff-retry",
    )
    assert response.status_code == 200


@pytest.mark.django_db(transaction=True)
def test_contact_delivery_runs_only_after_commit(django_capture_on_commit_callbacks, monkeypatch):
    delivered = []
    monkeypatch.setattr(
        "apps.notifications.services.send_mail",
        lambda *args, **kwargs: delivered.append(args) or 1,
    )
    with django_capture_on_commit_callbacks(execute=True):
        from django.db import transaction

        with transaction.atomic():
            create_contact_message(
                contact_payload(),
                idempotency_key="commit-timing",
                remote_addr="192.0.2.10",
            )
            assert ContactMessage.objects.filter(idempotency_key="commit-timing").exists()
            assert not EmailNotification.objects.exists()
            assert not delivered
    assert EmailNotification.objects.get().status == EmailNotification.Status.SENT
    assert len(delivered) == 1

@pytest.mark.django_db
def test_account_email_is_observable_without_persisting_single_use_token(monkeypatch):
    monkeypatch.setattr("apps.notifications.services.send_mail", lambda *args, **kwargs: 1)
    user = User.objects.create_user(
        email="account@example.test",
        password="Long-unique-passphrase-729!",
        first_name="Alice",
        last_name="Martin",
    )
    raw_token = "fictional-single-use-token"
    assert send_account_notification(user, raw_token, purpose="verify_email") is True

    item = EmailNotification.objects.get(kind=EmailNotification.Kind.VERIFY_EMAIL)
    assert item.status == EmailNotification.Status.SENT
    assert item.retryable is False
    assert raw_token not in json.dumps(item.context)
    assert raw_token not in item.idempotency_key

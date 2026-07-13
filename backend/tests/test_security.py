import json

import pytest
from django.test import override_settings
from django.urls import reverse


@pytest.mark.django_db
def test_unsafe_api_rejects_untrusted_origin(client):
    response = client.post(
        reverse("accounts:login"),
        {"email": "fictional@example.test", "password": "not-a-real-password"},
        content_type="application/json",
        HTTP_ORIGIN="https://evil.example.test",
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "invalid_origin"


@pytest.mark.django_db
@override_settings(REQUIRE_API_ORIGIN=True)
def test_production_origin_policy_rejects_missing_origin(client):
    response = client.post(
        reverse("accounts:login"),
        {"email": "fictional@example.test", "password": "not-a-real-password"},
        content_type="application/json",
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "missing_origin"


@pytest.mark.django_db
def test_configured_origin_reaches_the_view(client):
    response = client.post(
        reverse("accounts:login"),
        {"email": "fictional@example.test", "password": "not-a-real-password"},
        content_type="application/json",
        HTTP_ORIGIN="http://localhost:3000",
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] != "invalid_origin"


@pytest.mark.django_db
def test_stripe_webhook_is_origin_exempt_but_still_signature_protected(client, monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fictional")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_fictional")
    monkeypatch.setenv("STRIPE_ENVIRONMENT", "test")
    response = client.post(
        reverse("payments:stripe-webhook"),
        data=json.dumps({"id": "evt_fictional", "type": "checkout.session.completed"}),
        content_type="application/json",
        HTTP_ORIGIN="https://evil.example.test",
        HTTP_STRIPE_SIGNATURE="t=1,v1=forged",
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_signature"


@pytest.mark.django_db
def test_non_public_api_defaults_to_private_no_store(client):
    response = client.get(reverse("core:health-live"))
    assert "no-store" in response["Cache-Control"]
    assert "private" in response["Cache-Control"]
    assert response["Pragma"] == "no-cache"


@pytest.mark.django_db
def test_explicit_public_response_remains_cacheable_only_for_anonymous_requests(
    client, django_user_model
):
    public = client.get(reverse("content:public-content"))
    assert public["Cache-Control"] == "public, max-age=60"

    user = django_user_model.objects.create_user(
        email="cache-user@example.test", password="Fictional-password-492!"
    )
    client.force_login(user)
    authenticated = client.get(reverse("content:public-content"))
    assert "no-store" in authenticated["Cache-Control"]
    assert "private" in authenticated["Cache-Control"]


@pytest.mark.django_db
@override_settings(
    STAFF_NETWORK_GATE_ENABLED=True,
    STAFF_ALLOWED_NETWORKS=["203.0.113.8/32"],
    TRUSTED_PROXY_NETWORKS=["127.0.0.1/32"],
)
def test_staff_gate_uses_forwarded_ip_only_from_trusted_proxy(client):
    url = "/api/v1/staff/airports/"
    denied = client.get(url, REMOTE_ADDR="127.0.0.1", HTTP_X_FORWARDED_FOR="198.51.100.4")
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "staff_network_denied"

    allowed_network = client.get(
        url,
        REMOTE_ADDR="127.0.0.1",
        HTTP_X_FORWARDED_FOR="203.0.113.8",
    )
    assert allowed_network.status_code in {401, 403}
    assert allowed_network.json().get("error", {}).get("code") != "staff_network_denied"

    spoofed = client.get(
        url,
        REMOTE_ADDR="198.51.100.10",
        HTTP_X_FORWARDED_FOR="203.0.113.8",
    )
    assert spoofed.status_code == 403
    assert spoofed.json()["error"]["code"] == "staff_network_denied"


@pytest.mark.django_db
def test_disallowed_host_is_rejected(client):
    response = client.get(reverse("core:health-live"), HTTP_HOST="evil.example.test")
    assert response.status_code == 400


@pytest.mark.django_db
def test_retention_command_is_dry_run_by_default_and_requires_apply():
    from datetime import timedelta
    from io import StringIO

    from django.core.management import call_command
    from django.utils import timezone

    from apps.notifications.models import ContactMessage

    message = ContactMessage.objects.create(
        first_name="Fictional",
        last_name="Contact",
        email="retention@example.test",
        topic=ContactMessage.Topic.OTHER,
        message="Fictional retention test message.",
        request_hash="a" * 64,
    )
    ContactMessage.objects.filter(pk=message.pk).update(
        created_at=timezone.now() - timedelta(days=31)
    )
    arguments = {
        "booking_days": 30,
        "contact_days": 30,
        "notification_days": 30,
        "token_grace_days": 7,
    }

    dry_run = StringIO()
    call_command("enforce_data_retention", stdout=dry_run, **arguments)
    assert ContactMessage.objects.filter(pk=message.pk).exists()
    assert "Dry run only" in dry_run.getvalue()

    call_command("enforce_data_retention", apply=True, stdout=StringIO(), **arguments)
    assert not ContactMessage.objects.filter(pk=message.pk).exists()


@pytest.mark.django_db
def test_staff_flag_alone_cannot_use_legacy_privileged_actions(client, django_user_model):
    staff = django_user_model.objects.create_user(
        email="limited-staff@example.test",
        password="Fictional-password-582!",
        is_staff=True,
    )
    client.force_login(staff)
    booking_id = "11111111-1111-4111-8111-111111111111"
    payment_id = "22222222-2222-4222-8222-222222222222"

    transition = client.post(
        f"/api/v1/bookings/{booking_id}/transition/",
        {"to_status": "confirmed"},
        content_type="application/json",
    )
    reconcile = client.post(
        f"/api/v1/payments/{payment_id}/reconcile/",
        {},
        content_type="application/json",
    )
    refund = client.post(
        f"/api/v1/payments/{payment_id}/refund/",
        {"reason": "Fictional"},
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="fictional-refund",
    )
    assert transition.status_code == 403
    assert reconcile.status_code == 403
    assert refund.status_code == 403


def test_stripe_live_mode_requires_separate_explicit_confirmation(monkeypatch):
    from apps.payments.stripe_adapter import StripeConfigurationError, configuration

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_fictional")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_fictional")
    monkeypatch.setenv("STRIPE_ENVIRONMENT", "live")
    monkeypatch.delenv("STRIPE_LIVE_MODE_CONFIRMED", raising=False)
    with pytest.raises(StripeConfigurationError, match="explicit"):
        configuration()

    monkeypatch.setenv("STRIPE_LIVE_MODE_CONFIRMED", "true")
    assert configuration()["environment"] == "live"


def test_stripe_defaults_to_test_even_in_production(monkeypatch):
    from apps.payments.stripe_adapter import configuration

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fictional")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_fictional")
    monkeypatch.delenv("STRIPE_ENVIRONMENT", raising=False)
    assert configuration()["environment"] == "test"


def test_json_logging_redacts_credentials_and_personal_data():
    import json as json_module
    import logging

    from apps.core.logging import JsonFormatter

    record = logging.LogRecord(
        "security-test",
        logging.ERROR,
        __file__,
        1,
        "user@example.test +33 6 00 00 00 00 ?token=fictional-token sk_test_fictionalsecret",
        (),
        None,
    )
    payload = json_module.loads(JsonFormatter().format(record))
    message = payload["message"]
    assert "user@example.test" not in message
    assert "+33 6 00 00 00 00" not in message
    assert "fictional-token" not in message
    assert "sk_test_fictionalsecret" not in message
    assert "[redacted" in message


@pytest.mark.django_db
def test_contact_submission_requires_real_csrf_token_even_from_allowed_origin():
    from django.test import Client

    strict = Client(enforce_csrf_checks=True)
    payload = {
        "first_name": "Fictional",
        "last_name": "Sender",
        "email": "csrf@example.test",
        "topic": "other",
        "message": "This is a fictional CSRF test message.",
        "website": "",
        "form_started_at": int((__import__("time").time() - 10) * 1000),
    }
    rejected = strict.post(
        reverse("contact-submit"),
        payload,
        content_type="application/json",
        HTTP_ORIGIN="http://localhost:3000",
        HTTP_IDEMPOTENCY_KEY="csrf-fictional-1",
    )
    assert rejected.status_code == 403

    csrf_response = strict.get(reverse("accounts:csrf"))
    token = csrf_response.json()["csrf_token"]
    accepted = strict.post(
        reverse("contact-submit"),
        payload,
        content_type="application/json",
        HTTP_ORIGIN="http://localhost:3000",
        HTTP_X_CSRFTOKEN=token,
        HTTP_IDEMPOTENCY_KEY="csrf-fictional-2",
    )
    assert accepted.status_code == 201


@pytest.mark.django_db
def test_account_anonymization_is_explicit_and_revokes_login(django_user_model):
    from io import StringIO

    from django.core.management import call_command

    user = django_user_model.objects.create_user(
        email="erase-me@example.test",
        password="Fictional-password-731!",
        first_name="Fictional",
        last_name="Person",
    )
    call_command("anonymize_account", public_id=str(user.public_id), stdout=StringIO())
    user.refresh_from_db()
    assert user.email == "erase-me@example.test"
    assert user.is_active

    call_command(
        "anonymize_account",
        public_id=str(user.public_id),
        apply=True,
        stdout=StringIO(),
    )
    user.refresh_from_db()
    assert user.email.endswith("@example.invalid")
    assert not user.is_active
    assert not user.has_usable_password()

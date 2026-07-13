import re

import pytest
from django.contrib.auth.models import Group
from django.core import mail
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import AccountToken, User
from apps.content.models import LegalDocument

PASSWORD = "Long-unique-passphrase-729!"
NEW_PASSWORD = "Another-unique-passphrase-845!"


def csrf_post(client: Client, route: str, data: dict):
    csrf = client.get(reverse("accounts:csrf")).json()["csrf_token"]
    return client.post(
        reverse(route),
        data=data,
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf,
    )


def csrf_patch(client: Client, route: str, data: dict):
    csrf = client.get(reverse("accounts:csrf")).json()["csrf_token"]
    return client.patch(
        reverse(route),
        data=data,
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf,
    )


def publish_registration_documents():
    for kind, version in (
        (LegalDocument.Kind.TERMS, "terms-1"),
        (LegalDocument.Kind.PRIVACY, "privacy-1"),
    ):
        LegalDocument.objects.create(
            kind=kind,
            version=version,
            title=f"Document {kind}",
            body="Approved test text.",
            effective_at=timezone.now(),
            is_published=True,
        )


def registration_payload():
    return {
        "first_name": "Marie",
        "last_name": "Martin",
        "email": "Marie@Example.COM",
        "phone": "+33612345678",
        "password": PASSWORD,
        "accept_terms": True,
        "accept_privacy": True,
    }


@pytest.mark.django_db
def test_anonymous_state_change_requires_csrf():
    client = Client(enforce_csrf_checks=True)

    response = client.post(
        reverse("accounts:login"),
        data={"email": "nobody@example.com", "password": PASSWORD},
        content_type="application/json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_registration_is_closed_without_published_legal_documents():
    client = Client(enforce_csrf_checks=True)

    response = csrf_post(client, "accounts:register", registration_payload())

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "registration_unavailable"
    assert not User.objects.exists()


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
@pytest.mark.django_db
def test_registration_snapshots_consents_and_verification_is_single_use():
    publish_registration_documents()
    client = Client(enforce_csrf_checks=True)

    response = csrf_post(client, "accounts:register", registration_payload())

    assert response.status_code == 201
    assert response.json()["verification_email_sent"] is True
    user = User.objects.get()
    assert user.email == "marie@example.com"
    assert set(user.consent_records.values_list("document_version", flat=True)) == {
        "terms-1",
        "privacy-1",
    }
    assert "/verification-email#token=" in mail.outbox[0].body
    assert "/verification-email?token=" not in mail.outbox[0].body
    raw_token = re.search(r"token=([^\s]+)", mail.outbox[0].body).group(1)
    stored = AccountToken.objects.get(purpose=AccountToken.Purpose.VERIFY_EMAIL)
    assert raw_token not in stored.token_digest

    verified = csrf_post(client, "accounts:verify-email", {"token": raw_token})
    reused = csrf_post(client, "accounts:verify-email", {"token": raw_token})

    user.refresh_from_db()
    assert verified.status_code == 200
    assert reused.status_code == 400
    assert user.email_verified_at is not None


@pytest.mark.django_db
def test_login_session_profile_gate_and_logout():
    user = User.objects.create_user(
        email="person@example.com", password=PASSWORD, first_name="Pat", last_name="Test"
    )
    client = Client(enforce_csrf_checks=True)

    failed = csrf_post(
        client,
        "accounts:login",
        {"email": user.email, "password": "incorrect-password"},
    )
    success = csrf_post(client, "accounts:login", {"email": user.email, "password": PASSWORD})
    me = client.get(reverse("accounts:me"))
    blocked_profile = csrf_patch(client, "accounts:profile", {"first_name": "Updated"})

    assert failed.status_code == 403
    assert success.status_code == 200
    assert me.status_code == 200
    assert blocked_profile.status_code == 403

    user.email_verified_at = timezone.now()
    user.save(update_fields=("email_verified_at",))
    updated = csrf_patch(client, "accounts:profile", {"first_name": "Updated"})
    logged_out = csrf_post(client, "accounts:logout", {})

    assert updated.status_code == 200
    assert updated.json()["user"]["first_name"] == "Updated"
    assert logged_out.status_code == 200
    assert client.get(reverse("accounts:me")).status_code == 403


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
@pytest.mark.django_db
def test_password_reset_is_non_enumerating_and_token_is_single_use():
    user = User.objects.create_user(
        email="person@example.com", password=PASSWORD, first_name="Pat", last_name="Test"
    )
    client = Client(enforce_csrf_checks=True)

    known = csrf_post(client, "accounts:password-reset", {"email": user.email})
    unknown = csrf_post(client, "accounts:password-reset", {"email": "unknown@example.com"})

    assert known.status_code == unknown.status_code == 202
    assert known.json() == unknown.json()
    assert len(mail.outbox) == 1
    assert "/reinitialiser-mot-de-passe#token=" in mail.outbox[0].body
    assert "/reinitialiser-mot-de-passe?token=" not in mail.outbox[0].body
    raw_token = re.search(r"token=([^\s]+)", mail.outbox[0].body).group(1)

    reset = csrf_post(
        client,
        "accounts:password-reset-confirm",
        {"token": raw_token, "new_password": NEW_PASSWORD},
    )
    reused = csrf_post(
        client,
        "accounts:password-reset-confirm",
        {"token": raw_token, "new_password": PASSWORD},
    )

    user.refresh_from_db()
    assert reset.status_code == 200
    assert reused.status_code == 400
    assert user.check_password(NEW_PASSWORD)
    assert not user.check_password(PASSWORD)


@pytest.mark.django_db
def test_staff_role_groups_are_seeded():
    assert set(Group.objects.values_list("name", flat=True)) >= {
        "Operations",
        "Dispatcher",
        "Finance",
        "Content manager",
        "Administrator",
    }

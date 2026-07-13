import hashlib
import hmac
import json
import time
from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone

from apps.content.models import BusinessSettings
from apps.locations.models import Airport, ServiceArea
from apps.pricing.models import Quote, QuoteLine, Tariff, TripType

from apps.bookings.models import Booking, BookingStatusHistory
from apps.payments.models import Payment, PaymentAttempt, Refund, WebhookEvent


User = get_user_model()


@pytest.fixture
def open_quote(db):
    now = timezone.now()
    BusinessSettings.objects.create(minimum_lead_hours=2, maximum_booking_days=90, booking_enabled=True)
    airport = Airport.objects.create(name="Test airport", iata_code="TST", slug="test-airport", city="Paris", address="Test", latitude=48, longitude=2)
    area = ServiceArea.objects.create(name="Test area", slug="test-area", area_type="city", city="Paris")
    tariff = Tariff.objects.create(airport=airport, service_area=area, trip_type=TripType.AIRPORT_PICKUP, base_amount=Decimal("80.00"), currency="EUR", valid_from=now - timedelta(days=1))
    quote = Quote.objects.create(tariff=tariff, trip_type=TripType.AIRPORT_PICKUP, airport=airport, service_area=area, airport_name=airport.name, airport_iata_code="TST", service_area_name=area.name, pickup_at=now + timedelta(days=2), passenger_count=2, luggage_count=2, total_amount=Decimal("80.00"), currency="EUR", expires_at=now + timedelta(minutes=20))
    QuoteLine.objects.create(quote=quote, code="base-fare", label="Trajet", quantity=1, unit_amount=Decimal("80.00"), total_amount=Decimal("80.00"))
    return quote


@pytest.fixture
def stripe_config(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fixture")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_fixture")
    monkeypatch.setenv("STRIPE_ENVIRONMENT", "test")


def sign_event(payload: bytes) -> str:
    timestamp = str(int(time.time()))
    digest = hmac.new(b"whsec_fixture", f"{timestamp}.".encode() + payload, hashlib.sha256).hexdigest()
    return f"t={timestamp},v1={digest}"


def create_booking(client, quote):
    return client.post(
        reverse("bookings:create"),
        {
            "quote_id": str(quote.public_id), "booking_type": quote.trip_type,
            "adult_count": 2, "child_count": 0, "passenger_same_as_booker": True,
            "booker_first_name": "Ada", "booker_last_name": "Lovelace", "booker_email": "ada@example.com", "booker_phone": "+33123456789",
            "accept_terms": True, "accept_privacy": True,
        },
        content_type="application/json",
    ).json()


@pytest.mark.django_db
def test_checkout_is_server_priced_and_retries_reuse_existing_session(client, open_quote, stripe_config, monkeypatch):
    checkout_request = {}

    def create_session(**kwargs):
        checkout_request.update(kwargs)
        return {"id": "cs_fixture", "url": "https://checkout.stripe.com/cs_fixture"}

    monkeypatch.setattr(
        "apps.payments.services.create_checkout_session",
        create_session,
    )
    booking = create_booking(client, open_quote)
    url = reverse("payments:checkout", args=[booking["public_id"]])
    first = client.post(url, {}, content_type="application/json", HTTP_X_BOOKING_TOKEN=booking["management_token"], HTTP_IDEMPOTENCY_KEY="pay-1")
    assert first.status_code == 201
    assert first.json()["checkout_url"] == "https://checkout.stripe.com/cs_fixture"
    assert PaymentAttempt.objects.count() == 1
    assert "/paiement/retour#booking=" in checkout_request["success_url"]
    assert "?" not in checkout_request["success_url"]

    retry = client.post(url, {}, content_type="application/json", HTTP_X_BOOKING_TOKEN=booking["management_token"], HTTP_IDEMPOTENCY_KEY="pay-2")
    assert retry.status_code == 201
    assert retry.json()["checkout_url"] == first.json()["checkout_url"]
    assert PaymentAttempt.objects.count() == 1
    payment = Payment.objects.get()
    assert payment.amount == Decimal("80.00")
    assert payment.status == Payment.Status.PENDING


@pytest.mark.django_db
def test_signed_checkout_webhook_confirms_once_and_duplicate_is_ignored(client, open_quote, stripe_config, monkeypatch):
    monkeypatch.setattr("apps.payments.services.create_checkout_session", lambda **kwargs: {"id": "cs_paid", "url": "https://checkout.stripe.com/cs_paid"})
    booking = create_booking(client, open_quote)
    client.post(reverse("payments:checkout", args=[booking["public_id"]]), {}, content_type="application/json", HTTP_X_BOOKING_TOKEN=booking["management_token"], HTTP_IDEMPOTENCY_KEY="pay-paid")
    event = {
        "id": "evt_paid", "type": "checkout.session.completed", "data": {"object": {
            "id": "cs_paid", "amount_total": 8000, "currency": "eur", "payment_status": "paid", "payment_intent": "pi_paid",
            "metadata": {"payment_public_id": str(Payment.objects.get().public_id), "booking_reference": booking["reference"], "environment": "test"},
        }},
    }
    payload = json.dumps(event).encode()
    response = client.post(reverse("payments:stripe-webhook"), payload, content_type="application/json", HTTP_STRIPE_SIGNATURE=sign_event(payload))
    assert response.status_code == 200
    assert response.json()["outcome"] == "processed"
    payment = Payment.objects.get()
    assert payment.status == Payment.Status.SUCCEEDED
    assert Booking.objects.get(public_id=booking["public_id"]).status == Booking.Status.CONFIRMED
    assert BookingStatusHistory.objects.filter(to_status=Booking.Status.CONFIRMED).count() == 1

    duplicate = client.post(reverse("payments:stripe-webhook"), payload, content_type="application/json", HTTP_STRIPE_SIGNATURE=sign_event(payload))
    assert duplicate.status_code == 200
    assert duplicate.json()["outcome"] == "duplicate"
    assert BookingStatusHistory.objects.filter(to_status=Booking.Status.CONFIRMED).count() == 1


@pytest.mark.django_db
def test_webhook_amount_mismatch_is_quarantined_and_never_confirms(client, open_quote, stripe_config, monkeypatch):
    monkeypatch.setattr("apps.payments.services.create_checkout_session", lambda **kwargs: {"id": "cs_bad", "url": "https://checkout.stripe.com/cs_bad"})
    booking = create_booking(client, open_quote)
    client.post(reverse("payments:checkout", args=[booking["public_id"]]), {}, content_type="application/json", HTTP_X_BOOKING_TOKEN=booking["management_token"], HTTP_IDEMPOTENCY_KEY="pay-bad")
    event = {"id": "evt_bad", "type": "checkout.session.completed", "data": {"object": {
        "id": "cs_bad", "amount_total": 1, "currency": "eur", "payment_status": "paid", "payment_intent": "pi_bad",
        "metadata": {"payment_public_id": str(Payment.objects.get().public_id), "booking_reference": booking["reference"], "environment": "test"},
    }}}
    payload = json.dumps(event).encode()
    response = client.post(reverse("payments:stripe-webhook"), payload, content_type="application/json", HTTP_STRIPE_SIGNATURE=sign_event(payload))
    assert response.status_code == 200
    assert response.json()["outcome"] == "quarantined"
    assert Payment.objects.get().status == Payment.Status.MISMATCHED
    assert Booking.objects.get(public_id=booking["public_id"]).status == Booking.Status.PENDING_PAYMENT
    assert WebhookEvent.objects.get(provider_event_id="evt_bad").status == WebhookEvent.Status.QUARANTINED


@pytest.mark.django_db
def test_staff_refund_is_idempotent_and_updates_payment(client, open_quote, stripe_config, monkeypatch):
    monkeypatch.setattr("apps.payments.services.create_checkout_session", lambda **kwargs: {"id": "cs_refund", "url": "https://checkout.stripe.com/cs_refund"})
    monkeypatch.setattr("apps.payments.services.create_refund", lambda **kwargs: {"id": "re_fixture", "status": "succeeded"})
    booking = create_booking(client, open_quote)
    client.post(reverse("payments:checkout", args=[booking["public_id"]]), {}, content_type="application/json", HTTP_X_BOOKING_TOKEN=booking["management_token"], HTTP_IDEMPOTENCY_KEY="pay-refund")
    event = {"id": "evt_refund", "type": "checkout.session.completed", "data": {"object": {
        "id": "cs_refund", "amount_total": 8000, "currency": "eur", "payment_status": "paid", "payment_intent": "pi_refund",
        "metadata": {"payment_public_id": str(Payment.objects.get().public_id), "booking_reference": booking["reference"], "environment": "test"},
    }}}
    payload = json.dumps(event).encode()
    client.post(reverse("payments:stripe-webhook"), payload, content_type="application/json", HTTP_STRIPE_SIGNATURE=sign_event(payload))
    staff = User.objects.create_user(email="finance@example.com", password="Long-unique-passphrase-729!", is_staff=True)
    staff.user_permissions.add(Permission.objects.get(codename="add_refund"))
    client.force_login(staff)
    url = reverse("payments:refund", args=[Payment.objects.get().public_id])
    first = client.post(url, {"amount": "20.00", "reason": "Test refund"}, content_type="application/json", HTTP_IDEMPOTENCY_KEY="refund-1")
    assert first.status_code == 201
    assert first.json()["status"] == Refund.Status.SUCCEEDED
    replay = client.post(url, {"amount": "20.00", "reason": "Test refund"}, content_type="application/json", HTTP_IDEMPOTENCY_KEY="refund-1")
    assert replay.status_code == 201
    assert Refund.objects.count() == 1
    assert Payment.objects.get().status == Payment.Status.PARTIALLY_REFUNDED

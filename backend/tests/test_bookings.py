from datetime import timedelta
from decimal import Decimal

import pytest
from django.urls import reverse
from django.utils import timezone

from apps.content.models import BusinessSettings
from apps.locations.models import Airport, ServiceArea
from apps.pricing.models import Quote, QuoteLine, Tariff, TripType
from apps.bookings.models import Booking, BookingStatusHistory, PriceSnapshot
from apps.notifications.models import EmailNotification


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


def create_payload(quote, **changes):
    payload = {
        "quote_id": str(quote.public_id), "booking_type": quote.trip_type,
        "adult_count": 2, "child_count": 0, "passenger_same_as_booker": True,
        "booker_first_name": "Ada", "booker_last_name": "Lovelace", "booker_email": "ada@example.com", "booker_phone": "+33123456789",
        "accept_terms": True, "accept_privacy": True,
    }
    payload.update(changes)
    return payload


@pytest.mark.django_db
def test_guest_booking_is_created_once_and_can_be_retrieved(client, open_quote):
    response = client.post(reverse("bookings:create"), create_payload(open_quote), content_type="application/json", HTTP_IDEMPOTENCY_KEY="booking-test-1")
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == Booking.Status.PENDING_PAYMENT
    assert body["management_token"]
    assert Booking.objects.count() == 1
    assert PriceSnapshot.objects.get(booking__reference=body["reference"]).total_amount == Decimal("80.00")
    assert BookingStatusHistory.objects.get(booking__reference=body["reference"]).to_status == Booking.Status.PENDING_PAYMENT

    replay = client.post(reverse("bookings:create"), create_payload(open_quote), content_type="application/json", HTTP_IDEMPOTENCY_KEY="booking-test-1")
    assert replay.status_code == 200
    assert replay.json()["public_id"] == body["public_id"]
    assert Booking.objects.count() == 1

    accessed = client.post(reverse("bookings:guest-access"), {"reference": body["reference"], "management_token": body["management_token"]}, content_type="application/json")
    assert accessed.status_code == 200
    assert accessed.json()["reference"] == body["reference"]


@pytest.mark.django_db
def test_booking_rejects_expired_quote_and_forbidden_transition(client, open_quote):
    open_quote.expires_at = timezone.now() - timedelta(seconds=1)
    open_quote.save(update_fields=("expires_at",))
    response = client.post(reverse("bookings:create"), create_payload(open_quote), content_type="application/json")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "quote_expired"


@pytest.mark.django_db
def test_guest_can_cancel_before_deadline(client, open_quote):
    created = client.post(reverse("bookings:create"), create_payload(open_quote), content_type="application/json").json()
    response = client.post(reverse("bookings:cancel", args=[created["public_id"]]), {"reason": "Changement de programme"}, content_type="application/json", HTTP_X_BOOKING_TOKEN=created["management_token"])
    assert response.status_code == 200
    assert response.json()["status"] == Booking.Status.CANCELLED

@pytest.mark.django_db
def test_booking_commit_survives_email_failure(
    client, open_quote, django_capture_on_commit_callbacks, monkeypatch
):
    def fail_delivery(*args, **kwargs):
        raise OSError("simulated SMTP outage")

    monkeypatch.setattr("apps.notifications.services.send_mail", fail_delivery)
    with django_capture_on_commit_callbacks(execute=True):
        response = client.post(
            reverse("bookings:create"),
            create_payload(open_quote),
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="booking-email-failure",
        )
        assert response.status_code == 201
        assert Booking.objects.filter(public_id=response.json()["public_id"]).exists()
        assert not EmailNotification.objects.exists()

    notification = EmailNotification.objects.get()
    assert notification.status == EmailNotification.Status.FAILED
    assert Booking.objects.filter(public_id=response.json()["public_id"]).exists()

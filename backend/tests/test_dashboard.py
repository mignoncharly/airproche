from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from apps.bookings.models import Booking
from apps.content.models import BusinessSettings
from apps.locations.models import Airport, ServiceArea
from apps.pricing.models import Quote, QuoteLine, Tariff, TripType


User = get_user_model()


@pytest.fixture
def dashboard_quote(db):
    now = timezone.now()
    BusinessSettings.objects.create(minimum_lead_hours=2, maximum_booking_days=90, booking_enabled=True)
    airport = Airport.objects.create(name="Dashboard airport", iata_code="DSH", slug="dashboard-airport", city="Paris", address="Test", latitude=48, longitude=2)
    area = ServiceArea.objects.create(name="Dashboard area", slug="dashboard-area", area_type="city", city="Paris")
    tariff = Tariff.objects.create(airport=airport, service_area=area, trip_type=TripType.AIRPORT_PICKUP, base_amount=Decimal("80.00"), currency="EUR", valid_from=now - timedelta(days=1))
    quote = Quote.objects.create(tariff=tariff, trip_type=TripType.AIRPORT_PICKUP, airport=airport, service_area=area, airport_name=airport.name, airport_iata_code="DSH", service_area_name=area.name, pickup_at=now + timedelta(days=2), passenger_count=2, luggage_count=2, total_amount=Decimal("80.00"), currency="EUR", expires_at=now + timedelta(minutes=20))
    QuoteLine.objects.create(quote=quote, code="base-fare", label="Trajet", quantity=1, unit_amount=Decimal("80.00"), total_amount=Decimal("80.00"))
    return quote


def booking_payload(quote):
    return {
        "quote_id": str(quote.public_id), "booking_type": quote.trip_type,
        "adult_count": 2, "child_count": 0, "passenger_same_as_booker": True,
        "booker_first_name": "Customer", "booker_last_name": "Example", "booker_email": "customer@example.com", "booker_phone": "+33123456789",
        "accept_terms": True, "accept_privacy": True,
    }


@pytest.mark.django_db
def test_customer_dashboard_is_owner_scoped_and_receipt_is_private(client, dashboard_quote):
    customer = User.objects.create_user(email="customer@example.com", password="Long-unique-passphrase-729!")
    other = User.objects.create_user(email="other@example.com", password="Long-unique-passphrase-729!")
    client.force_login(customer)
    created = client.post(reverse("bookings:create"), booking_payload(dashboard_quote), content_type="application/json")
    assert created.status_code == 201
    body = created.json()
    booking = Booking.objects.get(public_id=body["public_id"])
    assert booking.customer_id == customer.pk

    dashboard = client.get(reverse("bookings:mine"))
    assert dashboard.status_code == 200
    assert len(dashboard.json()) == 1
    assert dashboard.json()[0]["payment_status"] == "not_created"
    receipt = client.get(reverse("bookings:receipt", args=[booking.public_id]))
    assert receipt.status_code == 200
    assert body["reference"] in receipt.content.decode()
    assert "no-store" in receipt["Cache-Control"]
    assert "facture fiscale" in receipt.content.decode().lower()

    client.force_login(other)
    assert client.get(reverse("bookings:mine")).json() == []
    assert client.get(reverse("bookings:receipt", args=[booking.public_id])).status_code == 404


@pytest.mark.django_db
def test_customer_cancellation_and_repeat_are_authorized(client, dashboard_quote):
    customer = User.objects.create_user(email="customer@example.com", password="Long-unique-passphrase-729!")
    client.force_login(customer)
    created = client.post(reverse("bookings:create"), booking_payload(dashboard_quote), content_type="application/json").json()
    cancel = client.post(reverse("bookings:cancel", args=[created["public_id"]]), {"reason": "Test"}, content_type="application/json")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == Booking.Status.CANCELLED
    repeat = client.post(reverse("bookings:repeat", args=[created["public_id"]]), {"pickup_at": (timezone.now() + timedelta(days=3)).isoformat()}, content_type="application/json")
    assert repeat.status_code == 201
    assert repeat.json()["status"] == "valid"

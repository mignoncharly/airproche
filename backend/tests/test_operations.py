from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.utils import timezone

from apps.bookings.models import Booking, BookingStatusHistory
from apps.content.models import BusinessSettings
from apps.locations.models import Airport, ServiceArea
from apps.operations.models import AuditEvent, Driver, DriverAssignment, Vehicle
from apps.pricing.models import Quote, QuoteLine, Tariff, TripType


User = get_user_model()


@pytest.fixture
def operational_booking(db):
    now = timezone.now()
    BusinessSettings.objects.create(minimum_lead_hours=2, maximum_booking_days=90, booking_enabled=True)
    airport = Airport.objects.create(name="Operations airport", iata_code="OPS", slug="operations-airport", city="Paris", address="Test", latitude=48, longitude=2)
    area = ServiceArea.objects.create(name="Operations area", slug="operations-area", area_type="city", city="Paris")
    tariff = Tariff.objects.create(airport=airport, service_area=area, trip_type=TripType.AIRPORT_PICKUP, base_amount=Decimal("120.00"), currency="EUR", valid_from=now - timedelta(days=1))
    quote = Quote.objects.create(tariff=tariff, trip_type=TripType.AIRPORT_PICKUP, airport=airport, service_area=area, airport_name=airport.name, airport_iata_code="OPS", service_area_name=area.name, pickup_at=now + timedelta(days=2), passenger_count=3, luggage_count=2, total_amount=Decimal("120.00"), currency="EUR", expires_at=now + timedelta(minutes=20))
    QuoteLine.objects.create(quote=quote, code="base-fare", label="Trajet", quantity=1, unit_amount=Decimal("120.00"), total_amount=Decimal("120.00"))
    booking = Booking.objects.create(
        reference="TR-OPS001", quote=quote, source=Booking.Source.STAFF, booking_type=quote.trip_type,
        airport=airport, service_area=area, pickup_at=quote.pickup_at, passenger_count=3,
        adult_count=3, luggage_count=2, booker_first_name="Op", booker_last_name="User",
        booker_email="ops@example.com", booker_phone="+33123456789", passenger_first_name="Op",
        passenger_last_name="User", passenger_phone="+33123456789", status=Booking.Status.DRIVER_ASSIGNMENT_PENDING,
        total_amount=quote.total_amount, currency="EUR",
    )
    BookingStatusHistory.objects.create(booking=booking, to_status=booking.status)
    return booking


def staff_with_permissions(*codenames):
    user = User.objects.create_user(email="dispatcher@example.com", password="Long-unique-passphrase-729!", is_staff=True)
    user.user_permissions.add(*Permission.objects.filter(codename__in=codenames))
    return user


@pytest.mark.django_db
def test_operations_api_is_staff_and_permission_scoped(client, operational_booking):
    assert client.get(reverse("operations:summary")).status_code in {401, 403}
    customer = User.objects.create_user(email="customer-ops@example.com", password="Long-unique-passphrase-729!")
    client.force_login(customer)
    assert client.get(reverse("operations:summary")).status_code == 403

    staff = staff_with_permissions("view_booking", "view_driver", "view_vehicle", "view_driverassignment")
    client.force_login(staff)
    summary = client.get(reverse("operations:summary"))
    assert summary.status_code == 200
    assert summary.json()["total_bookings"] == 1
    listing = client.get(reverse("operations:booking-list"), {"q": operational_booking.reference, "assigned": "false"})
    assert listing.status_code == 200
    assert listing.json()[0]["reference"] == operational_booking.reference


@pytest.mark.django_db
def test_assignment_validates_capacity_overlap_and_writes_audit(client, operational_booking):
    staff = staff_with_permissions("view_booking", "change_booking", "view_driver", "view_vehicle", "view_driverassignment", "change_driverassignment", "view_auditevent", "add_bookingnote")
    driver = Driver.objects.create(first_name="Ada", last_name="Driver", phone="+33111111111", max_passengers=4)
    vehicle = Vehicle.objects.create(registration="OPS-001", label="Van", seats=4, luggage_capacity=4)
    client.force_login(staff)

    response = client.post(reverse("operations:assignment", args=[operational_booking.public_id]), {"driver_id": str(driver.public_id), "vehicle_id": str(vehicle.public_id)}, content_type="application/json")
    assert response.status_code == 201
    assert response.json()["active"] is True
    operational_booking.refresh_from_db()
    assert operational_booking.status == Booking.Status.DRIVER_ASSIGNED
    assert DriverAssignment.objects.filter(booking=operational_booking, unassigned_at__isnull=True).exists()
    assert AuditEvent.objects.filter(action="driver_assignment_created").exists()

    second = Booking.objects.create(
        reference="TR-OPS002", quote=operational_booking.quote, source=Booking.Source.STAFF, booking_type=operational_booking.booking_type,
        airport=operational_booking.airport, service_area=operational_booking.service_area, pickup_at=operational_booking.pickup_at,
        passenger_count=3, adult_count=3, luggage_count=2, booker_first_name="Second", booker_last_name="User",
        booker_email="second@example.com", booker_phone="+33123456789", passenger_first_name="Second", passenger_last_name="User",
        passenger_phone="+33123456789", status=Booking.Status.DRIVER_ASSIGNMENT_PENDING, total_amount=Decimal("120.00"), currency="EUR",
    )
    conflict = client.post(reverse("operations:assignment", args=[second.public_id]), {"driver_id": str(driver.public_id), "vehicle_id": str(vehicle.public_id)}, content_type="application/json")
    assert conflict.status_code == 409

    narrow_vehicle = Vehicle.objects.create(registration="OPS-002", label="Compact", seats=2, luggage_capacity=1)
    capacity = client.post(reverse("operations:assignment", args=[second.public_id]), {"driver_id": str(driver.public_id), "vehicle_id": str(narrow_vehicle.public_id)}, content_type="application/json")
    assert capacity.status_code == 409
    override = client.post(reverse("operations:assignment", args=[second.public_id]), {"driver_id": str(driver.public_id), "vehicle_id": str(narrow_vehicle.public_id), "allow_override": True, "override_reason": "Dispatcher confirmed exceptional arrangement."}, content_type="application/json")
    assert override.status_code == 201

    assignment = DriverAssignment.objects.filter(booking=operational_booking, unassigned_at__isnull=True).get()
    note = client.post(reverse("operations:booking-note", args=[operational_booking.public_id]), {"body": "Call passenger before pickup."}, content_type="application/json")
    assert note.status_code == 201
    removed = client.post(reverse("operations:unassignment", args=[assignment.public_id]), {"reason": "Vehicle changed."}, content_type="application/json")
    assert removed.status_code == 200
    operational_booking.refresh_from_db()
    assert operational_booking.status == Booking.Status.DRIVER_ASSIGNMENT_PENDING
    assert AuditEvent.objects.filter(action="driver_assignment_removed").exists()


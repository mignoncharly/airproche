from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils import timezone

from apps.content.models import BusinessSettings
from apps.locations.models import Airport, ServiceArea
from apps.pricing.models import Quote, Tariff, TariffOption, TripType

User = get_user_model()


@pytest.fixture
def priced_route(db):
    now = timezone.now()
    BusinessSettings.objects.create(
        business_name="Accueil Privé",
        minimum_lead_hours=2,
        maximum_booking_days=90,
        quote_valid_minutes=20,
    )
    airport = Airport.objects.create(
        name="Aéroport Démonstration",
        iata_code="tst",
        slug="aeroport-demonstration",
        city="Paris",
        country_code="fr",
        address="1 avenue du Test",
        latitude=Decimal("48.856600"),
        longitude=Decimal("2.352200"),
        description="Accueil privé sur confirmation.",
    )
    area = ServiceArea.objects.create(
        name="Centre de démonstration",
        slug="centre-demonstration",
        area_type=ServiceArea.AreaType.CITY,
        city="Paris",
        postal_codes=["75002", "75001", "75001"],
        description="Zone centrale active.",
    )
    tariff = Tariff.objects.create(
        airport=airport,
        service_area=area,
        trip_type=TripType.AIRPORT_PICKUP,
        base_amount=Decimal("80.01"),
        currency="eur",
        passenger_capacity=4,
        luggage_capacity=3,
        valid_from=now - timedelta(days=1),
    )
    option = TariffOption.objects.create(
        code="child-seat",
        label="Siège enfant",
        tariff=tariff,
        pricing_method=TariffOption.PricingMethod.PER_UNIT,
        amount=Decimal("12.34"),
        currency="EUR",
        maximum_quantity=2,
        valid_from=now - timedelta(days=1),
    )
    return airport, area, tariff, option


def quote_payload(airport, area, **changes):
    payload = {
        "trip_type": TripType.AIRPORT_PICKUP,
        "airport_id": str(airport.public_id),
        "service_area_id": str(area.public_id),
        "pickup_at": (timezone.now() + timedelta(days=2)).isoformat(),
        "passenger_count": 2,
        "luggage_count": 2,
        "options": [],
    }
    payload.update(changes)
    return payload


@pytest.mark.django_db
def test_published_locations_are_dynamic_and_exclude_inactive(client, priced_route):
    airport, area, _, _ = priced_route
    Airport.objects.create(
        name="Published without tariff",
        iata_code="PUB",
        slug="published-without-tariff",
        city="Paris",
        address="Published",
        latitude=0,
        longitude=0,
        display_order=2,
    )
    Airport.objects.create(
        name="Hidden airport",
        iata_code="HID",
        slug="hidden-airport",
        city="Paris",
        address="Hidden",
        latitude=0,
        longitude=0,
        is_active=False,
    )

    airports = client.get(reverse("locations:airport-list"))
    detail = client.get(reverse("locations:airport-detail", args=[airport.slug]))
    areas = client.get(reverse("locations:service-area-list"))
    area_detail = client.get(reverse("locations:service-area-detail", args=[area.slug]))

    assert (
        airports.status_code
        == detail.status_code
        == areas.status_code
        == area_detail.status_code
        == 200
    )
    assert [item["iata_code"] for item in airports.json()] == ["TST", "PUB"]
    assert detail.json()["description"] == "Accueil privé sur confirmation."
    assert [item["public_id"] for item in areas.json()] == [str(area.public_id)]
    assert area_detail.json()["postal_codes"] == ["75001", "75002"]
    assert airports.headers["Cache-Control"] == "public, max-age=60"


@pytest.mark.django_db
def test_coverage_only_publishes_tariff_backed_active_routes(client, priced_route):
    airport, area, _, option = priced_route
    uncovered = ServiceArea.objects.create(
        name="Sans tarif",
        slug="sans-tarif",
        area_type=ServiceArea.AreaType.CITY,
    )

    response = client.get(reverse("pricing:coverage"))

    assert response.status_code == 200
    assert response.json() == {
        "routes": [
            {
                "airport_id": str(airport.public_id),
                "service_area_id": str(area.public_id),
                "trip_type": TripType.AIRPORT_PICKUP,
                "options": [
                    {
                        "code": option.code,
                        "label": option.label,
                        "pricing_method": option.pricing_method,
                        "maximum_quantity": option.maximum_quantity,
                    }
                ],
            }
        ]
    }
    assert str(uncovered.public_id) not in str(response.json())


@pytest.mark.django_db
def test_quote_is_server_calculated_rounded_and_snapshotted(client, priced_route):
    airport, area, tariff, _ = priced_route
    payload = quote_payload(
        airport,
        area,
        options=[{"code": "child-seat", "quantity": 2}],
    )

    response = client.post(
        reverse("pricing:quote-create"), payload, content_type="application/json"
    )

    assert response.status_code == 201
    body = response.json()
    assert body["total_amount"] == "104.69"
    assert body["currency"] == "EUR"
    assert [line["total_amount"] for line in body["lines"]] == ["80.01", "24.68"]
    assert body["airport_iata_code"] == "TST"
    assert body["calculation_version"] == "fixed-zone-v1"

    tariff.base_amount = Decimal("999.00")
    tariff.save(update_fields=("base_amount", "updated_at"))
    saved = client.get(reverse("pricing:quote-detail", args=[body["public_id"]]))

    assert saved.status_code == 200
    assert saved.json()["total_amount"] == "104.69"
    assert "no-store" in saved.headers["Cache-Control"]
    assert "private" in saved.headers["Cache-Control"]


@pytest.mark.django_db
def test_browser_cannot_submit_an_authoritative_amount(client, priced_route):
    airport, area, _, _ = priced_route
    payload = quote_payload(airport, area, total_amount="0.01", currency="USD")

    response = client.post(
        reverse("pricing:quote-create"), payload, content_type="application/json"
    )

    assert response.status_code == 400
    assert response.json()["error"]["fields"]["total_amount"]
    assert not Quote.objects.exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("changes", "expected_code"),
    [
        ({"passenger_count": 5}, "capacity"),
        ({"luggage_count": 4}, "capacity"),
        ({"options": [{"code": "unknown", "quantity": 1}]}, "option_unavailable"),
        ({"options": [{"code": "child-seat", "quantity": 3}]}, "option_unavailable"),
    ],
)
def test_quote_rejections_have_stable_codes(client, priced_route, changes, expected_code):
    airport, area, _, _ = priced_route

    response = client.post(
        reverse("pricing:quote-create"),
        quote_payload(airport, area, **changes),
        content_type="application/json",
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == expected_code


@pytest.mark.django_db
def test_quote_enforces_lead_time_and_booking_horizon(client, priced_route):
    airport, area, _, _ = priced_route
    create_url = reverse("pricing:quote-create")

    too_soon = client.post(
        create_url,
        quote_payload(
            airport, area, pickup_at=(timezone.now() + timedelta(minutes=30)).isoformat()
        ),
        content_type="application/json",
    )
    too_late = client.post(
        create_url,
        quote_payload(airport, area, pickup_at=(timezone.now() + timedelta(days=91)).isoformat()),
        content_type="application/json",
    )

    assert too_soon.status_code == too_late.status_code == 422
    assert too_soon.json()["error"]["code"] == "lead_time"
    assert too_late.json()["error"]["code"] == "booking_horizon"


@pytest.mark.django_db
def test_tariff_validity_boundary_selects_the_new_rate(client, priced_route):
    airport, area, tariff, _ = priced_route
    boundary = timezone.now() + timedelta(days=4)
    tariff.valid_until = boundary
    tariff.save(update_fields=("valid_until", "updated_at"))
    Tariff.objects.create(
        airport=airport,
        service_area=area,
        trip_type=TripType.AIRPORT_PICKUP,
        base_amount=Decimal("95.00"),
        valid_from=boundary,
    )

    response = client.post(
        reverse("pricing:quote-create"),
        quote_payload(airport, area, pickup_at=boundary.isoformat()),
        content_type="application/json",
    )

    assert response.status_code == 201
    assert response.json()["total_amount"] == "95.00"


@pytest.mark.django_db
@pytest.mark.parametrize("state", ["inactive", "expired"])
def test_inactive_and_expired_tariffs_are_unavailable(client, priced_route, state):
    airport, area, tariff, _ = priced_route
    if state == "inactive":
        tariff.is_active = False
        tariff.save(update_fields=("is_active", "updated_at"))
    else:
        tariff.valid_until = timezone.now() - timedelta(minutes=1)
        tariff.save(update_fields=("valid_until", "updated_at"))

    response = client.post(
        reverse("pricing:quote-create"),
        quote_payload(airport, area),
        content_type="application/json",
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "coverage"


@pytest.mark.django_db
def test_expired_option_is_not_applied(client, priced_route):
    airport, area, _, option = priced_route
    option.valid_until = timezone.now() - timedelta(minutes=1)
    option.save(update_fields=("valid_until", "updated_at"))

    response = client.post(
        reverse("pricing:quote-create"),
        quote_payload(airport, area, options=[{"code": option.code, "quantity": 1}]),
        content_type="application/json",
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "option_unavailable"


@pytest.mark.django_db
def test_quote_detail_reports_expiry_without_mutating_snapshot(client, priced_route):
    airport, area, tariff, _ = priced_route
    quote = Quote.objects.create(
        tariff=tariff,
        trip_type=TripType.AIRPORT_PICKUP,
        airport=airport,
        service_area=area,
        airport_name=airport.name,
        airport_iata_code=airport.iata_code,
        service_area_name=area.name,
        pickup_at=timezone.now() + timedelta(days=1),
        passenger_count=1,
        luggage_count=0,
        total_amount=Decimal("80.01"),
        currency="EUR",
        expires_at=timezone.now() - timedelta(seconds=1),
    )

    response = client.get(reverse("pricing:quote-detail", args=[quote.public_id]))

    assert response.status_code == 200
    assert response.json()["status"] == Quote.Status.EXPIRED
    quote.refresh_from_db()
    assert quote.status == Quote.Status.VALID


@pytest.mark.django_db
def test_overlapping_active_tariffs_fail_model_validation(priced_route):
    airport, area, _, _ = priced_route
    overlapping = Tariff(
        airport=airport,
        service_area=area,
        trip_type=TripType.AIRPORT_PICKUP,
        base_amount=Decimal("90.00"),
        valid_from=timezone.now(),
    )

    with pytest.raises(ValidationError):
        overlapping.full_clean()


@pytest.mark.django_db
def test_staff_coverage_crud_requires_granular_model_permissions(client, priced_route):
    airport, _, _, _ = priced_route
    staff = User.objects.create_user(
        email="operations@example.com",
        password="Long-unique-passphrase-729!",
        is_staff=True,
    )
    detail_url = reverse("staff:airport-detail", args=[airport.public_id])
    list_url = reverse("staff:airport-list")
    client.force_login(staff)

    denied_without_permission = client.get(list_url)
    staff.user_permissions.add(Permission.objects.get(codename="view_airport"))
    allowed_read = client.get(list_url)
    denied_write = client.patch(
        detail_url,
        {"terminal_guidance": "Rendez-vous porte 4."},
        content_type="application/json",
    )
    staff.user_permissions.add(Permission.objects.get(codename="change_airport"))
    allowed_write = client.patch(
        detail_url,
        {"terminal_guidance": "Rendez-vous porte 4."},
        content_type="application/json",
    )

    assert denied_without_permission.status_code == denied_write.status_code == 403
    assert allowed_read.status_code == 200
    assert allowed_write.status_code == 200
    airport.refresh_from_db()
    assert airport.terminal_guidance == "Rendez-vous porte 4."
    audit = LogEntry.objects.get(object_id=str(airport.pk), action_flag=CHANGE)
    assert audit.user_id == staff.pk
    assert "terminal_guidance" in audit.change_message


@pytest.mark.django_db
def test_non_staff_user_cannot_use_staff_api_even_with_model_permission(client, priced_route):
    airport, _, _, _ = priced_route
    customer = User.objects.create_user(
        email="customer@example.com", password="Long-unique-passphrase-729!"
    )
    customer.user_permissions.add(Permission.objects.get(codename="view_airport"))
    client.force_login(customer)

    response = client.get(reverse("staff:airport-detail", args=[airport.public_id]))

    assert response.status_code == 403


@pytest.mark.django_db
def test_active_airports_publish_without_tariffs_but_service_areas_require_one(client, priced_route):
    airport, area, tariff, _ = priced_route
    uncovered_airport = Airport.objects.create(
        name="Uncovered active airport",
        iata_code="UNC",
        slug="uncovered-active-airport",
        city="Paris",
        address="Unpublished",
        latitude=0,
        longitude=0,
    )
    uncovered_area = ServiceArea.objects.create(
        name="Uncovered active area",
        slug="uncovered-active-area",
        area_type=ServiceArea.AreaType.CITY,
    )

    airport_list = client.get(reverse("locations:airport-list")).json()
    area_list = client.get(reverse("locations:service-area-list")).json()
    assert [item["public_id"] for item in airport_list] == [
        str(airport.public_id),
        str(uncovered_airport.public_id),
    ]
    assert [item["public_id"] for item in area_list] == [str(area.public_id)]
    assert (
        client.get(reverse("locations:airport-detail", args=[uncovered_airport.slug])).status_code
        == 200
    )
    assert (
        client.get(reverse("locations:service-area-detail", args=[uncovered_area.slug])).status_code
        == 404
    )

    tariff.is_active = False
    tariff.save(update_fields=("is_active", "updated_at"))
    assert [item["public_id"] for item in client.get(reverse("locations:airport-list")).json()] == [
        str(airport.public_id),
        str(uncovered_airport.public_id),
    ]
    assert client.get(reverse("locations:service-area-list")).json() == []

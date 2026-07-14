import pytest
from django.urls import reverse

from apps.accounts.models import User
from apps.locations.models import Airport, ServiceArea
from apps.operations.models import DriverInquiry, MarketplaceDriverProfile


@pytest.fixture
def marketplace_driver(db):
    user = User.objects.create_user(email="driver@example.com", password="Long-unique-passphrase-729!", first_name="Marie", last_name="VTC", phone="+33600000000")
    airport = Airport.objects.create(name="Paris CDG", iata_code="CDG", slug="cdg", city="Paris", address="Test", latitude=48, longitude=2)
    area = ServiceArea.objects.create(name="Paris", slug="paris", area_type="city", city="Paris")
    profile = MarketplaceDriverProfile.objects.create(user=user, display_name="Marie VTC", phone=user.phone, verification_status="verified", is_published=True)
    profile.airports.add(airport)
    profile.service_areas.add(area)
    return profile, airport


@pytest.mark.django_db
def test_directory_only_exposes_verified_published_profiles(client, marketplace_driver):
    profile, _ = marketplace_driver
    response = client.get(reverse("marketplace:driver-list"))
    assert response.status_code == 200
    assert response.json()[0]["public_id"] == str(profile.public_id)
    profile.verification_status = "pending"
    profile.save(update_fields=("verification_status",))
    assert client.get(reverse("marketplace:driver-list")).json() == []


@pytest.mark.django_db
def test_inquiry_is_non_binding_and_scoped_to_published_driver(client, marketplace_driver):
    profile, airport = marketplace_driver
    response = client.post(reverse("marketplace:inquiry-create"), {
        "driver_id": str(profile.public_id), "airport_id": str(airport.public_id),
        "customer_name": "Jean Client", "customer_email": "jean@example.com",
        "customer_phone": "+33611111111", "destination": "Paris 15e", "passenger_count": 2,
    }, content_type="application/json")
    assert response.status_code == 201
    assert "ni une reservation ni un prix confirme" in response.json()["message"]
    assert DriverInquiry.objects.filter(driver=profile, status="new").exists()


@pytest.mark.django_db
def test_driver_owns_profile_and_inquiry_dashboard(client, marketplace_driver):
    profile, _ = marketplace_driver
    client.force_login(profile.user)
    own = client.get(reverse("marketplace:my-profile"))
    inbox = client.get(reverse("marketplace:my-inquiries"))
    assert own.status_code == 200
    assert own.json()["display_name"] == "Marie VTC"
    assert inbox.status_code == 200

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from apps.content.models import (
    FAQ,
    BusinessSettings,
    LegalDocument,
    ServiceContent,
)
from apps.content.models import Testimonial as CustomerReview
from apps.locations.models import Airport


@pytest.mark.django_db
def test_public_content_returns_only_publishable_records(client):
    BusinessSettings.objects.create(business_name="Accueil Privé", phone="+33123456789")
    ServiceContent.objects.create(
        slug="accueil-aeroport", title="Accueil aéroport", summary="Un accueil organisé."
    )
    ServiceContent.objects.create(slug="hidden", title="Hidden", summary="Hidden", is_active=False)
    FAQ.objects.create(question="Comment ?", answer="Nous confirmons chaque trajet.")
    testimonial = CustomerReview.objects.create(
        author_name="Marie",
        quote="Un trajet ponctuel.",
        rating=5,
        source_reference="consent-001",
        verified_at=timezone.now(),
        is_active=True,
    )
    CustomerReview.objects.create(
        author_name="Unverified",
        quote="Must stay private.",
        rating=5,
        source_reference="pending",
        is_active=False,
    )
    LegalDocument.objects.create(
        kind=LegalDocument.Kind.PRIVACY,
        version="1.0",
        title="Confidentialité",
        body="Texte approuvé.",
        effective_at=timezone.now(),
        is_published=True,
    )

    response = client.get(reverse("content:public-content"))

    assert response.status_code == 200
    payload = response.json()
    assert payload["settings"]["business_name"] == "Accueil Privé"
    assert [service["slug"] for service in payload["services"]] == ["accueil-aeroport"]
    assert [item["public_id"] for item in payload["testimonials"]] == [str(testimonial.public_id)]
    assert "source_reference" not in payload["testimonials"][0]
    assert payload["legal_documents"][0]["version"] == "1.0"
    assert response.headers["Cache-Control"] == "public, max-age=60"


@pytest.mark.django_db
def test_public_content_supports_etag_revalidation(client):
    first = client.get(reverse("content:public-content"))
    second = client.get(reverse("content:public-content"), HTTP_IF_NONE_MATCH=first.headers["ETag"])

    assert first.status_code == 200
    assert second.status_code == 304
    assert second.headers["ETag"] == first.headers["ETag"]


@pytest.mark.django_db
def test_public_content_does_not_create_default_settings_on_get(client):
    client.get(reverse("content:public-content"))

    assert not BusinessSettings.objects.exists()


@pytest.mark.django_db
def test_active_testimonial_requires_verification():
    testimonial = CustomerReview(
        author_name="Unknown",
        quote="Not verified.",
        rating=5,
        source_reference="pending",
        is_active=True,
    )

    with pytest.raises(ValidationError):
        testimonial.full_clean()


@pytest.mark.django_db
def test_marketplace_content_command_is_idempotent():
    call_command("publish_marketplace_content")
    call_command("publish_marketplace_content")

    settings = BusinessSettings.objects.get(pk=1)
    assert settings.business_name == "Airproche"
    assert settings.email == "info@gestionatech.de"
    assert settings.booking_enabled is False
    assert LegalDocument.objects.filter(is_published=True).count() == 6
    assert LegalDocument.objects.filter(kind="transparency").exists()
    assert FAQ.objects.filter(is_active=True).count() == 8
    assert list(Airport.objects.values_list("iata_code", flat=True)) == ["CDG", "ORY", "BVA"]

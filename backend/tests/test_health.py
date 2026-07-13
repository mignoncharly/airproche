import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_live_health_is_public_and_has_request_id(client):
    response = client.get(reverse("core:health-live"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]
    assert (
        response.headers["Cache-Control"]
        == "max-age=0, no-cache, no-store, must-revalidate, private"
    )


@pytest.mark.django_db
def test_ready_health_checks_database(client):
    response = client.get(reverse("core:health-ready"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_invalid_caller_request_id_is_replaced(client):
    response = client.get(reverse("core:health-live"), HTTP_X_REQUEST_ID="bad value")

    assert response.headers["X-Request-ID"] != "bad value"

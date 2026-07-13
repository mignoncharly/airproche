import pytest

from apps.accounts.models import User


@pytest.mark.django_db
def test_user_manager_normalizes_email_and_does_not_use_username():
    user = User.objects.create_user(email="Person@EXAMPLE.COM", password="a-safe-test-password")

    assert user.email == "person@example.com"
    assert "username" not in {field.name for field in User._meta.get_fields()}
    assert user.check_password("a-safe-test-password")


@pytest.mark.django_db
def test_public_user_id_is_not_the_database_id():
    user = User.objects.create_user(email="person@example.com", password="a-safe-test-password")

    assert str(user.public_id) != str(user.pk)

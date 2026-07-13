from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import password_validation
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.content.models import LegalDocument

from .models import AccountToken, User

logger = logging.getLogger(__name__)


def token_digest(raw_token: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), raw_token.encode(), hashlib.sha256).hexdigest()


def issue_account_token(user: User, purpose: str) -> str:
    now = timezone.now()
    lifetime = timedelta(hours=24 if purpose == AccountToken.Purpose.VERIFY_EMAIL else 1)
    AccountToken.objects.filter(user=user, purpose=purpose, consumed_at__isnull=True).update(
        consumed_at=now
    )
    raw_token = secrets.token_urlsafe(32)
    AccountToken.objects.create(
        user=user,
        purpose=purpose,
        token_digest=token_digest(raw_token),
        expires_at=now + lifetime,
    )
    return raw_token


def registration_documents() -> dict[str, LegalDocument]:
    result: dict[str, LegalDocument] = {}
    mapping = {
        "terms": LegalDocument.Kind.TERMS,
        "privacy": LegalDocument.Kind.PRIVACY,
    }
    for key, kind in mapping.items():
        document = (
            LegalDocument.objects.filter(
                kind=kind,
                is_published=True,
                effective_at__lte=timezone.now(),
            )
            .order_by("-effective_at")
            .first()
        )
        if document:
            result[key] = document
    return result


def _get_valid_token(raw_token: str, purpose: str) -> AccountToken:
    if not raw_token or len(raw_token) > 256:
        raise ValidationError({"token": "Ce lien est invalide ou a expiré."})
    try:
        token = (
            AccountToken.objects.select_for_update()
            .select_related("user")
            .get(token_digest=token_digest(raw_token), purpose=purpose)
        )
    except AccountToken.DoesNotExist as exc:
        raise ValidationError({"token": "Ce lien est invalide ou a expiré."}) from exc
    if token.consumed_at or token.expires_at <= timezone.now() or not token.user.is_active:
        raise ValidationError({"token": "Ce lien est invalide ou a expiré."})
    return token


@transaction.atomic
def verify_email_token(raw_token: str) -> User:
    token = _get_valid_token(raw_token, AccountToken.Purpose.VERIFY_EMAIL)
    now = timezone.now()
    token.consumed_at = now
    token.save(update_fields=("consumed_at",))
    user = token.user
    if not user.email_verified_at:
        user.email_verified_at = now
        user.save(update_fields=("email_verified_at",))
    AccountToken.objects.filter(
        user=user,
        purpose=AccountToken.Purpose.VERIFY_EMAIL,
        consumed_at__isnull=True,
    ).update(consumed_at=now)
    return user


@transaction.atomic
def reset_password_with_token(raw_token: str, new_password: str) -> User:
    token = _get_valid_token(raw_token, AccountToken.Purpose.RESET_PASSWORD)
    user = token.user
    password_validation.validate_password(new_password, user=user)
    user.set_password(new_password)
    user.save(update_fields=("password",))
    now = timezone.now()
    AccountToken.objects.filter(
        user=user,
        purpose=AccountToken.Purpose.RESET_PASSWORD,
        consumed_at__isnull=True,
    ).update(consumed_at=now)
    return user


def send_verification_email(user: User, raw_token: str) -> bool:
    link = f"{settings.APP_BASE_URL}/verification-email?token={raw_token}"
    try:
        sent = send_mail(
            "Vérifiez votre adresse e-mail",
            (
                f"Bonjour {user.first_name},\n\n"
                "Confirmez votre adresse e-mail en ouvrant ce lien valable 24 heures :\n"
                f"{link}\n\n"
                "Si vous n’avez pas créé ce compte, ignorez ce message."
            ),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return sent == 1
    except Exception:
        logger.exception("Account email delivery failed", extra={"event": "email_verify_failed"})
        return False


def send_password_reset_email(user: User, raw_token: str) -> bool:
    link = f"{settings.APP_BASE_URL}/reinitialiser-mot-de-passe?token={raw_token}"
    try:
        sent = send_mail(
            "Réinitialisez votre mot de passe",
            (
                f"Bonjour {user.first_name},\n\n"
                "Choisissez un nouveau mot de passe avec ce lien valable une heure :\n"
                f"{link}\n\n"
                "Si vous n’avez pas demandé ce changement, ignorez ce message."
            ),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return sent == 1
    except Exception:
        logger.exception("Account email delivery failed", extra={"event": "password_reset_failed"})
        return False

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class StripeConfigurationError(Exception):
    pass


class StripeProviderError(Exception):
    def __init__(self, message: str, code: str = "stripe_provider_error"):
        super().__init__(message)
        self.code = code


def configuration() -> dict[str, str]:
    secret = os.getenv("STRIPE_SECRET_KEY", "").strip()
    webhook = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    configured_environment = os.getenv("STRIPE_ENVIRONMENT", "test").strip().lower()
    if configured_environment not in {"test", "live"}:
        raise StripeConfigurationError("STRIPE_ENVIRONMENT must be test or live.")
    if not secret:
        raise StripeConfigurationError("Stripe is not configured.")
    if configured_environment == "test" and not secret.startswith("sk_test_"):
        raise StripeConfigurationError("A test Stripe environment requires a test secret key.")
    if configured_environment == "live" and not secret.startswith("sk_live_"):
        raise StripeConfigurationError("A live Stripe environment requires a live secret key.")
    live_confirmed = os.getenv("STRIPE_LIVE_MODE_CONFIRMED", "").strip().lower() in {
        "1", "true", "yes", "on"
    }
    if configured_environment == "live" and not live_confirmed:
        raise StripeConfigurationError(
            "Live Stripe mode requires explicit STRIPE_LIVE_MODE_CONFIRMED=true."
        )
    return {"secret_key": secret, "webhook_secret": webhook, "environment": configured_environment}


def _request(method: str, path: str, *, data: dict[str, str] | None = None, idempotency_key: str = "") -> dict:
    config = configuration()
    body = urlencode(data or {}).encode() if data is not None else None
    headers = {"Authorization": f"Bearer {config['secret_key']}", "Content-Type": "application/x-www-form-urlencoded"}
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    request = Request(f"https://api.stripe.com/v1/{path.lstrip('/')}", data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            payload = {}
        error = payload.get("error", {}) if isinstance(payload, dict) else {}
        raise StripeProviderError(error.get("message", "Stripe a refusé la demande."), error.get("code", "stripe_provider_error")) from exc
    except (URLError, TimeoutError) as exc:
        raise StripeProviderError("Stripe est momentanément indisponible.", "stripe_unavailable") from exc
    if not isinstance(payload, dict):
        raise StripeProviderError("Réponse Stripe invalide.")
    return payload


def create_checkout_session(*, amount_minor: int, currency: str, booking_reference: str, booking_public_id: str, payment_public_id: str, customer_email: str, success_url: str, cancel_url: str, idempotency_key: str) -> dict:
    return _request(
        "POST", "checkout/sessions", idempotency_key=idempotency_key,
        data={
            "mode": "payment", "success_url": success_url, "cancel_url": cancel_url,
            "client_reference_id": booking_reference, "customer_email": customer_email,
            "line_items[0][price_data][currency]": currency.lower(),
            "line_items[0][price_data][product_data][name]": f"Transfert {booking_reference}",
            "line_items[0][price_data][unit_amount]": str(amount_minor),
            "line_items[0][price_data][product_data][metadata][booking_reference]": booking_reference,
            "line_items[0][quantity]": "1",
            "metadata[booking_public_id]": booking_public_id,
            "metadata[booking_reference]": booking_reference,
            "metadata[payment_public_id]": payment_public_id,
            "metadata[environment]": configuration()["environment"],
        },
    )


def retrieve_checkout_session(session_id: str) -> dict:
    return _request("GET", f"checkout/sessions/{session_id}")


def create_refund(*, payment_intent_id: str, amount_minor: int, reason: str, idempotency_key: str) -> dict:
    data = {"payment_intent": payment_intent_id, "amount": str(amount_minor)}
    if reason:
        data["metadata[reason]"] = reason[:300]
    return _request("POST", "refunds", data=data, idempotency_key=idempotency_key)


def verify_signature(payload: bytes, signature_header: str, *, tolerance_seconds: int = 300) -> dict:
    config = configuration()
    if not config["webhook_secret"]:
        raise StripeConfigurationError("Stripe webhook secret is not configured.")
    values: dict[str, list[str]] = {}
    for item in signature_header.split(","):
        key, _, value = item.partition("=")
        values.setdefault(key, []).append(value)
    timestamp = values.get("t", [""])[0]
    try:
        timestamp_int = int(timestamp)
    except ValueError as exc:
        raise StripeProviderError("Signature Stripe invalide.", "invalid_signature") from exc
    if abs(int(time.time()) - timestamp_int) > tolerance_seconds:
        raise StripeProviderError("Signature Stripe expirée.", "invalid_signature")
    signed = f"{timestamp}.{payload.decode('utf-8')}".encode()
    expected = hmac.new(config["webhook_secret"].encode(), signed, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, candidate) for candidate in values.get("v1", [])):
        raise StripeProviderError("Signature Stripe invalide.", "invalid_signature")
    try:
        event = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StripeProviderError("Payload Stripe invalide.", "invalid_payload") from exc
    if not isinstance(event, dict) or not event.get("id") or not event.get("type"):
        raise StripeProviderError("Événement Stripe invalide.", "invalid_payload")
    return event


def redacted_event_payload(event: dict) -> dict:
    obj = event.get("data", {}).get("object", {}) if isinstance(event.get("data"), dict) else {}
    metadata = obj.get("metadata", {}) if isinstance(obj, dict) else {}
    safe_metadata = {key: str(metadata[key])[:160] for key in ("booking_public_id", "booking_reference", "payment_public_id", "environment") if key in metadata}
    return {
        "id": event.get("id"), "type": event.get("type"), "object_id": obj.get("id") if isinstance(obj, dict) else None,
        "metadata": safe_metadata, "amount_total": obj.get("amount_total") if isinstance(obj, dict) else None,
        "amount": obj.get("amount") if isinstance(obj, dict) else None, "currency": obj.get("currency") if isinstance(obj, dict) else None,
        "payment_status": obj.get("payment_status") if isinstance(obj, dict) else None,
        "payment_intent": obj.get("payment_intent") if isinstance(obj, dict) else None,
        "status": obj.get("status") if isinstance(obj, dict) else None,
    }

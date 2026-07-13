from __future__ import annotations

import ipaddress
import re
import uuid
from collections.abc import Callable
from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.cache import patch_cache_control

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,128}$")
UNSAFE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
ORIGIN_EXEMPT_PATHS = {"/api/v1/payments/webhooks/stripe/"}
STAFF_PATHS = (
    re.compile(r"^/django-admin(?:/|$)"),
    re.compile(r"^/api/v1/staff(?:/|$)"),
    re.compile(r"^/api/v1/bookings/[0-9a-f-]+/transition/$"),
    re.compile(r"^/api/v1/payments/[0-9a-f-]+/(?:reconcile|refund)/$"),
)


def _origin(value: str) -> str | None:
    try:
        parsed = urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return None
    default_port = 443 if parsed.scheme == "https" else 80
    port = parsed.port or default_port
    suffix = "" if port == default_port else f":{port}"
    return f"{parsed.scheme}://{parsed.hostname.lower()}{suffix}"


def allowed_request_origins() -> set[str]:
    configured = [settings.APP_BASE_URL, *settings.CSRF_TRUSTED_ORIGINS]
    return {origin for value in configured if (origin := _origin(value))}


def _error(request: HttpRequest, code: str, message: str, status: int) -> JsonResponse:
    return JsonResponse(
        {
            "error": {
                "code": code,
                "message": message,
                "fields": None,
                "request_id": getattr(request, "correlation_id", None),
            }
        },
        status=status,
    )


class CorrelationIdMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        supplied = request.headers.get("X-Request-ID", "")
        request.correlation_id = (
            supplied if REQUEST_ID_PATTERN.fullmatch(supplied) else uuid.uuid4().hex
        )
        response = self.get_response(request)
        response["X-Request-ID"] = request.correlation_id
        return response


class ApiOriginMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if (
            request.path.startswith("/api/")
            and request.method in UNSAFE_METHODS
            and request.path not in ORIGIN_EXEMPT_PATHS
        ):
            supplied = request.headers.get("Origin") or request.headers.get("Referer", "")
            supplied_origin = _origin(supplied) if supplied else None
            if supplied and supplied_origin not in allowed_request_origins():
                return _error(request, "invalid_origin", "Origine de requête refusée.", 403)
            if settings.REQUIRE_API_ORIGIN and not supplied:
                return _error(request, "missing_origin", "Origine de requête requise.", 403)
        return self.get_response(request)


class PrivateResponseCacheMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        if not request.path.startswith("/api/"):
            return response
        cache_control = response.get("Cache-Control", "")
        is_explicitly_public = "public" in cache_control.lower()
        is_authenticated = bool(getattr(request, "user", None) and request.user.is_authenticated)
        has_session = settings.SESSION_COOKIE_NAME in request.COOKIES
        if (
            not is_explicitly_public
            or is_authenticated
            or has_session
            or response.has_header("Set-Cookie")
        ):
            patch_cache_control(response, no_store=True, private=True)
            response["Pragma"] = "no-cache"
        return response


def _network_list(values: list[str]):
    return tuple(ipaddress.ip_network(value, strict=False) for value in values)


def request_client_ip(request: HttpRequest) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        remote = ipaddress.ip_address(request.META.get("REMOTE_ADDR", ""))
    except ValueError:
        return None
    trusted_proxies = _network_list(settings.TRUSTED_PROXY_NETWORKS)
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded and any(remote in network for network in trusted_proxies):
        candidate = forwarded.split(",", 1)[0].strip()
        try:
            return ipaddress.ip_address(candidate)
        except ValueError:
            return None
    return remote


class StaffNetworkGateMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not settings.STAFF_NETWORK_GATE_ENABLED or not any(
            pattern.match(request.path) for pattern in STAFF_PATHS
        ):
            return self.get_response(request)
        client_ip = request_client_ip(request)
        allowed = _network_list(settings.STAFF_ALLOWED_NETWORKS)
        if client_ip is None or not any(client_ip in network for network in allowed):
            return _error(request, "staff_network_denied", "Accès réseau refusé.", 403)
        return self.get_response(request)

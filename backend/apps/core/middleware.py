from __future__ import annotations

import re
import uuid
from collections.abc import Callable

from django.http import HttpRequest, HttpResponse

REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{8,128}$")


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

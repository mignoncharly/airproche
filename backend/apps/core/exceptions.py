from __future__ import annotations

from typing import Any

from rest_framework.response import Response
from rest_framework.views import exception_handler


def first_error_message(detail: Any) -> str | None:
    if isinstance(detail, dict):
        for value in detail.values():
            message = first_error_message(value)
            if message:
                return message
    elif isinstance(detail, (list, tuple)):
        for value in detail:
            message = first_error_message(value)
            if message:
                return message
    elif detail is not None:
        return str(detail)
    return None


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None

    request = context.get("request")
    correlation_id = getattr(request, "correlation_id", None)
    detail = response.data
    field_errors = detail if isinstance(detail, dict) else None
    message = "La demande n’a pas pu être traitée."
    code = "request_error"

    if isinstance(detail, dict) and "detail" in detail:
        message = str(detail["detail"])
        code_getter = getattr(detail["detail"], "code", None)
        if code_getter:
            code = str(code_getter)
    elif field_errors:
        message = first_error_message(field_errors) or message

    response.data = {
        "error": {
            "code": code,
            "message": message,
            "fields": field_errors,
            "request_id": correlation_id,
        }
    }
    return response

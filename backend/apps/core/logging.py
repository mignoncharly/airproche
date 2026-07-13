from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime

REDACTIONS = (
    (re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b"), "[redacted-email]"),
    (re.compile(r"\b(?:sk_(?:live|test)|whsec)_[A-Za-z0-9_-]+\b"), "[redacted-provider-secret]"),
    (re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]+=*"), "Bearer [redacted]"),
    (re.compile(r"(?i)([?#&](?:token|session_id)=)[^&\s]+"), r"\1[redacted]"),
    (re.compile(r"(?i)(postgres(?:ql)?://)[^\s@]+@"), r"\1[redacted]@"),
    (re.compile(r"(?:\+?\d[\s().-]*){8,}"), "[redacted-phone]"),
)


def redact_text(value: object) -> str:
    result = str(value)
    for pattern, replacement in REDACTIONS:
        result = pattern.sub(replacement, result)
    return result


class JsonFormatter(logging.Formatter):
    """Structured formatter with an explicit field allow-list and value redaction."""

    allowed_fields = ("correlation_id", "event", "status_code", "provider")

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact_text(record.getMessage()),
        }
        for field in self.allowed_fields:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = redact_text(value)
        if record.exc_info:
            payload["exception"] = redact_text(self.formatException(record.exc_info))
        return json.dumps(payload, ensure_ascii=False)

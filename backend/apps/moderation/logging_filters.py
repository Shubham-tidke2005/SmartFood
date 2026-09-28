import logging
import re
from collections.abc import Mapping


REDACTED = "[REDACTED]"

SENSITIVE_KEYS = {
    "password",
    "password_confirm",
    "new_password",
    "new_password_confirm",
    "old_password",
    "token",
    "access",
    "access_token",
    "refresh",
    "refresh_token",
    "authorization",
    "cookie",
    "set-cookie",
    "secret",
    "api_key",
    "apikey",
    "document",
    "documents",
    "file",
    "file_content",
}

SENSITIVE_TEXT_PATTERNS = [
    re.compile(
        r"(?i)"
        r"(password|password_confirm|new_password|"
        r"new_password_confirm|old_password|token|"
        r"access_token|refresh_token|authorization|"
        r"api[_-]?key|secret)"
        r"(\s*[=:]\s*)"
        r"([^\s,;&]+)"
    ),
    re.compile(
        r"(?i)"
        r"(Bearer\s+)"
        r"[A-Za-z0-9\-._~+/]+=*"
    ),
    re.compile(
        r"(?i)"
        r"(sf_refresh=)"
        r"[^;\s]+"
    ),
]


def is_sensitive_key(key):
    normalized = str(key).strip().lower()

    return (
        normalized in SENSITIVE_KEYS
        or "password" in normalized
        or "token" in normalized
        or "secret" in normalized
        or "authorization" in normalized
        or "cookie" in normalized
    )


def redact_text(value):
    text = value

    for pattern in SENSITIVE_TEXT_PATTERNS:
        if pattern.pattern.lower().startswith(
            "(?i)(bearer"
        ):
            text = pattern.sub(
                rf"\1{REDACTED}",
                text,
            )
        else:
            text = pattern.sub(
                rf"\1\2{REDACTED}",
                text,
            )

    return text


def redact_value(value, key=None):
    if key is not None and is_sensitive_key(key):
        return REDACTED

    if isinstance(value, Mapping):
        return {
            item_key: redact_value(
                item_value,
                key=item_key,
            )
            for item_key, item_value in value.items()
        }

    if isinstance(value, tuple):
        return tuple(
            redact_value(item)
            for item in value
        )

    if isinstance(value, list):
        return [
            redact_value(item)
            for item in value
        ]

    if isinstance(value, set):
        return {
            redact_value(item)
            for item in value
        }

    if isinstance(value, str):
        return redact_text(value)

    return value


class SensitiveDataFilter(logging.Filter):
    """
    Remove common credentials and secrets from log messages.

    This filter intentionally has no Django model imports because
    logging is configured before Django finishes loading apps.
    """

    def filter(self, record):
        try:
            if isinstance(record.msg, str):
                record.msg = redact_text(
                    record.msg
                )
            else:
                record.msg = redact_value(
                    record.msg
                )

            if record.args:
                record.args = redact_value(
                    record.args
                )

            # Do not replace or modify record.request. Django's
            # request and server log formatters may require the
            # original HttpRequest object.
        except Exception:
            # A logging filter must never prevent Django from
            # starting or handling a request.
            pass

        return True
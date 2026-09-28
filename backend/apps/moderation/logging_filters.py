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
        r"(?i)(?P<key>\b(?:password|password_confirm|new_password|"
        r"new_password_confirm|old_password|token|access_token|"
        r"refresh_token|authorization|api[_-]?key|secret|sf_refresh)\b)"
        r"(?P<sep>[\"']?\s*[=:]\s*)"
        r"(?P<value>\"(?:\\.|[^\"])*\"|'(?:\\.|[^'])*'|[^\s,;&}]+)"
    ),
    re.compile(
        r"(?i)(?P<key>\bBearer\s+)[A-Za-z0-9\-._~+/]+=*"
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
    # Callbacks avoid invalid backreferences and preserve JSON quoting.
    def replace_secret(match):
        quote = '"' if match.group("value").startswith('"') else ""
        return f"{match.group('key')}{match.group('sep')}{quote}{REDACTED}{quote}"

    text = SENSITIVE_TEXT_PATTERNS[0].sub(
        replace_secret,
        value,
    )
    return SENSITIVE_TEXT_PATTERNS[1].sub(
        lambda match: f"{match.group('key')}{REDACTED}",
        text,
    )


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
                # Format first: password=%s otherwise leaks via record.args.
                try:
                    message = record.getMessage()
                except (TypeError, ValueError):
                    message = str(record.msg)
                record.msg = redact_text(message)
                record.args = ()
            else:
                record.msg = redact_value(
                    record.msg
                )
                if record.args:
                    record.args = redact_value(record.args)

            # Do not replace or modify record.request. Django's
            # request and server log formatters may require the
            # original HttpRequest object.
        except Exception:
            # A logging filter must never prevent Django from
            # starting or handling a request.
            pass

        return True

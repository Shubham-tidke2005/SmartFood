from collections.abc import Mapping

from .audit_models import AuditEvent


SENSITIVE_KEYS = {
    "password",
    "password_confirm",
    "new_password",
    "new_password_confirm",
    "token",
    "access",
    "refresh",
    "authorization",
    "cookie",
    "set-cookie",
    "csrfmiddlewaretoken",
    "file",
    "document",
    "documents",
    "document_content",
    "private_key",
    "secret",
    "client_secret",
}


def is_sensitive_key(key):
    normalized = str(key).lower().replace(
        "-",
        "_",
    )

    return any(
        sensitive_key in normalized
        for sensitive_key in SENSITIVE_KEYS
    )


def sanitize_value(value):
    if isinstance(value, Mapping):
        return {
            str(key): (
                "[REDACTED]"
                if is_sensitive_key(key)
                else sanitize_value(item)
            )
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple)):
        return [
            sanitize_value(item)
            for item in value
        ]

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
            type(None),
        ),
    ):
        return value

    return str(value)


def request_ip_address(request):
    if request is None:
        return None

    # Do not trust X-Forwarded-For unless the deployment
    # proxy is explicitly configured and trusted.
    return request.META.get(
        "REMOTE_ADDR"
    )


def record_audit_event(
    *,
    action,
    target_type,
    target_id,
    actor=None,
    request=None,
    reason="",
    old_values=None,
    new_values=None,
    metadata=None,
):
    return AuditEvent.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        reason=reason,
        old_values=sanitize_value(
            old_values or {}
        ),
        new_values=sanitize_value(
            new_values or {}
        ),
        metadata=sanitize_value(
            metadata or {}
        ),
        ip_address=request_ip_address(
            request
        ),
    )
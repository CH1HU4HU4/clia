"""Central redaction. Every log line and dry-run passes through here."""

from __future__ import annotations

SENSITIVE_KEYS = ("token", "secret", "password", "key", "authorization", "cookie")


def mask(value):
    if not value:
        return value
    text = str(value)
    if len(text) < 20:
        return "****"
    return text[:4] + "****" + text[-4:]


def redact_value(key, value):
    lower = str(key).lower()
    if any(part in lower for part in SENSITIVE_KEYS):
        return mask(value)
    if isinstance(value, dict):
        return {k: redact_value(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact_value(key, v) for v in value]
    return value


def redact_headers(headers):
    return {key: redact_value(key, value) for key, value in headers.items()}


def redact_text(text, secrets):
    if not text:
        return text
    out = str(text)
    for secret in secrets:
        if secret:
            out = out.replace(secret, mask(secret))
    return out

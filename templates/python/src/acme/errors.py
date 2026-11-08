"""Error types, the HTTP-to-exit mapper, and the single error writer."""

from __future__ import annotations

import json
import sys

EXIT_BY_CODE = {
    "unexpected": 1,
    "job_failed": 1,
    "usage": 2,
    "auth_required": 3,
    "forbidden": 4,
    "not_found": 5,
    "conflict": 6,
    "validation": 6,
    "rate_limited": 7,
    "server_error": 7,
    "network_error": 8,
    "timeout": 8,
    "partial_success": 9,
    "confirmation_required": 10,
    "ambiguous_target": 11,
    "diagnostic_failed": 12,
    "cancelled": 130,
}

HTTP_TO_CODE = {
    400: "validation",
    401: "auth_required",
    403: "forbidden",
    404: "not_found",
    409: "conflict",
    422: "validation",
    429: "rate_limited",
}


def code_for_status(status):
    if status in HTTP_TO_CODE:
        return HTTP_TO_CODE[status]
    if status >= 500:
        return "server_error"
    if 400 <= status < 500:
        return "validation"
    return "unexpected"


class CliError(Exception):
    def __init__(self, code, message, hint=None, status=None, retryable=None,
                 request_id=None, target=None, extra=None):
        Exception.__init__(self, message)
        self.code = code
        self.message = message
        self.hint = hint
        self.status = status
        self.request_id = request_id
        self.target = target
        self.extra = extra or {}
        if retryable is None:
            retryable = code in ("rate_limited", "server_error", "network_error", "timeout")
        self.retryable = retryable
        self.exit = EXIT_BY_CODE.get(code, 1)


class UsageError(CliError):
    def __init__(self, message, hint=None):
        CliError.__init__(self, "usage", message, hint)


def target_dict(ctx):
    if ctx is None or not ctx.profile:
        return None
    return {
        "profile": ctx.profile,
        "base_url": ctx.base_url,
        "org": ctx.org,
        "project": ctx.project,
        "api_version": ctx.api_version,
    }


def error_payload(err, ctx=None):
    target = err.target if err.target is not None else target_dict(ctx)
    payload = {
        "error": {
            "code": err.code,
            "message": err.message,
        }
    }
    if err.hint:
        payload["error"]["hint"] = err.hint
    if err.status is not None:
        payload["error"]["status"] = err.status
    if err.request_id:
        payload["error"]["request_id"] = err.request_id
    payload["error"]["retryable"] = bool(err.retryable)
    if target:
        payload["error"]["target"] = target
    payload["error"].update(err.extra)
    return payload


def emit_error(err, ctx=None, json_mode=False):
    """Write the one error representation. Never writes to stdout."""
    if json_mode:
        sys.stderr.write(json.dumps(error_payload(err, ctx), separators=(",", ":")) + "\n")
        return
    sys.stderr.write("error: " + err.message + "\n")
    if err.hint:
        sys.stderr.write("hint: " + err.hint + "\n")
    target = err.target if err.target is not None else target_dict(ctx)
    if target:
        sys.stderr.write(
            "target: profile %s, %s, org %s, project %s, API %s\n"
            % (target["profile"], target["base_url"], target["org"],
               target["project"], target["api_version"])
        )

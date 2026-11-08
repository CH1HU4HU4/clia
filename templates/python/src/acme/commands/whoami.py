"""One-command check: user, org, profile, environment, token expiry."""

from __future__ import annotations

from ..api import Api
from ..output import emit_object
from ..errors import CliError

SPEC = {
    "path": ("whoami",),
    "summary": "Show the current user and target",
    "description": "Show the user, org, profile, environment, and token expiry for the selected target.",
    "arguments": [],
    "flags": [],
    "examples": [
        "acme whoami",
        "acme whoami --json",
    ],
    "related": ["acme auth status", "acme project list"],
    "data": True,
}

FIELDS = [
    ("user", "user"),
    ("org", "org"),
    ("profile", "profile"),
    ("environment", "environment"),
    ("token_expires_at", "token_expires_at"),
    ("base_url", "base_url"),
    ("api_version", "api_version"),
]


def run(ctx, opts, positionals):
    api = Api(ctx)
    me = api.me()
    user = (me.get("user") or {}).get("email")
    payload = {
        "user": user,
        "user_id": (me.get("user") or {}).get("id"),
        "org": me.get("org") or ctx.org,
        "profile": ctx.profile,
        "environment": me.get("environment"),
        "token_expires_at": ctx.expires_at or me.get("token_expires_at"),
        "base_url": ctx.base_url,
        "api_version": ctx.api_version,
    }
    emit_object(payload, ctx, opts, FIELDS)
    return 0

SPEC["run"] = run

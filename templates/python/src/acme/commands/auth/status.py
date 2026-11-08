"""Show authentication state and the resolved target."""

from __future__ import annotations

from ...api import Api
from ...output import emit_object

SPEC = {
    "path": ("auth", "status"),
    "summary": "Show authentication status",
    "description": "Show whether the selected profile is authenticated and which target it uses.",
    "arguments": [],
    "flags": [],
    "examples": [
        "acme auth status",
        "acme auth status --json",
    ],
    "related": ["acme whoami", "acme auth login"],
    "data": True,
}

FIELDS = [
    ("authenticated", "authenticated"),
    ("profile", "profile"),
    ("base_url", "base_url"),
    ("org", "org"),
    ("project", "project"),
    ("api_version", "api_version"),
    ("environment", "environment"),
    ("user", "user"),
    ("expires_at", "expires_at"),
]


def run(ctx, opts, positionals):
    if not ctx.token:
        payload = {
            "authenticated": False,
            "profile": ctx.profile,
            "base_url": ctx.base_url,
            "org": ctx.org or None,
            "project": ctx.project or None,
            "api_version": ctx.api_version,
            "environment": None,
            "user": None,
            "expires_at": None,
        }
        emit_object(payload, ctx, opts, FIELDS)
        return 0
    api = Api(ctx)
    me = api.me()
    payload = {
        "authenticated": True,
        "profile": ctx.profile,
        "base_url": ctx.base_url,
        "org": me.get("org") or ctx.org,
        "project": ctx.project or None,
        "api_version": ctx.api_version,
        "environment": me.get("environment"),
        "user": (me.get("user") or {}).get("email"),
        "expires_at": ctx.expires_at or me.get("token_expires_at"),
    }
    emit_object(payload, ctx, opts, FIELDS)
    return 0

SPEC["run"] = run

"""Remove the local credential for the selected profile."""

from __future__ import annotations

from ...output import print_json, print_text
from ... import config as config_store

SPEC = {
    "path": ("auth", "logout"),
    "summary": "Log out",
    "description": "Remove the stored access and refresh tokens for the selected profile.",
    "arguments": [],
    "flags": [],
    "examples": [
        "acme auth logout",
        "acme auth logout --json",
    ],
    "related": ["acme auth login", "acme auth status"],
    "data": True,
}


def run(ctx, opts, positionals):
    for key in ("access_token", "refresh_token", "expires_at"):
        try:
            config_store.unset_value(ctx.profile, key)
        except Exception:
            pass
    payload = {"ok": True, "logged_out": True, "profile": ctx.profile}
    if ctx.output == "json":
        print_json(payload)
    else:
        print_text("Logged out of profile %s." % ctx.profile)
    return 0

SPEC["run"] = run

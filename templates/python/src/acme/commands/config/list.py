"""List resolved config values, never raw secrets."""

from __future__ import annotations

from ... import config as config_store
from ...output import emit_list
from . import common

SPEC = {
    "path": ("config", "list"),
    "summary": "List config values",
    "description": "List every known key in the selected profile with its source. Secrets are masked.",
    "arguments": [],
    "flags": [],
    "examples": [
        "acme config list",
        "acme config list --json",
    ],
    "related": ["acme config get <key>", "acme auth status"],
    "data": True,
}

COLUMNS = [("key", "key", 22), ("value", "value", 50), ("source", "source", 10)]


def run(ctx, opts, positionals):
    values = config_store.profile_values(ctx.config_data, ctx.profile) or {}
    rows = []
    for key in common.KEYS:
        if key == "profile":
            value = ctx.profile
        elif key == "access_token" and ctx.token:
            value = ctx.token
        else:
            value = values.get(key)
        rows.append({
            "key": key,
            "value": common.display(key, value),
            "source": common.source(ctx.profile, key),
        })
    emit_list(rows, ctx, opts, COLUMNS, "config keys", has_more=False,
              next_cursor=None, truncated=False, empty_message="No config values.")
    return 0

SPEC["run"] = run

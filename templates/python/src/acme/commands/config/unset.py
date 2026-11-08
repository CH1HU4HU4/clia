"""Remove one config value from a profile."""

from __future__ import annotations

from ... import config as config_store
from ...output import emit_object
from . import common

SPEC = {
    "path": ("config", "unset"),
    "summary": "Remove a config value",
    "description": "Remove one key from the selected profile and fall back to the default.",
    "arguments": [{"name": "key", "description": "Config key", "required": True}],
    "flags": [],
    "examples": [
        "acme config unset project",
        "acme config unset access-token --json",
    ],
    "related": ["acme config list", "acme config get <key>"],
    "data": True,
}

FIELDS = [("ok", "ok"), ("key", "key"), ("profile", "profile")]


def run(ctx, opts, positionals):
    key = common.validate_key(positionals[0])
    config_store.unset_value(ctx.profile, key)
    emit_object({"ok": True, "key": key, "profile": ctx.profile}, ctx, opts, FIELDS)
    return 0

SPEC["run"] = run

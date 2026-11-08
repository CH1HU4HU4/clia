"""Write one config value for a profile."""

from __future__ import annotations

from ... import config as config_store
from ...output import emit_object
from . import common

SPEC = {
    "path": ("config", "set"),
    "summary": "Write a config value",
    "description": "Write one value to the user config (0600). Creates the profile section if needed.",
    "arguments": [
        {"name": "key", "description": "Config key", "required": True},
        {"name": "value", "description": "New value", "required": True},
    ],
    "flags": [],
    "examples": [
        "acme config set base-url https://api.acme.com",
        "acme config set output json --profile ci",
    ],
    "related": ["acme config get <key>", "acme config unset <key>"],
    "data": True,
}

FIELDS = [("key", "key"), ("profile", "profile"), ("ok", "ok")]


def run(ctx, opts, positionals):
    key = common.validate_key(positionals[0])
    value = common.validate_value(key, positionals[1])
    profile = ctx.profile
    config_store.set_value(profile, key, value, create=True)
    payload = {"ok": True, "key": key, "profile": profile}
    emit_object(payload, ctx, opts, FIELDS)
    return 0

SPEC["run"] = run

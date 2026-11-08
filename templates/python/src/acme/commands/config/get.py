"""Read one config value and show where it came from."""

from __future__ import annotations

from ... import config as config_store
from ...output import emit_object
from . import common

SPEC = {
    "path": ("config", "get"),
    "summary": "Read a config value",
    "description": "Print one resolved config value and its source (flag, env, file, default).",
    "arguments": [{"name": "key", "description": "Config key", "required": True}],
    "flags": [],
    "examples": [
        "acme config get base-url",
        "acme config get output --json",
    ],
    "related": ["acme config list", "acme config set <key> <value>"],
    "data": True,
}

FIELDS = [("key", "key"), ("value", "value"), ("source", "source"), ("profile", "profile")]


def run(ctx, opts, positionals):
    key = common.validate_key(positionals[0])
    if key == "profile":
        value = ctx.profile
    elif key == "access_token" and ctx.token:
        value = ctx.token
    else:
        values = config_store.profile_values(ctx.config_data, ctx.profile) or {}
        value = values.get(key)
    payload = {
        "key": key,
        "value": common.display(key, value),
        "source": common.source(ctx.profile, key),
        "profile": ctx.profile,
    }
    emit_object(payload, ctx, opts, FIELDS)
    return 0

SPEC["run"] = run

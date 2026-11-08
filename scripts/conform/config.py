"""Conformance configuration: defaults plus conformance.json."""

from __future__ import annotations

import json
import os

DEFAULTS = {
    "name": "cli",
    "tool": None,
    "profile": "default",
    "token_env": "ACME_TOKEN",
    "token": "test-token",
    "bad_token": "bad-token",
    "api_prefix": "/v1",
    "resource": "project",
    "sample_id": "prj_001",
    "ambiguous": "dupe",
    "missing_id": "prj_missing",
    "forbidden_id": "prj_forbidden",
    "rate_limit_id": "prj_ratelimit",
    "server_error_id": "prj_servererror",
    "slow_id": "prj_slow",
    "create_name": "clia-check",
    "conflict_name": "existing",
    "update_set": ["status=paused"],
    "update_unset": ["description"],
    "capabilities": {
        "jobs": False,
        "bulk": False,
        "files": False,
        "doctor": False,
        "schema": True,
        "completions": True,
        "update_check": False,
        "refresh": True,
        "idempotency": True,
    },
    "startup_budget_ms": 300,
    "key_case": "snake",
    "setup": [["config", "set", "base-url", "{base_url}"]],
    "login": ["auth", "login", "--token", "{token}"],
    "test_command": None,
    "golden_dir": "tests/golden",
    "install_line": None,
    "config_path": "{xdg}/{tool}/config.toml",
}


def _merge(base, overlay):
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            merged[key] = _merge(base[key], value)
        else:
            merged[key] = value
    return merged


def load(path):
    if not path or not os.path.exists(path):
        return dict(DEFAULTS)
    with open(path, encoding="utf-8") as stream:
        overlay = json.load(stream)
    return _merge(DEFAULTS, overlay)


def expand(template, values):
    text = str(template)
    for key, value in values.items():
        text = text.replace("{%s}" % key, str(value))
    return text

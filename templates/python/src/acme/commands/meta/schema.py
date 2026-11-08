"""Describe the command tree as JSON for agents that load help once."""

from __future__ import annotations

from ...constants import TOOL, VERSION
from ...output import print_json

SPEC = {
    "path": ("schema",),
    "summary": "Describe the command tree",
    "description": "Print the command tree, arguments, flags, defaults, and examples as one JSON document.",
    "arguments": [],
    "flags": [],
    "examples": ["acme schema", "acme schema | jq '.commands[].path'"],
    "data": False,
}


def _flag_payload(item):
    payload = {
        "name": item["long"],
        "type": item["kind"],
        "description": item.get("desc", ""),
    }
    if item.get("metavar"):
        payload["metavar"] = item["metavar"]
    if item.get("default") not in (None, ""):
        payload["default"] = item["default"]
    if item.get("env"):
        payload["env"] = item["env"]
    if item.get("short"):
        payload["short"] = item["short"]
    return payload


def run(ctx, opts, positionals):
    from ...args import GLOBAL_FLAGS
    from .. import all_specs
    specs = all_specs()
    commands = []
    for path in sorted(specs):
        spec = specs[path]
        if spec.get("group"):
            continue
        commands.append({
            "path": list(path),
            "summary": spec["summary"],
            "description": spec.get("description", ""),
            "arguments": spec.get("arguments", []),
            "flags": [_flag_payload(item) for item in spec.get("flags", [])],
            "examples": spec.get("examples", []),
            "data": bool(spec.get("data", True)),
            "destructive": bool(spec.get("destructive", False)),
        })
    print_json({
        "name": TOOL,
        "version": VERSION,
        "global_flags": [_flag_payload(item) for item in GLOBAL_FLAGS],
        "commands": commands,
    })
    return 0

SPEC["run"] = run

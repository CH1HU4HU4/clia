"""Print the version. Semver only, no banner."""

from __future__ import annotations

from ...constants import VERSION
from ...output import print_text

SPEC = {
    "path": ("version",),
    "summary": "Print the version",
    "description": "Print the semantic version and nothing else.",
    "arguments": [],
    "flags": [],
    "examples": ["acme version", "acme --version"],
    "data": False,
}


def run(ctx, opts, positionals):
    print_text(VERSION)
    return 0

SPEC["run"] = run

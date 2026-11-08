"""List projects with one page adapter and a stable envelope."""

from __future__ import annotations

from ...args import flag
from ...output import emit_dry_run, emit_list
from . import common

SPEC = {
    "path": ("project", "list"),
    "summary": "List projects",
    "description": "List projects in the current org. Returns summary fields; use --full for full objects.",
    "arguments": [],
    "flags": [
        flag("--limit", "value", "Results per page", "<n>", "50"),
        flag("--cursor", "value", "Continue after this cursor", "<cursor>"),
        flag("--all", desc="Fetch every page (cap: 10,000)"),
        flag("--sort", "value", "Sort field; prefix - for descending", "<field>"),
        flag("--filter", "value", "Exact match filter", "<key=value>", repeat=True),
        flag("--search", "value", "Server-side text search", "<text>"),
        flag("--status", "value", "Filter by status: active, paused, archived", "<status>"),
        flag("--owner", "value", "Filter by owner email", "<email>"),
        flag("--since", "value", "Created at or after (RFC 3339 or 24h)", "<time>"),
        flag("--until", "value", "Created at or before (RFC 3339 or 24h)", "<time>"),
        flag("--fields", "value", "Project top-level keys", "<id,name,status>"),
        flag("--full", desc="Return full objects instead of summaries"),
    ],
    "examples": [
        "acme project list --limit 5",
        "acme project list --status active --sort -created_at --json",
        "acme project list --all --fields id,name",
    ],
    "related": ["acme project get <id>", "acme project create --name web"],
    "data": True,
}


def run(ctx, opts, positionals):
    api = __import__("acme.api", fromlist=["Api"]).Api(ctx)
    query = common.list_query(opts)
    if opts.get("dry_run"):
        emit_dry_run(api.preview("GET", "/v1/projects", query), ctx, opts)
        return 0
    fields = common.requested_fields(opts)
    items, has_more, next_cursor, truncated = common.fetch(api, opts)
    shaped = [common.shape(item, full=bool(opts.get("full")), fields=fields) for item in items]
    emit_list(shaped, ctx, opts, common.LIST_COLUMNS, "projects",
              has_more=has_more, next_cursor=next_cursor, truncated=truncated)
    return 0

SPEC["run"] = run

"""Partial update with --set and --unset. No full object required."""

from __future__ import annotations

from ...args import flag
from ...errors import UsageError
from ...output import emit_dry_run, emit_object
from . import common

SPEC = {
    "path": ("project", "update"),
    "summary": "Update a project",
    "description": "Update only the fields you pass. Use --set key=value and --unset key.",
    "arguments": [{"name": "project", "description": "Project ID or name", "required": True}],
    "flags": [
        flag("--set", "value", "Set a field (repeatable, dotted keys allowed)", "<key=value>", repeat=True),
        flag("--unset", "value", "Clear a field", "<key>", repeat=True),
        flag("--file", "value", "JSON patch file, or - for stdin", "<path>"),
        flag("--data", "value", "Inline JSON patch", "<json>"),
    ],
    "examples": [
        "acme project update prj_001 --set status=paused",
        "acme project update web --set description=\"New copy\" --unset settings.region --json",
    ],
    "related": ["acme project get <id>", "acme project delete <id> --yes"],
    "data": True,
}


def run(ctx, opts, positionals):
    from ...api import Api
    api = Api(ctx)
    patch = common.patch_from_flags(opts)
    if not patch:
        raise UsageError("nothing to update", "Pass --set key=value or --unset key")
    project = common.resolve_project(api, positionals[0])
    if opts.get("dry_run"):
        emit_dry_run(api.preview("PATCH", common.path_for(project["id"]), None, patch), ctx, opts)
        return 0
    updated = api.patch(common.path_for(project["id"]), patch)
    emit_object(common.shape(updated, full=True), ctx, opts, common.GET_FIELDS)
    return 0

SPEC["run"] = run

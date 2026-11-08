"""Read one project by ID or unique name."""

from __future__ import annotations

from ...args import flag
from ...output import emit_dry_run, emit_object
from . import common

SPEC = {
    "path": ("project", "get"),
    "summary": "Get one project",
    "description": "Get one project by ID or unique name. Name ambiguity exits 11 with candidates.",
    "arguments": [{"name": "project", "description": "Project ID or name", "required": True}],
    "flags": [
        flag("--fields", "value", "Project top-level keys", "<id,name,status>"),
    ],
    "examples": [
        "acme project get prj_001",
        "acme project get web --json",
    ],
    "related": ["acme project list", "acme project update <id> --set status=paused"],
    "data": True,
}


def run(ctx, opts, positionals):
    from ...api import Api
    api = Api(ctx)
    value = positionals[0]
    if opts.get("dry_run"):
        emit_dry_run(api.preview("GET", common.path_for(value)), ctx, opts)
        return 0
    fields = common.requested_fields(opts)
    project = common.resolve_project(api, value)
    emit_object(common.shape(project, full=True, fields=fields), ctx, opts, common.GET_FIELDS)
    return 0

SPEC["run"] = run

"""Create a project with an idempotency key and a dry-run preview."""

from __future__ import annotations

import uuid

from ...args import flag
from ...errors import UsageError
from ...output import emit_dry_run, emit_object
from . import common

SPEC = {
    "path": ("project", "create"),
    "summary": "Create a project",
    "description": "Create a project. Sends an Idempotency-Key so retries never duplicate it.",
    "arguments": [],
    "flags": [
        flag("--name", "value", "Project name (required)", "<name>"),
        flag("--description", "value", "Project description", "<text>"),
        flag("--file", "value", "JSON body file, or - for stdin", "<path>"),
        flag("--data", "value", "Inline JSON body", "<json>"),
        flag("--idempotency-key", "value", "Reuse an external idempotency key", "<key>"),
    ],
    "examples": [
        "acme project create --name web",
        "acme project create --name web --description \"Customer-facing app\" --json",
        "acme project create --file project.json --dry-run",
    ],
    "related": ["acme project list", "acme project delete <id> --yes"],
    "data": True,
}


def run(ctx, opts, positionals):
    from ...api import Api
    api = Api(ctx)
    body = common.body_flags(opts)
    if opts.get("name"):
        body["name"] = opts["name"]
    if opts.get("description"):
        body["description"] = opts["description"]
    if not body.get("name"):
        raise UsageError('missing required flag "--name"', 'Pass --name "web" or --file project.json')
    key = opts.get("idempotency_key") or str(uuid.uuid4())
    if opts.get("dry_run"):
        emit_dry_run(api.preview("POST", "/v1/projects", None, body, key), ctx, opts)
        return 0
    project = api.post("/v1/projects", body, idempotency_key=key)
    emit_object(common.shape(project, full=True), ctx, opts, common.GET_FIELDS)
    return 0

SPEC["run"] = run

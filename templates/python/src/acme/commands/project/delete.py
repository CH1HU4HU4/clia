"""Delete a project: confirm on a TTY, require --yes everywhere else."""

from __future__ import annotations

import sys

from ...args import flag
from ...errors import CliError
from ...output import emit_action, emit_dry_run
from . import common

SPEC = {
    "path": ("project", "delete"),
    "summary": "Delete a project",
    "description": "Delete a project and everything it owns. Destructive: needs --yes off a TTY.",
    "arguments": [{"name": "project", "description": "Project ID or name", "required": True}],
    "flags": [],
    "examples": [
        "acme project delete prj_001 --yes",
        "acme project delete web --dry-run --json",
    ],
    "related": ["acme project list", "acme project get <id>"],
    "data": True,
    "destructive": True,
}


def _confirm(ctx, project, opts):
    if ctx.output != "table" or opts.get("no_input") or not sys.stdin.isatty():
        raise CliError(
            "confirmation_required",
            'Refusing to delete project "%s" (%s) without --yes' % (project["name"], project["id"]),
            "Re-run with --yes to delete project %s" % project["id"],
        )
    sys.stderr.write('About to delete project "%s" (%s)\n' % (project["name"], project["id"]))
    sys.stderr.write(
        "target: profile %s, %s, org %s, project %s, API %s\n"
        % (ctx.profile, ctx.base_url, ctx.org, ctx.project, ctx.api_version)
    )
    sys.stderr.write("Continue? [y/N] ")
    sys.stderr.flush()
    answer = sys.stdin.readline().strip().lower()
    if answer not in ("y", "yes"):
        raise CliError("confirmation_required", "Deletion cancelled", "No changes were made")


def run(ctx, opts, positionals):
    from ...api import Api
    api = Api(ctx)
    project = common.resolve_project(api, positionals[0])
    if opts.get("dry_run"):
        emit_dry_run(api.preview("DELETE", common.path_for(project["id"])), ctx, opts)
        return 0
    if not opts.get("yes"):
        _confirm(ctx, project, opts)
    result = api.delete(common.path_for(project["id"]))
    emit_action(result, ctx, "Deleted project %s." % project["id"])
    return 0

SPEC["run"] = run

"""`acme help [command]` behaves like `<command> --help`."""

from __future__ import annotations

from ...errors import UsageError
from ...help import command_help, have_specs, root_help
from ...output import print_text

SPEC = {
    "path": ("help",),
    "summary": "Show help",
    "description": "Show root help or help for one command.",
    "arguments": [
        {"name": "command", "description": "Command path", "required": False},
        {"name": "subcommand", "description": "Subcommand", "required": False},
    ],
    "flags": [],
    "examples": ["acme help", "acme help project list"],
    "data": False,
}


def run(ctx, opts, positionals):
    from .. import all_specs
    specs = all_specs()
    have_specs(specs)
    if not positionals:
        print_text(root_help(specs))
        return 0
    path = tuple(positionals)
    if path not in specs:
        raise UsageError('unknown command "%s"' % " ".join(path), "Run acme --help")
    print_text(command_help(specs[path]))
    return 0

SPEC["run"] = run

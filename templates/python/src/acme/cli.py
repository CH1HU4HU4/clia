"""Entry point: parse, resolve context, run one command, map one error."""

from __future__ import annotations

import os
import sys
import traceback

from . import config
from .args import parse
from .commands import all_specs
from .constants import ENV, TOOL, VERSION
from .context import resolve_context
from .errors import CliError, UsageError, emit_error
from .help import command_help, have_specs, root_help
from .output import print_text
from .redact import redact_text

NO_CONTEXT = {("help",), ("version",), ("completion",), ("schema",)}


def _json_requested(argv, opts, ctx):
    if opts.get("json"):
        return True
    if ctx is not None and ctx.output == "json":
        return True
    if os.environ.get(ENV + "_OUTPUT") == "json":
        return True
    return "--json" in argv


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    registry = all_specs()
    have_specs(registry)
    ctx = None
    opts = {}
    try:
        spec, opts, positionals = parse(argv, registry)
        if spec is None:
            if opts.get("version"):
                print_text(VERSION)
                return 0
            print_text(root_help(registry))
            return 0
        if opts.get("help"):
            print_text(command_help(spec))
            return 0
        if opts.get("version"):
            raise UsageError("--version is a root flag", "Run: %s --version" % TOOL)
        if spec["path"] in NO_CONTEXT:
            return spec["run"](None, opts, positionals) or 0
        ctx = resolve_context(opts, allow_missing_profile=spec["path"] == ("config", "set"))
        return spec["run"](ctx, opts, positionals) or 0
    except KeyboardInterrupt:
        err = CliError("cancelled", "Interrupted", None)
        emit_error(err, ctx, _json_requested(argv, opts, ctx))
        return 130
    except CliError as err:
        secrets = [getattr(ctx, "token", None), getattr(ctx, "refresh_token", None)]
        err.message = redact_text(err.message, secrets)
        if err.hint:
            err.hint = redact_text(err.hint, secrets)
        emit_error(err, ctx, _json_requested(argv, opts, ctx))
        return err.exit
    except Exception as err:  # pragma: no cover - last resort
        if opts.get("debug"):
            traceback.print_exc()
        secrets = [getattr(ctx, "token", None), getattr(ctx, "refresh_token", None)]
        wrapped = CliError(
            "unexpected",
            "Internal error: " + redact_text(str(err), secrets),
            "Run with --debug for a traceback",
        )
        emit_error(wrapped, ctx, _json_requested(argv, opts, ctx))
        return 1


if __name__ == "__main__":
    sys.exit(main())

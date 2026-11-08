"""Checks for documentation, names, help, and the offline path."""

from __future__ import annotations

import os
import re
import shlex

from .discover import META
from .util import SEMVER, has_ansi

ALLOWED_VERBS = {
    "list", "get", "create", "update", "replace", "delete",
    "cancel", "retry", "rotate", "invite", "archive", "unarchive",
    "wait", "logs", "deploy", "pause", "resume", "revoke", "use",
    "login", "logout", "status", "set", "unset", "run", "download",
    "upload", "publish", "test", "apply", "diff", "rollback",
}
RESERVED_TOP = {"auth", "config", "whoami", "version", "completion", "schema", "help"}
NOT_EXAMPLE_SAFE = {"auth", "config"}


def check_m01(ctx):
    path = ctx.cli_doc
    if not os.path.exists(path):
        return ctx.check("M01", False, "CLI.md not found at " + path)
    text = open(path, encoding="utf-8").read().lower()
    missing = []
    for needle in ("surface map", "command tree", "gaps", "exit codes", "auth"):
        if needle not in text:
            missing.append(needle)
    table = "| capability" in text and "| command" in text
    ok = not missing and table
    detail = "surface map, command tree, gaps, exit codes, auth" if ok \
        else "missing: " + ", ".join(missing + (["capability table"] if not table else []))
    return ctx.check("M01", ok, detail)


def check_m03(ctx):
    bad = []
    for path in ctx.commands:
        for segment in path:
            if not re.match(r"^[a-z][a-z0-9-]*$", segment):
                bad.append("segment %r in %s" % (segment, " ".join(path)))
        if len(path) > 2:
            bad.append("too deep: " + " ".join(path))
            continue
        if path[0] in RESERVED_TOP or path[0] in META:
            continue
        if len(path) == 2 and path[1] not in ALLOWED_VERBS:
            bad.append("verb %r in %s" % (path[1], " ".join(path)))
        if path[0].endswith("s") and path[0] not in ("status", "billing", "settings"):
            bad.append("plural resource: " + path[0])
    ok = not bad
    return ctx.check("M03", ok, "; ".join(bad[:4]) or "grammar and verbs follow section 3")


def check_m07(ctx):
    bad = []
    for path, command in sorted(ctx.commands.items()):
        if command.get("group"):
            continue
        result = ctx.run(list(path) + ["--help"])
        help_text = result.out
        name = " ".join(path)
        if result.code != 0:
            bad.append(name + " help exit " + str(result.code))
            continue
        examples = command.get("examples") or []
        if len(examples) < 2:
            bad.append(name + " has %d examples" % len(examples))
        for example in examples:
            if re.search(r"<[a-z-]+>|abc123|your-id|\bfoo\b", example):
                bad.append(name + " placeholder in example")
                break
        if "Flags:" not in help_text:
            bad.append(name + " help lacks Flags")
        for flag in command.get("flags") or []:
            if flag.get("default") not in (None, "") and "default:" not in help_text:
                bad.append(name + " help hides default for " + flag.get("name", "?"))
                break
            if flag.get("env") and "env:" not in help_text:
                bad.append(name + " help hides env for " + flag.get("name", "?"))
                break
    return ctx.check("M07", not bad, "; ".join(bad[:4]) or "help has args, flags, defaults, examples")


def _example_args(ctx, example):
    try:
        parts = shlex.split(example)
    except ValueError:
        return None
    if not parts:
        return None
    parts = parts[1:]
    return parts


def check_m08(ctx):
    bad = []
    executed = 0
    for path, command in sorted(ctx.commands.items()):
        if command.get("group") or path[0] in META or path[0] in NOT_EXAMPLE_SAFE:
            continue
        clean = ctx.example_commands(command)
        if not clean:
            bad.append(" ".join(path) + " has no shell-free example")
            continue
        args = _example_args(ctx, clean[0])
        if args is None:
            bad.append(" ".join(path) + " example does not parse")
            continue
        result = ctx.run(args + ["--dry-run", "--json"])
        executed += 1
        if result.code != 0:
            bad.append("example for %s exited %d" % (" ".join(path), result.code))
        elif result.out.strip():
            try:
                import json
                json.loads(result.out)
            except ValueError:
                bad.append("example for %s did not emit JSON" % " ".join(path))
    ok = not bad and executed > 0
    return ctx.check("M08", ok, ("%d examples executed; " % executed) + "; ".join(bad[:4]))


def check_m09(ctx):
    result = ctx.run(["--version"])
    text = result.out.strip()
    lines = [line for line in result.out.splitlines() if line.strip()]
    ok = result.code == 0 and bool(SEMVER.match(text)) and len(lines) == 1 and not result.err.strip()
    return ctx.check("M09", ok, "stdout %r exit %d" % (text, result.code))


def check_m10(ctx):
    problems = []
    unknown = "projet"
    if (unknown,) in ctx.commands:
        unknown = "projetx"
    result = ctx.run([unknown])
    if result.code != 2:
        problems.append("unknown command exit %d" % result.code)
    if "unknown command" not in result.err.lower():
        problems.append("unknown command not named")
    if "did you mean" not in result.err.lower() and "project" not in result.err.lower():
        problems.append("unknown command has no suggestion")
    list_cmd = ctx.resource_command("list")
    if list_cmd:
        flag_result = ctx.run(list(list_cmd["path"]) + ["--limt", "5"])
        if flag_result.code != 2:
            problems.append("unknown flag exit %d" % flag_result.code)
        if "unknown flag" not in flag_result.err.lower():
            problems.append("unknown flag not named")
        if "did you mean" not in flag_result.err.lower():
            problems.append("unknown flag has no suggestion")
    else:
        problems.append("no list command to test unknown flags")
    return ctx.check("M10", not problems, "; ".join(problems) or "exit 2 with suggestions")


def check_m11(ctx):
    completion = ctx.command("completion")
    if not completion:
        return ctx.defer("M11", "completion command not shipped (P1)")
    problems = []
    for shell in ("bash", "zsh", "fish"):
        result = ctx.run(["completion", shell])
        if result.code != 0 or not result.out.strip():
            problems.append("%s exit %d" % (shell, result.code))
        if has_ansi(result.out):
            problems.append("%s emitted ANSI" % shell)
    return ctx.check("M11", not problems, "; ".join(problems) or "bash, zsh, fish generated")


def check_m12(ctx):
    result = ctx.run(["--help"])
    text = result.out
    host = ctx.base_url.replace("http://", "").replace("https://", "").rstrip("/")
    ok = result.code == 0 and "Profile:" in text and host in text and "API" in text
    return ctx.check("M12", ok, "root help shows the resolved target" if ok
                     else "root help lacks the profile, base URL, or API version")


def check_m35(ctx):
    problems = []
    for args in (["--help"], ["--version"], [ctx.cfg["resource"], "list", "--help"]):
        result = ctx.offline(args, timeout=8)
        if result.code != 0:
            problems.append("%s exit %d offline" % (" ".join(args), result.code))
    return ctx.check("M35", not problems, "; ".join(problems) or "help and version work offline")


def check_m47(ctx):
    path = os.path.join(ctx.repo, "README.md")
    if not os.path.exists(path):
        return ctx.review("M47", "README.md missing")
    text = open(path, encoding="utf-8").read()
    missing = [needle for needle in ("AGENTS.md", "--json", "--yes") if needle not in text]
    return ctx.review("M47", "snippet present" if not missing else "missing: " + ", ".join(missing))


def check_reviews(ctx):
    path = ctx.cli_doc
    text = open(path, encoding="utf-8").read().lower() if os.path.exists(path) else ""
    ctx.review("M02", "surface map covers user jobs" if "surface map" in text else "surface map missing")
    ctx.review("M04", "existing-CLI path recorded" if "existing cli" in text else "path not recorded")
    ctx.review("M05", "API inventory filled" if "capability inventory" in text else "inventory missing")
    ctx.review("M06", "first slice recorded" if "slice" in text else "slice not recorded")
    ctx.review("M29", "precedence recorded" if "precedence" in text else "precedence not recorded")
    ctx.review("M36", "context resolution centralized" if "context" in text else "context not recorded")


def all_checks(ctx):
    check_m01(ctx)
    check_reviews(ctx)
    check_m03(ctx)
    check_m07(ctx)
    check_m08(ctx)
    check_m09(ctx)
    check_m10(ctx)
    check_m11(ctx)
    check_m12(ctx)
    check_m35(ctx)
    check_m47(ctx)

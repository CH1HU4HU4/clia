"""Help is a feature: every command prints arguments, flags, defaults, examples."""

from __future__ import annotations

import os

from . import config
from .constants import DOCS_URL, ENV, TOOL, VERSION

ROOT_ORDER = ["auth", "config", "project", "whoami", "version", "completion", "schema", "help"]

EXIT_LINE = ("0 success, 2 usage, 3 auth, 4 forbidden, 5 not found, 6 conflict, "
             "7 rate limit/server, 8 network, 10 confirmation, 11 ambiguous")


def _flag_syntax(item):
    text = item["long"]
    if item["kind"] == "value":
        text += " " + (item.get("metavar") or "<value>")
    elif item["long"] == "--json":
        pass
    if item.get("short"):
        text = item["short"] + ", " + text
    return text


def _flag_line(item):
    text = _flag_syntax(item)
    description = item.get("desc") or ""
    extras = []
    if item["kind"] == "value" and item.get("default") not in (None, ""):
        extras.append("default: %s" % item["default"])
    if item.get("env"):
        extras.append("env: %s" % item["env"])
    if extras:
        description = ("%s (%s)" % (description, "; ".join(extras))).strip()
    return "  " + text.ljust(30) + description.rstrip()


def _target_line():
    try:
        configured = os.path.exists(config.config_path()) or os.environ.get(ENV + "_PROFILE") \
            or os.environ.get(ENV + "_BASE_URL")
        if not configured:
            return None
        data = config.load()
        profile = os.environ.get(ENV + "_PROFILE") or str(data.get("profile") or "default")
        values = config.profile_values(data, profile) or {}
        base = os.environ.get(ENV + "_BASE_URL") or values.get("base_url") or ""
        org = os.environ.get(ENV + "_ORG") or values.get("org") or "-"
        project = os.environ.get(ENV + "_PROJECT") or values.get("project") or "-"
        version = os.environ.get(ENV + "_API_VERSION") or values.get("api_version") or "-"
        return "Profile: %s (%s, org %s, project %s, API %s)" % (
            profile, base, org, project, version)
    except Exception:
        return None


def root_help(specs):
    lines = [
        "%s %s \u2014 Command line for Acme" % (TOOL, VERSION),
        "",
        "Manage Acme projects from a terminal or an agent.",
        "",
        "Usage:",
        "  %s <command> [flags]" % TOOL,
        "",
        "Commands:",
    ]
    top = [path for path in specs if len(path) == 1 and not specs[path].get("hidden")]
    ordered = [name for name in ROOT_ORDER if (name,) in top]
    ordered += sorted(name[0] for name in top if name[0] not in ROOT_ORDER)
    for name in ordered:
        lines.append("  " + name.ljust(12) + specs[(name,)]["summary"])
    lines += ["", "Global flags:"]
    for item in _global_flags():
        lines.append(_flag_line(item))
    lines += [
        "",
        "Examples:",
        "  %s auth login --token $%s_TOKEN" % (TOOL, ENV),
        "  %s project list --limit 5 --json" % TOOL,
        "  %s project get prj_001" % TOOL,
        "",
        "Exit codes:",
        "  " + EXIT_LINE,
        "",
        "Docs: " + DOCS_URL,
    ]
    target = _target_line()
    if target:
        lines.insert(4, target)
        lines.insert(5, "")
    return "\n".join(lines)


def _global_flags():
    from .args import GLOBAL_FLAGS
    return [item for item in GLOBAL_FLAGS if item["long"] != "--version"]


def command_help(spec):
    lines = [spec.get("description") or spec["summary"], ""]
    if spec.get("group"):
        lines += ["Usage:", "  %s %s <command> [flags]" % (TOOL, " ".join(spec["path"])), "", "Commands:"]
        return "\n".join(lines + _child_lines(spec))
    tail = []
    for argument in spec.get("arguments", []):
        tail.append("<%s>" % argument["name"] if argument.get("required") else "[%s]" % argument["name"])
    tail.append("[flags]")
    lines += ["Usage:", "  %s %s %s" % (TOOL, " ".join(spec["path"]), " ".join(tail)), ""]
    if spec.get("arguments"):
        lines.append("Arguments:")
        for argument in spec["arguments"]:
            lines.append("  " + argument["name"].ljust(14) + argument.get("description", ""))
        lines.append("")
    lines.append("Flags:")
    for item in list(spec.get("flags", [])) + _global_flags():
        lines.append(_flag_line(item))
    lines += ["", "Examples:"]
    for example in spec.get("examples", []):
        lines.append("  " + example)
    if spec.get("related"):
        lines += ["", "Related:"]
        for item in spec["related"]:
            lines.append("  " + item)
    return "\n".join(lines)


def _child_lines(spec):
    lines = []
    specs = _all_specs()
    children = [path for path in specs if len(path) == len(spec["path"]) + 1
                and path[:-1] == spec["path"]]
    for path in sorted(children):
        lines.append("  " + path[-1].ljust(12) + specs[path]["summary"])
    return lines


_CACHE = {}


def _all_specs():
    return _CACHE["specs"]


def have_specs(specs):
    _CACHE["specs"] = specs

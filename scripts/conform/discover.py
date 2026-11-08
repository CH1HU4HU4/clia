"""Discover the command tree from `schema --json`, or from help text."""

from __future__ import annotations

import re

META = {"help", "version", "completion", "schema"}


def _section(text, name):
    lines = text.splitlines()
    collecting = False
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped.lower() == name.lower() + ":":
            collecting = True
            continue
        if collecting:
            if stripped and not line.startswith(" ") and stripped.endswith(":"):
                break
            if stripped and not line.startswith(" "):
                break
            out.append(line)
    return out


def _flag_from_line(line):
    stripped = line.strip()
    if not stripped.startswith("-"):
        return None
    parts = stripped.split(None, 1)
    syntax = parts[0]
    description = parts[1].strip() if len(parts) > 1 else ""
    name = syntax
    if "," in syntax:
        options = [piece.strip() for piece in syntax.split(",")]
        longs = [piece for piece in options if piece.startswith("--")]
        name = longs[0] if longs else options[-1]
    match = re.search(r"<([^>]+)>", name)
    if match:
        type_name = "value"
        metavar = "<%s>" % match.group(1)
        name = name.split("<")[0].strip()
    else:
        type_name = "bool"
        metavar = None
    default = None
    env = None
    for note in re.findall(r"\(([^)]*)\)", description):
        for part in note.split(";"):
            piece = part.strip()
            if piece.startswith("default:"):
                default = piece.split(":", 1)[1].strip()
            elif piece.startswith("env:"):
                env = piece.split(":", 1)[1].strip()
    return {
        "name": name,
        "type": type_name,
        "metavar": metavar,
        "default": default,
        "env": env,
        "description": description,
    }


def parse_help(text, path, summary="", destructive=False, data=True):
    arguments = []
    for line in _section(text, "Arguments"):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split(None, 1)
        arguments.append({
            "name": parts[0],
            "description": parts[1].strip() if len(parts) > 1 else "",
            "required": True,
        })
    flags = []
    for line in _section(text, "Flags"):
        parsed = _flag_from_line(line)
        if parsed:
            flags.append(parsed)
    examples = [line.strip() for line in _section(text, "Examples") if line.strip()]
    return {
        "path": list(path),
        "summary": summary,
        "arguments": arguments,
        "flags": flags,
        "examples": examples,
        "destructive": destructive,
        "data": data,
        "group": False,
        "help": text,
    }


def _command_names(lines):
    names = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        parts = re.split(r"\s{2,}", stripped, maxsplit=1)
        if parts and re.match(r"^[a-z][a-z0-9-]*$", parts[0]):
            names.append((parts[0], parts[1].strip() if len(parts) > 1 else ""))
    return names


def from_help(runner):
    commands = {}
    root = runner.run(["--help"])
    if root.code != 0:
        return commands
    top = _command_names(_section(root.out, "Commands"))
    for name, summary in top:
        result = runner.run([name, "--help"])
        if result.code != 0:
            continue
        if _section(result.out, "Commands"):
            for child, child_summary in _command_names(_section(result.out, "Commands")):
                leaf = runner.run([name, child, "--help"])
                if leaf.code != 0:
                    continue
                destructive = child in ("delete", "revoke", "cancel", "rotate")
                commands[tuple([name, child])] = parse_help(
                    leaf.out, [name, child], child_summary, destructive,
                    data=name not in META,
                )
        else:
            commands[tuple([name])] = parse_help(
                result.out, [name], summary, data=name not in META
            )
    return commands


def from_schema(runner):
    result = runner.run(["schema"])
    payload = result.json_out()
    if result.code != 0 or not isinstance(payload, dict):
        return {}
    commands = {}
    for item in payload.get("commands") or []:
        path = item.get("path") or []
        if not path:
            continue
        command = {
            "path": list(path),
            "summary": item.get("summary", ""),
            "arguments": item.get("arguments") or [],
            "flags": item.get("flags") or [],
            "examples": item.get("examples") or [],
            "destructive": bool(item.get("destructive")),
            "data": bool(item.get("data", True)),
            "group": False,
            "help": "",
        }
        commands[tuple(path)] = command
    return commands


def discover(runner, cfg):
    commands = {}
    if (cfg.get("capabilities") or {}).get("schema"):
        commands = from_schema(runner)
    if not commands:
        commands = from_help(runner)
    for command in commands.values():
        command["name"] = " ".join(command["path"])
    return commands

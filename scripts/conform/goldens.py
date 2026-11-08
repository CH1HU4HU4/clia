"""Golden snapshots for help and the five canonical tasks."""

from __future__ import annotations

import json
import os
import re

UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
REQUEST_ID = re.compile(r"req_[0-9a-zA-Z]+")
EPOCH = re.compile(r'"created_at":"[^"]+"')


def normalize(ctx, text):
    if text is None:
        return None
    out = text
    out = out.replace(ctx.base_url, "{base_url}")
    if ctx.token:
        out = out.replace(ctx.token, "{token}")
    out = out.replace(ctx.xdg, "{xdg}")
    out = out.replace(ctx.home, "{home}")
    out = UUID.sub("{uuid}", out)
    out = REQUEST_ID.sub("req_{id}", out)
    out = re.sub(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", "{timestamp}", out)
    out = re.sub(r'"(idempotency-key|expires_at|created_at|updated_at)":"[^"]*"',
                 r'"\1":"{value}"', out)
    return out


def _canonical_commands(ctx):
    resource = ctx.cfg["resource"]
    sample = ctx.cfg["sample_id"]
    return {
        "root_help": ["--help"],
        "task1_auth_status": ["auth", "status", "--json"],
        "task2_list": [resource, "list", "--limit", "5", "--json"],
        "task3_get": [resource, "get", sample, "--json"],
        "task4_create_dry": [resource, "create", "--name", "clia-golden", "--dry-run", "--json"],
        "task5_delete_refused": [resource, "delete", sample, "--json"],
    }


def snapshot(ctx):
    help_payload = {}
    for path, command in sorted(ctx.commands.items()):
        result = ctx.run(list(path) + ["--help"])
        help_payload[" ".join(path)] = {
            "code": result.code,
            "stdout": normalize(ctx, result.out),
        }
    canonical = {}
    for name, args in _canonical_commands(ctx).items():
        result = ctx.run(args)
        canonical[name] = {
            "code": result.code,
            "stdout": normalize(ctx, result.out),
            "stderr": normalize(ctx, result.err),
        }
    return {"help": help_payload, "canonical": canonical}


def verify(ctx, golden_dir, update=False):
    help_path = os.path.join(golden_dir, "help.json")
    canonical_path = os.path.join(golden_dir, "canonical.json")
    current = snapshot(ctx)
    if update:
        os.makedirs(golden_dir, exist_ok=True)
        with open(help_path, "w", encoding="utf-8") as stream:
            json.dump(current["help"], stream, indent=2, sort_keys=True)
            stream.write("\n")
        with open(canonical_path, "w", encoding="utf-8") as stream:
            json.dump(current["canonical"], stream, indent=2, sort_keys=True)
            stream.write("\n")
        return True, "wrote %d help snapshots and %d canonical snapshots" % (
            len(current["help"]), len(current["canonical"]))
    missing = [path for path in (help_path, canonical_path) if not os.path.exists(path)]
    if missing:
        return False, "missing goldens: " + ", ".join(os.path.basename(path) for path in missing) \
            + " (run with --update-goldens)"
    with open(help_path, encoding="utf-8") as stream:
        expected_help = json.load(stream)
    with open(canonical_path, encoding="utf-8") as stream:
        expected_canonical = json.load(stream)
    problems = []
    for name, expected in expected_help.items():
        actual = current["help"].get(name)
        if actual is None:
            problems.append("help missing for " + name)
        elif actual["code"] != expected.get("code") or actual["stdout"] != expected.get("stdout"):
            problems.append("help drifted: " + name)
    for name, expected in expected_canonical.items():
        actual = current["canonical"].get(name)
        if actual is None:
            problems.append("canonical missing for " + name)
            continue
        for field in ("code", "stdout", "stderr"):
            if actual.get(field) != expected.get(field):
                problems.append("%s drifted: %s" % (name, field))
    if problems:
        return False, "; ".join(problems[:5])
    return True, "%d help and %d canonical snapshots match" % (
        len(expected_help), len(expected_canonical))

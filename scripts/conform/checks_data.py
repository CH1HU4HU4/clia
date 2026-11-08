"""Checks for JSON, lists, errors, dry runs, and the canonical tasks."""

from __future__ import annotations

import json
import re
import time

from .util import RFC3339, has_ansi, key_case_ok, walk_keys, walk_scalars


def _json(result):
    payload = result.json_out()
    return payload if isinstance(payload, (dict, list)) else None


def _resource(ctx, verb):
    return ctx.resource_command(verb)


def check_m13(ctx):
    problems = []
    for command in ctx.data_commands():
        help_text = ctx.run(list(command["path"]) + ["--help"]).out
        if not ctx.has_flag(command, "--json") and "--json" not in help_text:
            problems.append(" ".join(command["path"]) + " lacks --json")
    probes = []
    list_cmd = _resource(ctx, "list")
    if list_cmd:
        probes.append(list_cmd["path"] + ["--limit", "1", "--json"])
    get_cmd = _resource(ctx, "get")
    if get_cmd:
        probes.append(get_cmd["path"] + [ctx.cfg["sample_id"], "--json"])
    create_cmd = _resource(ctx, "create")
    if create_cmd:
        probes.append(create_cmd["path"] + ["--name", "clia-probe", "--dry-run", "--json"])
    for args in probes:
        result = ctx.run(args)
        if result.code != 0:
            problems.append(" ".join(args) + " exit %d" % result.code)
        elif _json(result) is None:
            problems.append(" ".join(args) + " did not emit one JSON document")
    return ctx.check("M13", not problems, "; ".join(problems[:4]) or "every data command has --json")


def check_m14(ctx):
    convention = ctx.cfg.get("key_case", "snake")
    payloads = []
    resource = ctx.cfg["resource"]
    probes = [
        [resource, "list", "--limit", "2", "--json"],
        [resource, "get", ctx.cfg["sample_id"], "--json"],
        ["auth", "status", "--json"],
    ]
    for args in probes:
        result = ctx.run(args)
        if result.code == 0 and _json(result) is not None:
            payloads.append(_json(result))
    missing = ctx.run([ctx.cfg["resource"], "get", ctx.cfg["missing_id"], "--json"])
    if missing.json_err():
        payloads.append(missing.json_err())
    bad_keys = set()
    bad_times = set()
    bad_ids = set()
    for payload in payloads:
        for key in walk_keys(payload):
            if not key_case_ok(key, convention):
                bad_keys.add(key)
        for scalar in walk_scalars(payload):
            if isinstance(scalar, str) and re.match(r"^\d{4}-\d{2}-\d{2}T", scalar):
                if not RFC3339.match(scalar):
                    bad_times.add(scalar)
        for key, value in _flatten(payload):
            if (key == "id" or key.endswith("_id")) and value is not None and not isinstance(value, str):
                bad_ids.add(key)
    problems = []
    if bad_keys:
        problems.append("key convention: " + ", ".join(sorted(bad_keys)[:4]))
    if bad_times:
        problems.append("timestamps not RFC 3339 Z: " + ", ".join(sorted(bad_times)[:2]))
    if bad_ids:
        problems.append("non-string IDs: " + ", ".join(sorted(bad_ids)[:4]))
    return ctx.check("M14", not problems, "; ".join(problems) or "snake_case, UTC timestamps, string IDs")


def _flatten(payload, prefix=""):
    if isinstance(payload, dict):
        for key, value in payload.items():
            if isinstance(value, (dict, list)):
                for item in _flatten(value, key):
                    yield item
            else:
                yield key, value
    elif isinstance(payload, list):
        for item in payload:
            for nested in _flatten(item, prefix):
                yield nested


def check_m15(ctx):
    command = _resource(ctx, "list")
    if not command:
        return ctx.na("M15", "no list command in this product")
    problems = []
    first = ctx.run(command["path"] + ["--limit", "2", "--json"])
    payload = _json(first)
    if first.code != 0 or not isinstance(payload, dict):
        return ctx.check("M15", False, "list --limit 2 failed: " + str(first.code))
    for key in ("data", "has_more", "next_cursor", "truncated"):
        if key not in payload:
            problems.append("missing " + key)
    data = payload.get("data") or []
    if len(data) > 2:
        problems.append("limit ignored (%d items)" % len(data))
    cursor = payload.get("next_cursor")
    if cursor:
        second = ctx.run(command["path"] + ["--limit", "2", "--cursor", str(cursor), "--json"])
        page = _json(second)
        if second.code != 0 or not page:
            problems.append("--cursor failed")
        elif data and page.get("data") and page["data"][0].get("id") == data[0].get("id"):
            problems.append("cursor returned the same first item")
    else:
        problems.append("next_cursor missing with more pages")
    all_result = ctx.run(command["path"] + ["--all", "--json"])
    all_payload = _json(all_result)
    if all_result.code != 0 or not all_payload:
        problems.append("--all failed")
    elif len(all_payload.get("data") or []) < len(data):
        problems.append("--all returned fewer items")
    empty = ctx.run(command["path"] + ["--search", "zzz-no-such-project", "--json"])
    empty_payload = _json(empty)
    if empty.code != 0 or not empty_payload or empty_payload.get("data") != []:
        problems.append("empty list did not exit 0 with data: []")
    return ctx.check("M15", not problems, "; ".join(problems[:4]) or "limit, cursor, all, envelope, empty")


def check_m16(ctx):
    list_cmd = _resource(ctx, "list")
    get_cmd = _resource(ctx, "get")
    if not list_cmd or not get_cmd:
        return ctx.na("M16", "list or get not present")
    problems = []
    if not ctx.has_flag(list_cmd, "--full"):
        problems.append("list has no --full")
    listed = _json(ctx.run(list_cmd["path"] + ["--limit", "1", "--json"])) or {}
    gotten = _json(ctx.run(get_cmd["path"] + [ctx.cfg["sample_id"], "--json"])) or {}
    item = (listed.get("data") or [{}])[0]
    extra = set(gotten) - set(item)
    if not extra:
        problems.append("list items are not summaries (no keys omitted)")
    if extra and set(item) & extra:
        problems.append("summary leaks full fields: " + ", ".join(sorted(set(item) & extra)))
    full = _json(ctx.run(list_cmd["path"] + ["--full", "--limit", "1", "--json"])) or {}
    full_item = (full.get("data") or [{}])[0]
    if not (extra & set(full_item)):
        problems.append("--full does not return full objects")
    return ctx.check("M16", not problems, "; ".join(problems) or "summaries, full get, --full")


def check_m17(ctx):
    command = _resource(ctx, "list")
    if not command:
        return ctx.defer("M17", "no list command")
    if not ctx.has_flag(command, "--quiet") and "--quiet" not in ctx.run(command["path"] + ["--help"]).out:
        return ctx.defer("M17", "--quiet not shipped (P1)")
    result = ctx.run(command["path"] + ["--quiet", "--limit", "3"])
    lines = [line for line in result.out.splitlines() if line.strip()]
    ids = []
    payload = _json(ctx.run(command["path"] + ["--limit", "3", "--json"])) or {}
    for item in payload.get("data") or []:
        ids.append(str(item.get("id")))
    ok = result.code == 0 and lines == ids and not has_ansi(result.out)
    return ctx.check("M17", ok, "one identifier per line" if ok else "quiet output was %r" % lines[:3])


def check_m18(ctx):
    command = _resource(ctx, "list")
    if not command:
        return ctx.na("M18", "no list command")
    problems = []
    for env in ({}, {"NO_COLOR": "1"}):
        result = ctx.run(command["path"] + ["--limit", "1"], env_extra=env)
        if has_ansi(result.out) or has_ansi(result.err):
            problems.append("ANSI with NO_COLOR=%s" % env.get("NO_COLOR"))
    result = ctx.run(command["path"] + ["--limit", "1", "--json"])
    if has_ansi(result.out) or has_ansi(result.err):
        problems.append("ANSI with --json")
    return ctx.check("M18", not problems, "; ".join(problems) or "no ANSI when piped or asked for JSON")


def _error_case(ctx, args, expected, env=None, human=False, need_retry_after=False):
    result = ctx.run(args, env_extra=env)
    problems = []
    if result.code != expected:
        problems.append("%s exit %d, want %d" % (" ".join(args), result.code, expected))
    if human:
        if not result.err.strip().startswith("error:"):
            problems.append("human error lacks 'error:'")
        if "hint:" not in result.err:
            problems.append("human error lacks 'hint:'")
        return problems
    payload = result.json_err()
    error = (payload or {}).get("error") or {}
    if not error:
        problems.append("no JSON error envelope on stderr")
        return problems
    if not error.get("message"):
        problems.append("error lacks message")
    if not error.get("hint"):
        problems.append("error lacks hint")
    if "retryable" not in error:
        problems.append("error lacks retryable")
    if "target" not in error:
        problems.append("error lacks resolved target")
    code_by_exit = {3: "auth_required", 4: "forbidden", 5: "not_found", 6: "validation",
                    7: "rate_limited", 8: "timeout"}
    wanted = code_by_exit.get(expected)
    if expected == 6 and error.get("code") not in ("validation", "conflict"):
        problems.append("conflict/validation code missing")
    elif expected == 7 and error.get("code") not in ("rate_limited", "server_error"):
        problems.append("rate_limited/server_error code missing")
    elif expected == 8 and error.get("code") not in ("timeout", "network_error"):
        problems.append("timeout/network_error code missing")
    elif wanted and expected not in (6, 7, 8) and error.get("code") != wanted:
        problems.append("code %r, want %r" % (error.get("code"), wanted))
    if need_retry_after and "retry_after" not in error:
        problems.append("429 lacks retry_after")
    return problems


def check_m19(ctx):
    list_cmd = _resource(ctx, "list")
    get_cmd = _resource(ctx, "get")
    create_cmd = _resource(ctx, "create")
    update_cmd = _resource(ctx, "update")
    problems = []
    if list_cmd:
        problems += _error_case(ctx, list_cmd["path"] + ["--json"], 3,
                                env={ctx.token_env: ctx.cfg["bad_token"]})
    if get_cmd:
        problems += _error_case(ctx, get_cmd["path"] + [ctx.cfg["forbidden_id"], "--json"], 4)
        problems += _error_case(ctx, get_cmd["path"] + [ctx.cfg["missing_id"], "--json"], 5)
        problems += _error_case(ctx, get_cmd["path"] + [ctx.cfg["missing_id"]], 5, human=True)
        problems += _error_case(ctx, get_cmd["path"] + [ctx.cfg["slow_id"], "--timeout", "1", "--json"], 8)
        problems += _error_case(ctx, get_cmd["path"] + [ctx.cfg["rate_limit_id"], "--json"], 7,
                                need_retry_after=True)
        problems += _error_case(ctx, get_cmd["path"] + [ctx.cfg["server_error_id"], "--json"], 7)
    if create_cmd:
        problems += _error_case(ctx, create_cmd["path"] + ["--name", ctx.cfg["conflict_name"], "--json"], 6)
    if update_cmd:
        problems += _error_case(ctx, update_cmd["path"] + [ctx.cfg["sample_id"], "--set", "status=bogus", "--json"], 6)
    problems += _error_case(ctx, [ctx.cfg["resource"], "list", "--base-url", "http://127.0.0.1:1", "--json"], 8)
    return ctx.check("M19", not problems, "; ".join(problems[:5]) or "401/403/404/409/422/429/500/timeout/network mapped")


def check_m20(ctx):
    command = _resource(ctx, "create")
    delete = _resource(ctx, "delete")
    problems = []
    if command:
        result = ctx.run(command["path"] + ["--name", "clia-preview", "--dry-run", "--json"])
        payload = _json(result)
        if result.code != 0 or not payload:
            problems.append("create dry-run failed")
        else:
            for key in ("method", "url", "headers", "body"):
                if key not in payload:
                    problems.append("dry-run lacks " + key)
            if payload.get("method") != "POST":
                problems.append("dry-run method is not POST")
            if (payload.get("body") or {}).get("name") != "clia-preview":
                problems.append("dry-run body lacks the request fields")
            if "target" not in payload:
                problems.append("dry-run lacks the resolved target")
            if ctx.token and ctx.token in result.out:
                problems.append("dry-run leaked the token")
    if delete:
        result = ctx.run(delete["path"] + [ctx.cfg["sample_id"], "--dry-run", "--json"])
        payload = _json(result)
        if result.code != 0 or not payload or payload.get("method") != "DELETE":
            problems.append("destructive dry-run failed")
        elif ctx.token and ctx.token in result.out:
            problems.append("delete dry-run leaked the token")
    return ctx.check("M20", not problems, "; ".join(problems) or "structured, redacted dry-run")


def check_m48(ctx):
    list_cmd = _resource(ctx, "list")
    get_cmd = _resource(ctx, "get")
    create_cmd = _resource(ctx, "create")
    delete_cmd = _resource(ctx, "delete")
    problems = []
    help_result = ctx.run(["--help"])
    status = ctx.run(["auth", "status", "--json"])
    payload = _json(status) or {}
    if help_result.code != 0 or status.code != 0 or payload.get("authenticated") is not True:
        problems.append("task 1 discover/auth failed")
    if list_cmd:
        result = ctx.run(list_cmd["path"] + ["--limit", "5", "--json"])
        page = _json(result) or {}
        if result.code != 0 or not isinstance(page.get("data"), list) or len(page["data"]) > 5:
            problems.append("task 2 list failed")
    if get_cmd:
        result = ctx.run(get_cmd["path"] + [ctx.cfg["sample_id"], "--json"])
        item = _json(result) or {}
        if result.code != 0 or item.get("id") != ctx.cfg["sample_id"]:
            problems.append("task 3 get failed")
    created_id = None
    if create_cmd:
        name = "clia-canonical"
        preview = ctx.run(create_cmd["path"] + ["--name", name, "--dry-run", "--json"])
        preview_payload = _json(preview) or {}
        if preview.code != 0 or preview_payload.get("method") != "POST":
            problems.append("task 4 dry-run failed")
        created = ctx.run(create_cmd["path"] + ["--name", name, "--json"])
        created_payload = _json(created) or {}
        if created.code != 0 or not created_payload.get("id"):
            problems.append("task 4 create failed")
        else:
            created_id = created_payload["id"]
    if delete_cmd:
        target = created_id or ctx.cfg["sample_id"]
        refused = ctx.run(delete_cmd["path"] + [target, "--json"], stdin=b"")
        if refused.code != 10 or "--yes" not in refused.err:
            problems.append("task 5 did not refuse safely with exit 10")
        if created_id:
            cleanup = ctx.run(delete_cmd["path"] + [created_id, "--yes", "--json"])
            if cleanup.code != 0:
                problems.append("cleanup delete failed")
    return ctx.check("M48", not problems, "; ".join(problems) or "five canonical tasks pass")


def all_checks(ctx):
    check_m13(ctx)
    check_m14(ctx)
    check_m15(ctx)
    check_m16(ctx)
    check_m17(ctx)
    check_m18(ctx)
    check_m19(ctx)
    check_m20(ctx)
    check_m48(ctx)

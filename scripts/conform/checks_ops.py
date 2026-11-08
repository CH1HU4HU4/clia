"""Checks for auth, config, refresh, startup, CI, tests, goldens, and the agent path."""

from __future__ import annotations

import glob
import json
import os
import statistics
import time
from datetime import datetime, timedelta, timezone

from . import goldens
from .rules import P0_CHECK_IDS


def check_m28(ctx):
    problems = []
    status = ctx.run(["auth", "status", "--json"])
    payload = status.json_out() or {}
    if status.code != 0 or payload.get("authenticated") is not True:
        problems.append("auth status is not authenticated")
    who = ctx.run(["whoami", "--json"])
    if who.code != 0 or not (who.json_out() or {}).get("user"):
        problems.append("whoami failed")
    out = ctx.run(["auth", "logout", "--json"])
    if out.code != 0:
        problems.append("auth logout failed")
    after = ctx.run(["auth", "status", "--json"], env_extra={ctx.token_env: None})
    after_payload = after.json_out() or {}
    if after.code != 0 or after_payload.get("authenticated") is not False:
        problems.append("auth status still authenticated after logout")
    login = ctx.cfg.get("login") or []
    if login:
        restored = ctx.run([str(piece).replace("{token}", ctx.token) for piece in login])
        if restored.code != 0:
            problems.append("auth login did not restore the credential")
    return ctx.check("M28", not problems, "; ".join(problems) or "login, logout, status, whoami")


def check_m30(ctx):
    path = ctx.config_file()
    problems = []
    if not os.path.exists(path):
        problems.append("config file not found at " + path)
    else:
        mode = os.stat(path).st_mode & 0o777
        if mode & 0o077:
            problems.append("config mode is %o, want 600" % mode)
    list_cmd = ctx.resource_command("list")
    if list_cmd:
        debug = ctx.run(list_cmd["path"] + ["--limit", "1", "--json", "--debug"])
        if ctx.token and ctx.token in debug.err:
            problems.append("--debug leaked the token")
        if ctx.token and ctx.token in debug.out:
            problems.append("stdout leaked the token")
    bad = ctx.run(["project", "list", "--json"],
                  env_extra={ctx.token_env: ctx.cfg["bad_token"]})
    if ctx.token and ctx.token in bad.err:
        problems.append("error output leaked the token")
    listing = ctx.run(["config", "list", "--json"])
    if ctx.token and ctx.token in listing.out:
        problems.append("config list leaked the token")
    return ctx.check("M30", not problems, "; ".join(problems) or "0600 and no secret exposure")


def _last_header(ctx, method, suffix, header):
    stats = ctx.mock.stats() if ctx.mock else {"requests": []}
    for entry in reversed(stats.get("requests", [])):
        if entry["method"] == method and entry["path"].endswith(suffix):
            return (entry.get("headers") or {}).get(header.lower())
    return None


def check_m31(ctx):
    list_cmd = ctx.resource_command("list")
    if not list_cmd:
        return ctx.na("M31", "no list command")
    problems = []
    setup = ctx.run(["config", "set", "base-url", ctx.base_url, "--profile", "staging"])
    if setup.code != 0:
        problems.append("could not write the staging profile")
    listed = ctx.run(list_cmd["path"] + ["--limit", "1", "--json", "--profile", "staging"])
    if listed.code != 0:
        problems.append("--profile staging failed")

    ctx.run(["config", "set", "base-url", "http://127.0.0.1:1"])
    overridden = ctx.run(list_cmd["path"] + ["--limit", "1", "--json", "--base-url", ctx.base_url])
    if overridden.code != 0:
        problems.append("--base-url override failed")
    ctx.run(["config", "set", "base-url", ctx.base_url])

    versioned = ctx.run(list_cmd["path"] + ["--limit", "1", "--json",
                                            "--api-version", "2025-01-01"])
    if versioned.code != 0:
        problems.append("--api-version 2025-01-01 failed")
    seen = _last_header(ctx, "GET", "/projects", "x-api-version")
    if seen != "2025-01-01":
        problems.append("API version header was %r" % seen)
    unsupported = ctx.run(list_cmd["path"] + ["--json", "--api-version", "1999-01-01"])
    if unsupported.code != 6:
        problems.append("unsupported API version exit %d, want 6" % unsupported.code)
    if "2026-01-01" not in unsupported.err:
        problems.append("unsupported version error lacks the supported versions")

    ctx.run(["config", "set", "output", "json"])
    machine = ctx.run(list_cmd["path"] + ["--limit", "1"])
    if machine.code != 0 or machine.json_out() is None:
        problems.append("output=json setting did not apply")
    ctx.run(["config", "unset", "output"])
    return ctx.check("M31", not problems, "; ".join(problems) or "profiles, base URL, version, output mode")


def check_m32(ctx):
    result = ctx.run(["whoami", "--json"])
    payload = result.json_out() or {}
    missing = [key for key in ("user", "org", "profile", "environment", "token_expires_at")
               if key not in payload]
    ok = result.code == 0 and not missing
    return ctx.check("M32", ok, "whoami has user, org, profile, environment, expiry" if ok
                     else "missing: " + ", ".join(missing))


def check_m33(ctx):
    doctor = ctx.command("doctor")
    if not doctor:
        return ctx.defer("M33", "doctor not shipped (P1)")
    result = ctx.run(["doctor", "--json"])
    if result.code not in (0, 12):
        return ctx.check("M33", False, "doctor exit %d" % result.code)
    payload = result.json_out()
    if isinstance(payload, dict) and "checks" in payload:
        return ctx.check("M33", True, "doctor reports checks")
    if isinstance(payload, list):
        return ctx.check("M33", True, "doctor reports checks")
    return ctx.check("M33", False, "doctor --json has no checks")


def check_m34(ctx):
    if not (ctx.cfg.get("capabilities") or {}).get("refresh", True):
        return ctx.na("M34", "API inventory: tokens do not expire")
    if not ctx.mock:
        return ctx.defer("M34", "no mock control for the refresh test")
    problems = []
    seeded = ctx.mock.seed_short_token()
    ctx.run(["config", "set", "access-token", seeded["access_token"]])
    ctx.run(["config", "set", "refresh-token", seeded["refresh_token"]])
    ctx.run(["config", "set", "expires-at", seeded["expires_at"]])
    listed = ctx.run(["project", "list", "--limit", "1", "--json"],
                     env_extra={ctx.token_env: None})
    if listed.code != 0:
        problems.append("command with an expiring token failed")
    stats = ctx.mock.stats()
    if stats.get("counts", {}).get("POST /v1/auth/refresh", 0) < 1:
        problems.append("no refresh request was made")

    ctx.mock.revoke_refresh()
    soon = (datetime.now(timezone.utc) + timedelta(seconds=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    ctx.run(["config", "set", "refresh-token", "rt_invalid"])
    ctx.run(["config", "set", "expires-at", soon])
    failed = ctx.run(["project", "list", "--limit", "1", "--json"],
                     env_extra={ctx.token_env: None})
    if failed.code != 3:
        problems.append("failed refresh exit %d, want 3" % failed.code)
    if "auth login" not in failed.err.lower():
        problems.append("failed refresh lacks an auth login hint")

    login = ctx.cfg.get("login") or []
    if login:
        ctx.run([str(piece).replace("{token}", ctx.token) for piece in login])
    return ctx.check("M34", not problems, "; ".join(problems) or "refresh before expiry, exit 3 on failure")


def check_m37(ctx):
    samples = []
    for _ in range(10):
        result = ctx.run(["--version"], timeout=10)
        if result.code != 0:
            return ctx.check("M37", False, "--version failed during the startup sample")
        samples.append(result.ms)
    median = statistics.median(samples)
    budget = int(ctx.cfg.get("startup_budget_ms") or 300)
    return ctx.check("M37", median <= budget, "median %d ms (budget %d ms)" % (median, budget))


def check_m38(ctx):
    if not (ctx.cfg.get("capabilities") or {}).get("update_check", False):
        return ctx.defer("M38", "update checks not shipped (P1)")
    helps = " ".join(command.get("help", "") for command in ctx.commands.values())
    if "--no-update-check" not in helps:
        return ctx.check("M38", False, "no --no-update-check flag")
    return ctx.check("M38", True, "update checks can be disabled")


def _read(path):
    try:
        return open(path, encoding="utf-8").read()
    except OSError:
        return ""


def check_m39(ctx):
    workflows = []
    for pattern in ("*.yml", "*.yaml"):
        workflows.extend(glob.glob(os.path.join(ctx.repo, ".github", "workflows", pattern)))
    text = "\n".join(_read(path) for path in workflows)
    readme = _read(os.path.join(ctx.repo, "README.md"))
    problems = []
    if not workflows:
        problems.append("no CI workflow")
    if "upload-artifact" not in text and "actions/upload" not in text:
        problems.append("CI does not upload an artifact")
    if not any(word in text.lower() for word in ("sha256", "shasum", "checksum")):
        problems.append("CI produces no checksums")
    if not any(word in readme.lower() for word in ("pip install", "pipx install", "npm install",
                                                   "install .", "brew install", "install.sh")):
        problems.append("README has no install line")
    return ctx.check("M39", not problems, "; ".join(problems) or "artifact, checksums, install line")


def check_m40(ctx):
    command = ctx.cfg.get("test_command")
    if not command:
        return ctx.check("M40", False, "no test_command configured")
    import shlex
    import subprocess
    argv = shlex.split(command) if isinstance(command, str) else list(command)
    try:
        proc = subprocess.run(argv, cwd=ctx.repo, env=ctx.runner.env, capture_output=True,
                              text=True, timeout=180)
        code = proc.returncode
        tail_text = (proc.stderr or proc.stdout or "").strip()
    except subprocess.TimeoutExpired:
        code = -9
        tail_text = "test command timed out"
    tail = tail_text.splitlines()[-1:] or [""]
    ok = code == 0
    return ctx.check("M40", ok, "tests pass: " + tail[0][:120] if ok
                     else "tests exit %d: %s" % (code, tail[0][:160]))


def check_m41(ctx):
    golden_dir = ctx.cfg.get("golden_dir") or "tests/golden"
    if not os.path.isabs(golden_dir):
        golden_dir = os.path.join(ctx.repo, golden_dir)
    ok, detail = goldens.verify(ctx, golden_dir, update=bool(getattr(ctx, "update_goldens", False)))
    return ctx.check("M41", ok, detail)


def check_m45(ctx):
    problems = []
    for path, command in sorted(ctx.commands.items()):
        if command.get("group"):
            continue
        result = ctx.offline(list(path) + ["--help"], timeout=10)
        if result.code != 0:
            problems.append("help for %s exited %d" % (" ".join(path), result.code))
    list_cmd = ctx.resource_command("list")
    get_cmd = ctx.resource_command("get")
    create_cmd = ctx.resource_command("create")
    delete_cmd = ctx.resource_command("delete")
    probes = []
    if list_cmd:
        probes.append((list_cmd["path"] + ["--limit", "1", "--json"], 0))
    if get_cmd:
        probes.append((get_cmd["path"] + [ctx.cfg["sample_id"], "--json"], 0))
    if create_cmd:
        probes.append((create_cmd["path"] + ["--name", "clia-noinput", "--dry-run", "--json"], 0))
    if delete_cmd:
        probes.append((delete_cmd["path"] + [ctx.cfg["sample_id"], "--json"], 10))
    probes.append((["auth", "status", "--json"], 0))
    probes.append((["whoami", "--json"], 0))
    probes.append((["config", "list", "--json"], 0))
    for args, expected in probes:
        result = ctx.run(args, stdin=b"", timeout=15)
        if "command timed out" in result.err:
            problems.append("hang: " + " ".join(args))
        elif result.code != expected:
            problems.append("%s exit %d, want %d" % (" ".join(args), result.code, expected))
        if "Continue?" in result.err:
            problems.append("prompted with stdin closed: " + " ".join(args))
    return ctx.check("M45", not problems, "; ".join(problems[:4]) or "no prompts or hangs with stdin closed")


def check_m46(ctx):
    schema = ctx.command("schema")
    if not schema:
        return ctx.defer("M46", "schema not shipped (P1)")
    result = ctx.run(["schema"])
    payload = result.json_out()
    ok = result.code == 0 and isinstance(payload, dict) and len(payload.get("commands") or []) >= 3
    return ctx.check("M46", ok, "schema describes %d commands" % len((payload or {}).get("commands") or [])
                     if ok else "schema --json invalid")


def check_m42(ctx):
    failures = []
    missing = []
    for rule_id in P0_CHECK_IDS:
        if rule_id == "M42":
            continue
        status = ctx.report.status(rule_id)
        if status is None:
            missing.append(rule_id)
        elif status == "FAIL":
            failures.append(rule_id)
    ok = not failures and not missing
    detail = "all applicable P0 checks pass"
    if failures:
        detail = "failing: " + ", ".join(failures)
    if missing:
        detail = (detail + "; " if failures else "") + "not run: " + ", ".join(missing)
    return ctx.check("M42", ok, detail)


def all_checks(ctx):
    check_m28(ctx)
    check_m30(ctx)
    check_m31(ctx)
    check_m32(ctx)
    check_m33(ctx)
    check_m34(ctx)
    check_m37(ctx)
    check_m38(ctx)
    check_m39(ctx)
    check_m40(ctx)
    check_m41(ctx)
    check_m45(ctx)
    check_m46(ctx)
    check_m42(ctx)

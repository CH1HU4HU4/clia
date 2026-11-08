"""Checks for destructive safety, idempotency, updates, ambiguity, and HTTPS."""

from __future__ import annotations

import json
import time

from .util import run_tty


def _create(ctx, name, extra=None):
    command = ctx.resource_command("create")
    if not command:
        return None
    result = ctx.run(command["path"] + ["--name", name] + list(extra or []) + ["--json"])
    return result.json_out() if result.code == 0 else None


def _delete(ctx, project_id, yes=False):
    command = ctx.resource_command("delete")
    if not command:
        return None
    args = command["path"] + [project_id]
    if yes:
        args.append("--yes")
    return ctx.run(args + ["--json"], stdin=b"")


def check_m21(ctx):
    delete = ctx.resource_command("delete")
    if not delete:
        return ctx.na("M21", "product has no destructive command")
    name = "clia-tty-%d" % int(time.time())
    created = _create(ctx, name)
    if not created:
        return ctx.check("M21", False, "could not create a project for the delete test")
    project_id = created["id"]
    problems = []

    refused = _delete(ctx, project_id)
    payload = refused.json_err() or {}
    error = payload.get("error") or {}
    if refused.code != 10:
        problems.append("non-TTY delete exit %d, want 10" % refused.code)
    if error.get("code") != "confirmation_required":
        problems.append("non-TTY delete code %r" % error.get("code"))
    if "--yes" not in (error.get("hint") or ""):
        problems.append("non-TTY hint lacks --yes")

    argv = ctx.runner.binary + delete["path"] + [project_id]
    code, text, sent = run_tty(argv, ctx.runner.cwd, ctx.runner.env, answer=b"n\n")
    if code != 10:
        problems.append("TTY decline exit %d, want 10" % code)
    if not sent or "Continue?" not in text:
        problems.append("TTY prompt not shown")
    if ctx.base_url.split("//")[-1] not in text:
        problems.append("TTY prompt does not echo the target")

    code, text, sent = run_tty(argv, ctx.runner.cwd, ctx.runner.env, answer=b"y\n")
    if code != 0:
        problems.append("TTY confirm exit %d, want 0" % code)
    if not sent:
        problems.append("TTY confirm prompt not shown")

    leftovers = ctx.run(delete["path"] + [project_id, "--yes", "--json"], stdin=b"")
    if leftovers.code not in (0, 5):
        problems.append("cleanup delete exit %d" % leftovers.code)
    return ctx.check("M21", not problems, "; ".join(problems) or "TTY prompt, --yes off TTY, exit 10")


def check_m22(ctx):
    delete = ctx.resource_command("delete")
    if not delete:
        return ctx.na("M22", "product has no destructive command")
    problems = []
    result = ctx.run(delete["path"] + [ctx.cfg["sample_id"], "--dry-run", "--json"])
    payload = result.json_out() or {}
    if result.code != 0:
        problems.append("dry-run exit %d" % result.code)
    if payload.get("method") != "DELETE":
        problems.append("dry-run method is not DELETE")
    if "target" not in payload:
        problems.append("dry-run lacks target")
    if ctx.token and ctx.token in result.out:
        problems.append("dry-run leaked the token")
    still_there = ctx.run(ctx.resource_command("get")["path"] + [ctx.cfg["sample_id"], "--json"])
    if still_there.code != 0:
        problems.append("dry-run deleted the resource")
    return ctx.check("M22", not problems, "; ".join(problems) or "destructive dry-run is safe")


def check_m23(ctx):
    if not (ctx.cfg.get("capabilities") or {}).get("idempotency", True):
        return ctx.na("M23", "API inventory: no idempotency key support")
    create = ctx.resource_command("create")
    if not create:
        return ctx.na("M23", "no create command")
    name = "clia-idem-%d" % int(time.time())
    key = "clia-idem-key-%d" % int(time.time())
    first = ctx.run(create["path"] + ["--name", name, "--idempotency-key", key, "--json"])
    second = ctx.run(create["path"] + ["--name", name, "--idempotency-key", key, "--json"])
    one = first.json_out() or {}
    two = second.json_out() or {}
    problems = []
    if first.code != 0 or second.code != 0:
        problems.append("idempotent create failed (%d, %d)" % (first.code, second.code))
    elif one.get("id") != two.get("id"):
        problems.append("same key produced two resources")
    stats = ctx.mock.stats() if ctx.mock else {"requests": []}
    posts = [entry for entry in stats.get("requests", [])
             if entry["method"] == "POST" and entry["path"].endswith("/projects")]
    if not posts:
        problems.append("no create request recorded")
    elif not all(entry.get("idempotency_key") for entry in posts):
        problems.append("a create request sent no idempotency key")
    if problems:
        return ctx.check("M23", False, "; ".join(problems))
    delete = ctx.resource_command("delete")
    if delete and one.get("id"):
        ctx.run(delete["path"] + [one["id"], "--yes", "--json"], stdin=b"")
    return ctx.check("M23", True, "idempotency key sent; retry did not duplicate")


def check_m24(ctx):
    if not (ctx.cfg.get("capabilities") or {}).get("bulk", False):
        return ctx.na("M24", "API inventory: no bulk endpoint")
    verbs = ctx.verbs()
    if not any("bulk" in " ".join(command["path"]) or "--all" in command.get("help", "")
               for command in ctx.data_commands()):
        return ctx.check("M24", False, "bulk capability declared but no bulk command found")
    return ctx.check("M24", True, "bulk command present")


def check_m25(ctx):
    update = ctx.resource_command("update")
    if not update:
        return ctx.na("M25", "no update command")
    name = "clia-update-%d" % int(time.time())
    created = _create(ctx, name)
    if not created:
        return ctx.check("M25", False, "could not create a project for the update test")
    project_id = created["id"]
    problems = []
    changed = ctx.run(update["path"] + [project_id, "--set", "description=changed", "--json"])
    payload = changed.json_out() or {}
    if changed.code != 0 or payload.get("description") != "changed":
        problems.append("--set did not change the field")
    cleared = ctx.run(update["path"] + [project_id, "--unset", "description", "--json"])
    cleared_payload = cleared.json_out() or {}
    if cleared.code != 0 or cleared_payload.get("description") not in (None, ""):
        problems.append("--unset did not clear the field")
    stats = ctx.mock.stats() if ctx.mock else {"requests": []}
    patches = [entry for entry in stats.get("requests", [])
               if entry["method"] == "PATCH" and entry["path"].endswith(project_id)]
    if not patches:
        problems.append("no PATCH request recorded")
    elif set((patches[-1].get("body") or {}).keys()) != {"description"}:
        problems.append("update sent more than the changed field: %r" % (patches[-1].get("body") or {}))
    delete = ctx.resource_command("delete")
    if delete:
        ctx.run(delete["path"] + [project_id, "--yes", "--json"], stdin=b"")
    return ctx.check("M25", not problems, "; ".join(problems) or "--set and --unset send only the patch")


def check_m26(ctx):
    if not (ctx.cfg.get("capabilities") or {}).get("jobs", False):
        return ctx.na("M26", "API inventory: no async jobs")
    wait = ctx.command("wait") or ctx.command(ctx.cfg["resource"], "wait")
    flags = any("--wait" in command.get("help", "") for command in ctx.commands.values())
    if not wait or not flags:
        return ctx.check("M26", False, "jobs declared but --wait/wait command missing")
    return ctx.check("M26", True, "job, --wait, and wait command present")


def check_m27(ctx):
    get = ctx.resource_command("get")
    if not get:
        return ctx.na("M27", "no get command")
    result = ctx.run(get["path"] + [ctx.cfg["ambiguous"], "--json"])
    payload = result.json_err() or {}
    error = payload.get("error") or {}
    problems = []
    if result.code != 11:
        problems.append("ambiguous lookup exit %d, want 11" % result.code)
    if error.get("code") != "ambiguous_target":
        problems.append("code %r" % error.get("code"))
    candidates = error.get("candidates") or []
    if len(candidates) < 2:
        problems.append("ambiguity did not list candidates")
    return ctx.check("M27", not problems, "; ".join(problems) or "ambiguous name exits 11 with candidates")


def _lan_ip():
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()


def check_m43(ctx):
    problems = []
    list_cmd = ctx.resource_command("list")
    if list_cmd:
        refused = ctx.run(list_cmd["path"] + ["--base-url", "http://api.example.com", "--json"])
        if refused.code == 0:
            problems.append("plain http to a non-loopback host was accepted")
        if "http" not in refused.err.lower():
            problems.append("http refusal has no explanation")
    for path, command in ctx.commands.items():
        if ctx.has_flag(command, "--insecure") or "--insecure" in command.get("help", ""):
            problems.append("--insecure exists on " + " ".join(path))
            break
    ip = _lan_ip()
    if ip and list_cmd:
        proxied = ctx.run(
            list_cmd["path"] + ["--limit", "1", "--base-url",
                                "http://%s:%s" % (ip, _mock_port(ctx)), "--allow-http", "--json"],
            env_extra={"HTTP_PROXY": "http://127.0.0.1:1", "HTTPS_PROXY": "http://127.0.0.1:1",
                       "NO_PROXY": ""},
        )
        if proxied.code != 8:
            problems.append("proxy variables were ignored (exit %d)" % proxied.code)
    return ctx.check("M43", not problems, "; ".join(problems) or "HTTPS enforced, proxy honored, no --insecure")


def _mock_port(ctx):
    try:
        return ctx.base_url.rsplit(":", 1)[1].rstrip("/")
    except IndexError:
        return "80"


def check_m44(ctx):
    if not (ctx.cfg.get("capabilities") or {}).get("files", False):
        return ctx.na("M44", "API inventory: no file endpoints")
    downloads = [command for command in ctx.data_commands()
                 if "download" in " ".join(command["path"])]
    uploads = [command for command in ctx.data_commands()
               if "upload" in " ".join(command["path"])]
    if not downloads and not uploads:
        return ctx.check("M44", False, "files declared but no file commands found")
    return ctx.check("M44", True, "file commands present")


def all_checks(ctx):
    check_m21(ctx)
    check_m22(ctx)
    check_m23(ctx)
    check_m24(ctx)
    check_m25(ctx)
    check_m26(ctx)
    check_m27(ctx)
    check_m43(ctx)
    check_m44(ctx)

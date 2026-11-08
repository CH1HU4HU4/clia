"""Log in with a token or a device flow. Both work without a browser prompt."""

from __future__ import annotations

import getpass
import sys
import time

from ...args import flag
from ...errors import CliError, UsageError
from ...output import print_json, print_text
from ... import config as config_store

SPEC = {
    "path": ("auth", "login"),
    "summary": "Log in",
    "description": "Store an API token, or run the device flow. Off a TTY, pass --token or --device.",
    "arguments": [],
    "flags": [
        flag("--device", desc="Use the OAuth device flow (never prompts)"),
    ],
    "examples": [
        "acme auth login --token $ACME_TOKEN",
        "acme auth login --device",
    ],
    "related": ["acme auth status", "acme whoami"],
    "data": True,
}


def _save(ctx, access_token, refresh_token=None, expires_at=None):
    config_store.set_value(ctx.profile, "access_token", access_token, create=False)
    if refresh_token:
        config_store.set_value(ctx.profile, "refresh_token", refresh_token, create=False)
    else:
        config_store.unset_value(ctx.profile, "refresh_token")
    if expires_at:
        config_store.set_value(ctx.profile, "expires_at", expires_at, create=False)
    else:
        config_store.unset_value(ctx.profile, "expires_at")


def _device_login(api, ctx):
    device = api.public_post("/v1/auth/device", {"client": "acme-cli"})
    uri = device.get("verification_uri", "")
    code = device.get("user_code", "")
    interval = max(1, int(device.get("interval") or 1))
    sys.stderr.write("Open %s and enter code %s\n" % (uri, code))
    sys.stderr.flush()
    deadline = time.time() + 120
    while time.time() < deadline:
        try:
            token = api.public_post("/v1/auth/token", {"device_code": device.get("device_code")})
            return token
        except CliError as err:
            if err.status == 428:
                time.sleep(interval)
                continue
            raise
    raise CliError("auth_required", "Device login timed out", "Run acme auth login --device again")


def run(ctx, opts, positionals):
    from ...api import Api
    api = Api(ctx)
    if opts.get("device"):
        token = _device_login(api, ctx)
        ctx.token = token.get("access_token")
        ctx.refresh_token = token.get("refresh_token")
        ctx.expires_at = token.get("expires_at")
        _save(ctx, token.get("access_token"), token.get("refresh_token"), token.get("expires_at"))
    else:
        token = opts.get("token")
        if not token:
            if not sys.stdin.isatty():
                raise UsageError("no token provided", "Pass --token, set ACME_TOKEN, or use --device")
            token = getpass.getpass("Paste API token: ").strip()
        if not token:
            raise UsageError("no token provided", "Pass --token or set ACME_TOKEN")
        ctx.token = token
        ctx.expires_at = None
        ctx.refresh_token = None
        _save(ctx, token)

    me = api.me()
    user = (me.get("user") or {}).get("email")
    payload = {
        "ok": True,
        "authenticated": True,
        "user": user,
        "org": me.get("org") or ctx.org,
        "profile": ctx.profile,
        "token": None,
    }
    if ctx.output == "json":
        print_json(payload)
    else:
        print_text("Logged in as %s (org %s, profile %s)" % (user, payload["org"], ctx.profile))
    return 0

SPEC["run"] = run

"""One resolver for profile, base URL, org, project, API version, and token.

Every command calls resolve_context(); no command reads config directly.
"""

from __future__ import annotations

import os

from . import config
from .constants import DEFAULT_API_VERSION, DEFAULT_BASE_URL, ENV, TOOL
from .errors import CliError


class Context:
    def __init__(self, profile, base_url, org, project, api_version, output,
                 token, expires_at, refresh_token, timeout, allow_http,
                 debug, config_data):
        self.profile = profile
        self.base_url = base_url
        self.org = org
        self.project = project
        self.api_version = api_version
        self.output = output
        self.token = token
        self.expires_at = expires_at
        self.refresh_token = refresh_token
        self.timeout = timeout
        self.allow_http = allow_http
        self.debug = debug
        self.config_data = config_data


def _env(name):
    return os.environ.get(ENV + "_" + name)


def _first(*values):
    for value in values:
        if value is not None and value != "":
            return value
    return None


def resolve_context(opts, allow_missing_profile=False):
    data = config.load()
    explicit_profile = _first(opts.get("profile"), _env("PROFILE"))
    profile = explicit_profile or str(data.get("profile") or "default")
    values = config.profile_values(data, profile)
    if values is None:
        if explicit_profile and not allow_missing_profile:
            known = ", ".join(sorted(data["profiles"])) or "(none)"
            raise CliError(
                "validation",
                "Profile %s is not configured" % profile,
                "Configured profiles: %s. Run %s config set profile %s" % (known, TOOL, profile),
            )
        values = {}

    base_url = str(_first(opts.get("base_url"), _env("BASE_URL"),
                          values.get("base_url"), DEFAULT_BASE_URL))
    api_version = str(_first(opts.get("api_version"), _env("API_VERSION"),
                            values.get("api_version"), DEFAULT_API_VERSION))
    org = str(_first(opts.get("org"), _env("ORG"), values.get("org"), "") or "")
    project = str(_first(opts.get("project"), _env("PROJECT"), values.get("project"), "") or "")

    output = str(_first(_env("OUTPUT"), values.get("output"), "table"))
    if opts.get("json"):
        output = "json"
    elif opts.get("quiet"):
        output = "quiet"
    if output not in ("table", "json", "quiet"):
        raise CliError("validation", "Unsupported output mode %r" % output,
                       "Use table, json, or quiet")

    token = _first(opts.get("token"), _env("TOKEN"), _env("API_KEY"),
                   values.get("access_token"))

    timeout_raw = str(_first(opts.get("timeout"), _env("TIMEOUT"), "30"))
    try:
        timeout = float(timeout_raw)
        if timeout <= 0:
            raise ValueError
    except ValueError:
        raise CliError("usage", "--timeout must be a positive number",
                       "Pass seconds, for example --timeout 30")

    return Context(
        profile=profile,
        base_url=base_url,
        org=org,
        project=project,
        api_version=api_version,
        output=output,
        token=token,
        expires_at=values.get("expires_at"),
        refresh_token=values.get("refresh_token"),
        timeout=timeout,
        allow_http=bool(opts.get("allow_http")),
        debug=bool(opts.get("debug")),
        config_data=data,
    )

"""Shared config command helpers: allowed keys, sources, masking."""

from __future__ import annotations

import os

from ... import config as config_store
from ...constants import ENV
from ...errors import UsageError
from ...redact import mask

KEYS = ["profile", "base_url", "api_version", "org", "project", "output",
        "access_token", "refresh_token", "expires_at"]
SECRETS = ("access_token", "refresh_token")

ENV_FOR = {
    "base_url": ENV + "_BASE_URL",
    "api_version": ENV + "_API_VERSION",
    "org": ENV + "_ORG",
    "project": ENV + "_PROJECT",
    "output": ENV + "_OUTPUT",
    "profile": ENV + "_PROFILE",
    "access_token": ENV + "_TOKEN",
}

OUTPUT_CHOICES = ("table", "json", "quiet")


def normalize(key):
    return str(key).replace("-", "_")


def validate_key(key):
    key = normalize(key)
    if key not in KEYS:
        raise UsageError('unknown config key "%s"' % key, "Allowed: " + ", ".join(KEYS))
    return key


def validate_value(key, value):
    if key == "output" and value not in OUTPUT_CHOICES:
        raise UsageError("output must be table, json, or quiet", "Got %r" % value)
    if key == "base_url":
        if not (value.startswith("http://") or value.startswith("https://")):
            raise UsageError("base_url must start with http:// or https://", "Got %r" % value)
    if key == "profile" and not value:
        raise UsageError("profile cannot be empty")
    return value


def source(profile, key):
    env = ENV_FOR.get(key)
    if env and os.environ.get(env):
        return "env"
    try:
        flat = config_store.parse_toml(open(config_store.config_path(), encoding="utf-8").read())
    except OSError:
        flat = {}
    if key == "profile" and "profile" in flat:
        return "file"
    if "profiles.%s.%s" % (profile, key) in flat:
        return "file"
    return "default"


def display(key, value):
    if key in SECRETS and value:
        return mask(value)
    return value

"""User config: TOML subset, profiles, credential precedence, 0600 enforcement.

Path: $XDG_CONFIG_HOME/acme/config.toml (default ~/.config/acme/config.toml).
Project config (./.acme/config.toml) may hold context only, never credentials.
"""

from __future__ import annotations

import json
import os
import stat

from .constants import DEFAULT_API_VERSION, DEFAULT_BASE_URL, ENV, TOOL
from .errors import CliError

TOKEN_KEYS = ("access_token", "refresh_token")
SECRET_KEYS = TOKEN_KEYS + ("api_key",)


def config_home():
    return os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")


def config_path():
    return os.path.join(config_home(), TOOL, "config.toml")


def project_config_path():
    return os.path.join(os.getcwd(), "." + TOOL, "config.toml")


def defaults():
    return {
        "profile": "default",
        "profiles": {
            "default": {
                "base_url": DEFAULT_BASE_URL,
                "api_version": DEFAULT_API_VERSION,
                "org": "",
                "project": "",
                "output": "table",
            }
        },
    }


def _parse_value(raw):
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"') and len(raw) >= 2:
        try:
            return json.loads(raw)
        except ValueError:
            return raw[1:-1]
    if raw in ("true", "false"):
        return raw == "true"
    if raw.lstrip("-").isdigit():
        return int(raw)
    return raw


def _strip_comment(line):
    quoted = False
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if char == "\\":
            escaped = True
            continue
        if char == '"':
            quoted = not quoted
            continue
        if char == "#" and not quoted:
            return line[:index]
    return line


def parse_toml(text):
    data = {}
    section = []
    for raw_line in text.splitlines():
        line = _strip_comment(raw_line).strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip().split(".")
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if not key:
            continue
        data[".".join(section + [key])] = _parse_value(value)
    return data


def _format_value(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value))


def dump_toml(flat):
    top = {}
    sections = {}
    for key, value in flat.items():
        if "." in key:
            section, _, leaf = key.rpartition(".")
            sections.setdefault(section, {})[leaf] = value
        else:
            top[key] = value
    lines = []
    for key in sorted(top):
        lines.append("%s = %s" % (key, _format_value(top[key])))
    for section in sorted(sections):
        if lines:
            lines.append("")
        lines.append("[%s]" % section)
        for key in sorted(sections[section]):
            lines.append("%s = %s" % (key, _format_value(sections[section][key])))
    return "\n".join(lines) + "\n"


def _flatten(data):
    flat = {}
    for key, value in data.items():
        if key == "profiles":
            for profile, values in value.items():
                for leaf, leaf_value in values.items():
                    flat["profiles.%s.%s" % (profile, leaf)] = leaf_value
        else:
            flat[key] = value
    return flat


def load():
    """Read the config, refusing a world-readable file that holds a token."""
    path = config_path()
    data = defaults()
    if not os.path.exists(path):
        return data
    mode = os.stat(path).st_mode
    if mode & (stat.S_IRWXG | stat.S_IRWXO):
        text = open(path, encoding="utf-8").read()
        if any(key in text for key in SECRET_KEYS):
            raise CliError(
                "validation",
                "Refusing to read %s: it is readable by other users and contains a token" % path,
                "Run: chmod 600 %s" % path,
            )
    text = open(path, encoding="utf-8").read()
    flat = parse_toml(text)
    if "profile" in flat:
        data["profile"] = str(flat["profile"])
    merged = {}
    for key, value in flat.items():
        if key.startswith("profiles."):
            _, profile, leaf = key.split(".", 2)
            merged.setdefault(profile, {})[leaf] = value
    for profile, values in merged.items():
        base = data["profiles"].get(profile, {})
        base.update(values)
        data["profiles"][profile] = base
    return data


def save(data):
    path = config_path()
    directory = os.path.dirname(path)
    os.makedirs(directory, mode=0o700, exist_ok=True)
    flat = _flatten(data)
    temp = path + ".tmp"
    handle = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        stream.write(dump_toml(flat))
    os.replace(temp, path)
    os.chmod(path, 0o600)


def profile_values(data, profile):
    values = data["profiles"].get(profile)
    if values is None:
        return None
    merged = dict(data["profiles"].get("default", {}))
    merged.update(values)
    return merged


def set_value(profile, key, value, create=False):
    data = load()
    if key == "profile":
        data["profile"] = value
        save(data)
        return
    values = data["profiles"].get(profile)
    if values is None:
        if not create:
            raise CliError(
                "validation",
                "Profile %s is not configured" % profile,
                "Run: %s config set profile %s" % (TOOL, profile),
            )
        values = {}
        data["profiles"][profile] = values
    if isinstance(value, str):
        lowered = value.lower()
        if lowered in ("true", "false"):
            value = lowered == "true"
    values[key] = value
    save(data)


def unset_value(profile, key):
    data = load()
    if key == "profile":
        data.pop("profile", None)
        save(data)
        return
    values = data["profiles"].get(profile)
    if values is None:
        raise CliError("validation", "Profile %s is not configured" % profile)
    values.pop(key, None)
    save(data)

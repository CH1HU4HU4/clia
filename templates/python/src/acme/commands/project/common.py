"""Shared project helpers: name resolution, fields, pagination."""

from __future__ import annotations

from urllib.parse import quote

from ...constants import ALL_CAP, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from ...errors import CliError, UsageError

SUMMARY_FIELDS = ["id", "name", "status", "owner", "created_at", "updated_at"]
FULL_FIELDS = SUMMARY_FIELDS + ["description", "settings", "counts", "metadata"]

LIST_COLUMNS = [
    ("id", "id", None),
    ("name", "name", 30),
    ("status", "status", 10),
    ("owner", "owner", 28),
    ("updated", "updated_at", 20),
]

GET_FIELDS = [
    ("id", "id"),
    ("name", "name"),
    ("status", "status"),
    ("owner", "owner"),
    ("description", "description"),
    ("created_at", "created_at"),
    ("updated_at", "updated_at"),
    ("settings", "settings"),
    ("counts", "counts"),
]


def path_for(project_id):
    return "/v1/projects/" + quote(str(project_id), safe="")


def resolve_project(api, value):
    """Accept an ID or a name. One direct read for an ID, one lookup for a name."""
    try:
        return api.get(path_for(value))
    except CliError as err:
        if err.code != "not_found":
            raise
    page = api.get("/v1/projects", [("name", value), ("limit", "2")])
    matches = page.get("data") or []
    if len(matches) == 1:
        return api.get(path_for(matches[0]["id"]))
    if len(matches) > 1:
        candidates = [{"id": item["id"], "name": item["name"]} for item in matches]
        raise CliError(
            "ambiguous_target",
            'Multiple projects match "%s"' % value,
            "Retry with a project ID, for example: acme project get %s" % matches[0]["id"],
            extra={"candidates": candidates},
        )
    raise CliError("not_found", "Project %s not found" % value, "Run acme project list")


def page_limit(opts):
    raw = opts.get("limit")
    try:
        limit = int(raw)
    except (TypeError, ValueError):
        raise UsageError("--limit must be an integer", "Pass a number from 1 to 200")
    if limit < 1 or limit > MAX_PAGE_SIZE:
        raise UsageError("--limit must be between 1 and %d" % MAX_PAGE_SIZE,
                         "Default is %d" % DEFAULT_PAGE_SIZE)
    return limit


def list_query(opts, cursor=None):
    query = [("limit", page_limit(opts))]
    selected = cursor if cursor is not None else opts.get("cursor")
    if selected:
        query.append(("cursor", selected))
    if opts.get("sort"):
        query.append(("sort", opts["sort"]))
    for item in opts.get("filter") or []:
        query.append(("filter", item))
    for name in ("search", "status", "owner", "since", "until"):
        if opts.get(name):
            query.append((name, opts[name]))
    if opts.get("full"):
        query.append(("full", "1"))
    return query


def requested_fields(opts):
    raw = opts.get("fields")
    if not raw:
        return None
    allowed = FULL_FIELDS if opts.get("full") else SUMMARY_FIELDS
    fields = [part.strip() for part in str(raw).split(",") if part.strip()]
    unknown = [field for field in fields if field not in allowed]
    if unknown:
        raise UsageError("unknown field %r" % unknown[0],
                         "Allowed now: " + ", ".join(allowed)
                         + (" (use --full for " + ", ".join(FULL_FIELDS[len(SUMMARY_FIELDS):]) + ")"
                            if not opts.get("full") else ""))
    return fields


def shape(item, full=False, fields=None):
    source = item if full else {key: value for key, value in item.items() if key in SUMMARY_FIELDS}
    if fields:
        source = {key: source.get(key) for key in fields}
    return source


def fetch(api, opts):
    """Return (items, has_more, next_cursor, truncated). Never calls paging per command."""
    limit = page_limit(opts)
    cursor = opts.get("cursor")
    items = []
    has_more = False
    truncated = False
    while True:
        page = api.get("/v1/projects", list_query(opts, cursor))
        batch = page.get("data") or []
        room = ALL_CAP - len(items)
        if len(batch) > room:
            items.extend(batch[:room])
        else:
            items.extend(batch)
        has_more = bool(page.get("has_more"))
        cursor = page.get("next_cursor")
        if len(items) >= ALL_CAP and (has_more or opts.get("all")):
            truncated = True
            break
        if not opts.get("all") or not has_more or not cursor:
            break
    return items, has_more, cursor, truncated


def body_flags(opts):
    """Build a JSON body from --file, --data, and typed flags."""
    body = {}
    import json
    import sys
    if opts.get("data"):
        try:
            body = json.loads(opts["data"])
        except ValueError as err:
            raise UsageError("--data is not valid JSON: %s" % err, "Pass a JSON object")
        if not isinstance(body, dict):
            raise UsageError("--data must be a JSON object")
    if opts.get("file"):
        if opts["data"]:
            sys.stderr.write("warning: --file wins over --data\n")
        try:
            if opts["file"] == "-":
                raw = sys.stdin.read()
            else:
                with open(opts["file"], encoding="utf-8") as stream:
                    raw = stream.read()
        except OSError as err:
            raise UsageError("cannot read --file %s: %s" % (opts["file"], err))
        try:
            body = json.loads(raw)
        except ValueError as err:
            raise UsageError("--file is not valid JSON: %s" % err)
        if not isinstance(body, dict):
            raise UsageError("--file must contain a JSON object")
    return body


def coerce(value):
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered == "null":
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        return value


def nested_set(target, dotted, value):
    parts = dotted.split(".")
    cursor = target
    for part in parts[:-1]:
        if not isinstance(cursor.get(part), dict):
            cursor[part] = {}
        cursor = cursor[part]
    cursor[parts[-1]] = value


def patch_from_flags(opts):
    patch = body_flags(opts)
    for item in opts.get("set") or []:
        if "=" not in item:
            raise UsageError("--set expects key=value, got %r" % item, "Example: --set status=active")
        dotted, _, value = item.partition("=")
        nested_set(patch, dotted.strip(), coerce(value))
    for item in opts.get("unset") or []:
        nested_set(patch, item.strip(), None)
    return patch

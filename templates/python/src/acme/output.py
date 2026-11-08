"""All writes to stdout/stderr for data. Commands never format strings."""

from __future__ import annotations

import json
import sys

from .errors import target_dict

MAX_TABLE_WIDTH = 120


def _write(stream, text):
    stream.write(text + "\n")


def print_json(payload):
    _write(sys.stdout, json.dumps(payload, separators=(",", ":"), default=str))


def print_text(text, stream=None):
    _write(stream or sys.stdout, text)


def _cell(value, cap):
    if value is None:
        return "-"
    text = str(value)
    if cap and len(text) > cap:
        return text[: max(1, cap - 1)] + "\u2026"
    return text


def render_table(columns, rows):
    """columns: [(header, key, cap)]. IDs are never truncated (cap None)."""
    widths = []
    for header, _key, cap in columns:
        width = len(header)
        for row in rows:
            width = max(width, min(len(str(row.get(_key, ""))), cap or 10 ** 9))
        widths.append(width)
    width_total = sum(widths) + 3 * (len(columns) - 1)
    if width_total > MAX_TABLE_WIDTH:
        excess = width_total - MAX_TABLE_WIDTH
        for index, (_header, _key, cap) in enumerate(columns):
            if cap and excess > 0:
                squeeze = min(excess, max(0, widths[index] - len(columns[index][0])))
                widths[index] -= squeeze
                excess -= squeeze
    header_line = "   ".join(
        header.upper().ljust(widths[index]) for index, (header, _key, _cap) in enumerate(columns)
    ).rstrip()
    lines = [header_line]
    for row in rows:
        cells = []
        for index, (_header, key, cap) in enumerate(columns):
            text = _cell(row.get(key), cap)
            if len(text) > widths[index]:
                text = text[: max(1, widths[index] - 1)] + "\u2026"
            cells.append(text.ljust(widths[index]))
        lines.append("   ".join(cells).rstrip())
    return "\n".join(lines)


def list_envelope(items, has_more, next_cursor, truncated):
    return {
        "data": items,
        "has_more": bool(has_more),
        "next_cursor": next_cursor,
        "truncated": bool(truncated),
    }


def emit_list(items, ctx, opts, columns, label, id_key="id", has_more=False,
              next_cursor=None, truncated=False, empty_message=None):
    if ctx.output == "json":
        print_json(list_envelope(items, has_more, next_cursor, truncated))
        return
    if ctx.output == "quiet":
        for item in items:
            value = item.get(id_key)
            if value is not None:
                _write(sys.stdout, str(value))
        return
    if not items:
        _write(sys.stderr, empty_message or ("No %s found." % label))
        return
    _write(sys.stdout, render_table(columns, items))
    if truncated:
        _write(sys.stderr, "warning: stopped at the 10,000 item cap; results are truncated."
               + (" Next: --cursor %s" % next_cursor if next_cursor else ""))
    elif has_more and next_cursor:
        _write(sys.stderr, "Showing %d. Next: --cursor %s" % (len(items), next_cursor))


def emit_object(obj, ctx, opts, fields=None):
    fields = fields or []
    if ctx.output == "json":
        print_json(obj)
        return
    if ctx.output == "quiet":
        value = obj.get("id")
        if value is not None:
            _write(sys.stdout, str(value))
        return
    for key, label in fields:
        value = obj.get(key)
        if value is None:
            value = "-"
        elif isinstance(value, (dict, list)):
            value = json.dumps(value, separators=(",", ":"))
        _write(sys.stdout, "%s: %s" % (label, value))


def emit_action(payload, ctx, message):
    if ctx.output == "json":
        print_json(payload)
        return
    _write(sys.stdout, message)


def emit_dry_run(preview, ctx, opts):
    preview = dict(preview)
    target = target_dict(ctx)
    if target:
        preview["target"] = target
    if ctx.output == "json":
        print_json(preview)
        return
    _write(sys.stderr, "Dry run: no request sent")
    _write(sys.stderr, "%s %s" % (preview["method"], preview["url"]))
    if preview.get("headers"):
        _write(sys.stderr, "headers: " + json.dumps(preview["headers"], separators=(",", ":")))
    if preview.get("body") is not None:
        _write(sys.stderr, "body: " + json.dumps(preview["body"], separators=(",", ":")))
    if target:
        _write(sys.stderr, "target: profile %s, %s, org %s, project %s, API %s"
               % (target["profile"], target["base_url"], target["org"],
                  target["project"], target["api_version"]))

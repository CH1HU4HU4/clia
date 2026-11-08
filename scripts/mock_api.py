#!/usr/bin/env python3
"""Mock SaaS API used by the CLIA conformance checker and eval fixtures.

Models a small projects API with cursor pagination, idempotent creates,
partial updates, name ambiguity, expiring device-flow tokens, refresh, and
injectable 401/403/404/409/422/429/500/timeout conditions.

Run:
    python3 scripts/mock_api.py --port 0          # prints {"port": N} then serves
    python3 scripts/mock_api.py --port 8787       # fixed port
    python3 scripts/mock_api.py --port 0 --quiet  # no startup line

Debug endpoints (no auth):
    GET  /__debug/stats        request log, counts
    POST /__debug/reset        restore seed data, clear log and tokens
    POST /__debug/revoke_refresh   make every refresh token invalid
    GET  /__debug/health       {"ok": true}

Environment:
    MOCK_API_PORT   fallback when --port is omitted (default 0)
"""

import argparse
import base64
import json
import os
import sys
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

SUPPORTED_VERSIONS = ["2026-01-01", "2025-01-01"]
DEFAULT_VERSION = "2026-01-01"
STATIC_TOKEN = "test-token"
STATIC_TOKEN_EXPIRED = "expired-token"

SUMMARY_FIELDS = ["id", "name", "status", "owner", "created_at", "updated_at"]
FULL_EXTRA_FIELDS = ["description", "settings", "counts", "metadata"]

LOCK = threading.RLock()
STATE = {}


def iso(dt):
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def now_iso():
    return iso(datetime.now(timezone.utc))


def seed():
    base = datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
    rows = [
        ("prj_001", "web", "active", "alice@acme.com", "Customer-facing web app"),
        ("prj_002", "api", "active", "bob@acme.com", "Public HTTP API"),
        ("prj_003", "data", "paused", "carol@acme.com", "Warehouse pipelines"),
        ("prj_004", "worker", "active", "alice@acme.com", "Background jobs"),
        ("prj_005", "billing", "active", "dave@acme.com", "Invoices and plans"),
        ("prj_006", "docs", "archived", "carol@acme.com", "Documentation site"),
        ("prj_007", "dupe", "active", "alice@acme.com", "First project named dupe"),
        ("prj_008", "dupe", "active", "bob@acme.com", "Second project named dupe"),
        ("prj_009", "existing", "active", "dave@acme.com", "Used for conflict tests"),
    ]
    projects = {}
    for index, (pid, name, status, owner, description) in enumerate(rows):
        created = base + timedelta(days=index)
        projects[pid] = {
            "id": pid,
            "name": name,
            "status": status,
            "owner": owner,
            "created_at": iso(created),
            "updated_at": iso(created + timedelta(hours=2)),
            "description": description,
            "settings": {"region": "us-east-1", "retention_days": 30 + index},
            "counts": {"deployments": index * 3, "members": index + 1},
            "metadata": {"tier": "pro" if index % 2 else "free"},
        }
    projects["prj_forbidden"] = make_project("prj_forbidden", "forbidden", "active")
    projects["prj_ratelimit"] = make_project("prj_ratelimit", "ratelimit", "active")
    projects["prj_servererror"] = make_project("prj_servererror", "servererror", "active")
    projects["prj_slow"] = make_project("prj_slow", "slow", "active")
    return {
        "projects": projects,
        "idempotency": {},
        "requests": [],
        "refresh_tokens": {},
        "access_tokens": {},
        "refresh_valid": True,
        "created": 0,
        "deleted": 0,
    }


def make_project(pid, name, status):
    stamp = "2026-02-01T00:00:00Z"
    return {
        "id": pid,
        "name": name,
        "status": status,
        "owner": "omer@acme.com",
        "created_at": stamp,
        "updated_at": stamp,
        "description": "Fixture project " + name,
        "settings": {"region": "us-east-1", "retention_days": 30},
        "counts": {"deployments": 0, "members": 1},
        "metadata": {"tier": "pro"},
    }


STATE = seed()


def summary(project):
    return {key: project[key] for key in SUMMARY_FIELDS}


def full(project):
    return dict(project)


class ApiError(Exception):
    def __init__(self, status, code, message, hint=None, extra=None):
        Exception.__init__(self, message)
        self.status = status
        self.code = code
        self.message = message
        self.hint = hint
        self.extra = extra or {}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "clia-mock/1.0"

    def log_message(self, fmt, *args):
        if not self.server.quiet:
            sys.stderr.write("mock: " + (fmt % args) + "\n")

    # -- plumbing ---------------------------------------------------------
    def _read_body(self):
        length = int(self.headers.get("content-length") or 0)
        if not length:
            return None
        raw = self.rfile.read(length)
        if not raw:
            return None
        try:
            return json.loads(raw.decode("utf-8"))
        except ValueError:
            raise ApiError(400, "validation", "Request body is not valid JSON")

    def _send(self, status, payload, headers=None):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.send_header("x-request-id", "req_" + uuid.uuid4().hex[:10])
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _error(self, err):
        payload = {
            "error": {
                "code": err.code,
                "message": err.message,
                "status": err.status,
            }
        }
        if err.hint:
            payload["error"]["hint"] = err.hint
        payload["error"].update(err.extra)
        self._send(err.status, payload)

    def _record(self, status, body):
        entry = {
            "method": self.command,
            "path": urlparse(self.path).path,
            "query": parse_qs(urlparse(self.path).query),
            "headers": {key.lower(): value for key, value in self.headers.items()},
            "body": body,
            "status": status,
            "time": time.time(),
            "idempotency_key": self.headers.get("idempotency-key"),
        }
        with LOCK:
            STATE["requests"].append(entry)

    def _auth(self):
        header = self.headers.get("authorization") or ""
        if not header.lower().startswith("bearer "):
            raise ApiError(401, "auth_required", "Missing bearer token", "Run acme auth login")
        token = header.split(None, 1)[1].strip()
        if token == STATIC_TOKEN and not getattr(self.server, "device_only", False):
            return {"user": "omer@acme.com", "org": "acme", "token_expires_at": None}
        if token == STATIC_TOKEN_EXPIRED:
            raise ApiError(401, "auth_required", "Token expired", "Run acme auth login")
        with LOCK:
            meta = STATE["access_tokens"].get(token)
            if not meta:
                raise ApiError(401, "auth_required", "Invalid token", "Run acme auth login")
            if meta["expires"] <= time.time():
                raise ApiError(401, "auth_required", "Token expired", "Run acme auth login")
            return {"user": "omer@acme.com", "org": meta.get("org", "acme"),
                    "token_expires_at": iso(datetime.fromtimestamp(meta["expires"], timezone.utc))}

    def _version(self):
        version = self.headers.get("x-api-version")
        if version and version not in SUPPORTED_VERSIONS:
            raise ApiError(
                400,
                "validation",
                "Unsupported API version %s" % version,
                "Supported versions: " + ", ".join(SUPPORTED_VERSIONS),
                {"supported_versions": SUPPORTED_VERSIONS},
            )
        return version or DEFAULT_VERSION

    # -- routing ----------------------------------------------------------
    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_PATCH(self):
        self._dispatch("PATCH")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def _dispatch(self, method):
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        body = None
        status = 200
        try:
            if path.startswith("/__debug/"):
                status, payload = self._debug(method, path, body)
                self._send(status, payload)
                return
            body = self._read_body() if method in ("POST", "PATCH", "PUT") else None
            status, payload, headers = self._route(method, path, query, body)
            self._record(status, body)
            self._send(status, payload, headers)
        except ApiError as err:
            self._record(err.status, body)
            self._error(err)
        except BrokenPipeError:
            pass
        except Exception as err:  # pragma: no cover - defensive
            self._record(500, body)
            self._error(ApiError(500, "server_error", "Mock server failure: %s" % err))

    def _debug(self, method, path, body):
        with LOCK:
            if path == "/__debug/health":
                return 200, {"ok": True}
            if path == "/__debug/stats":
                counts = {}
                for entry in STATE["requests"]:
                    key = entry["method"] + " " + entry["path"]
                    counts[key] = counts.get(key, 0) + 1
                return 200, {
                    "requests": list(STATE["requests"]),
                    "counts": counts,
                    "created": STATE["created"],
                    "deleted": STATE["deleted"],
                }
            if path == "/__debug/reset" and method == "POST":
                STATE.update(seed())
                return 200, {"ok": True}
            if path == "/__debug/revoke_refresh" and method == "POST":
                STATE["refresh_valid"] = False
                STATE["refresh_tokens"] = {}
                return 200, {"ok": True}
            if path == "/__debug/expire_tokens" and method == "POST":
                for meta in STATE["access_tokens"].values():
                    meta["expires"] = time.time() - 1
                return 200, {"ok": True}
            if path == "/__debug/seed_and_expire" and method == "POST":
                # Returns an access token that expires in 20 seconds and a
                # refresh token, for refresh tests that avoid device login.
                token = "at_" + uuid.uuid4().hex[:12]
                refresh = "rt_" + uuid.uuid4().hex[:12]
                STATE["access_tokens"][token] = {
                    "expires": time.time() + 20,
                    "org": "acme",
                }
                STATE["refresh_tokens"][refresh] = {"org": "acme"}
                return 200, {
                    "access_token": token,
                    "refresh_token": refresh,
                    "expires_at": iso(datetime.now(timezone.utc) + timedelta(seconds=20)),
                    "expires_in": 20,
                }
        return 404, {"error": {"code": "not_found", "message": "Unknown debug path"}}

    def _route(self, method, path, query, body):
        if path == "/v1/auth/device" and method == "POST":
            code = "dev_" + uuid.uuid4().hex[:10]
            return 201, {
                "device_code": code,
                "user_code": "ACME-1234",
                "verification_uri": "https://acme.test/activate",
                "interval": 1,
                "expires_in": 600,
            }, {}
        if path == "/v1/auth/token" and method == "POST":
            code = (body or {}).get("device_code")
            if not code:
                raise ApiError(400, "validation", "device_code is required")
            token = "at_" + uuid.uuid4().hex[:12]
            refresh = "rt_" + uuid.uuid4().hex[:12]
            expires = time.time() + 30
            with LOCK:
                STATE["access_tokens"][token] = {"expires": expires, "org": "acme"}
                STATE["refresh_tokens"][refresh] = {"org": "acme"}
            return 200, {
                "access_token": token,
                "refresh_token": refresh,
                "token_type": "bearer",
                "expires_in": 30,
                "expires_at": iso(datetime.fromtimestamp(expires, timezone.utc)),
                "org": "acme",
            }, {}
        if path == "/v1/auth/refresh" and method == "POST":
            refresh = (body or {}).get("refresh_token")
            with LOCK:
                meta = STATE["refresh_tokens"].get(refresh) if STATE["refresh_valid"] else None
                if not meta:
                    raise ApiError(401, "auth_required", "Refresh token rejected", "Run acme auth login")
                token = "at_" + uuid.uuid4().hex[:12]
                expires = time.time() + 3600
                STATE["access_tokens"][token] = {"expires": expires, "org": meta.get("org", "acme")}
            return 200, {
                "access_token": token,
                "token_type": "bearer",
                "expires_in": 3600,
                "expires_at": iso(datetime.fromtimestamp(expires, timezone.utc)),
            }, {}

        # Everything below needs auth and a version header.
        self._auth()
        self._version()

        if path == "/v1/me" and method == "GET":
            return 200, {
                "user": {"id": "usr_001", "email": "omer@acme.com", "name": "Omer"},
                "org": "acme",
                "environment": "sandbox",
                "token_expires_at": None,
            }, {}

        if path == "/v1/projects":
            if method == "GET":
                return 200, self._list_projects(query), {}
            if method == "POST":
                return self._create_project(body)

        if path.startswith("/v1/projects/"):
            pid = path.split("/")[3]
            if pid in ("prj_forbidden",):
                raise ApiError(403, "forbidden", "You lack permission for project %s" % pid,
                               "Ask an org owner for access")
            if pid == "prj_ratelimit":
                raise ApiError(429, "rate_limited", "Rate limit exceeded",
                               "Retry after 1 second", {"retry_after": 1})
            if pid == "prj_servererror":
                raise ApiError(500, "server_error", "Upstream failure", "Retry later")
            if pid == "prj_slow":
                time.sleep(3.0)
            if method == "GET":
                return 200, self._get_project(pid), {}
            if method == "PATCH":
                return self._update_project(pid, body)
            if method == "DELETE":
                return self._delete_project(pid)
        raise ApiError(404, "not_found", "Unknown endpoint %s" % path)

    def _list_projects(self, query):
        with LOCK:
            rows = list(STATE["projects"].values())
        name = first(query, "name")
        search = first(query, "search")
        status = first(query, "status")
        owner = first(query, "owner")
        if name is not None:
            rows = [p for p in rows if p["name"] == name]
        if status:
            rows = [p for p in rows if p["status"] == status]
        if owner:
            rows = [p for p in rows if p["owner"] == owner]
        for expr in query.get("filter", []):
            key, _, value = expr.partition("=")
            rows = [p for p in rows if str(p.get(key, "")) == value]
        if search:
            hay = search.lower()
            rows = [p for p in rows if hay in p["name"].lower() or hay in p["description"].lower()]
        sort = first(query, "sort") or "-created_at"
        descending = sort.startswith("-")
        field = sort[1:] if descending else sort
        if field not in SUMMARY_FIELDS and field not in FULL_EXTRA_FIELDS:
            raise ApiError(400, "validation", "Cannot sort by %s" % field,
                           "Sortable: " + ", ".join(SUMMARY_FIELDS))
        rows.sort(key=lambda p: str(p.get(field, "")), reverse=descending)

        try:
            limit = int(first(query, "limit") or 50)
        except ValueError:
            raise ApiError(400, "validation", "limit must be an integer")
        if limit < 1:
            raise ApiError(400, "validation", "limit must be at least 1")
        limit = min(limit, 200)
        offset = decode_cursor(first(query, "cursor") or "")
        page = rows[offset:offset + limit]
        next_offset = offset + len(page)
        has_more = next_offset < len(rows)
        full_mode = first(query, "full") in ("1", "true")
        return {
            "data": [full(p) if full_mode else summary(p) for p in page],
            "has_more": has_more,
            "next_cursor": encode_cursor(next_offset) if has_more else None,
        }

    def _get_project(self, pid):
        with LOCK:
            project = STATE["projects"].get(pid)
        if not project:
            raise ApiError(404, "not_found", "Project %s not found" % pid,
                           "Run acme project list")
        return full(project)

    def _create_project(self, body):
        if not isinstance(body, dict):
            raise ApiError(400, "validation", "JSON body is required")
        name = body.get("name")
        if not name:
            raise ApiError(422, "validation", "name is required", "Pass --name <name>",
                           {"fields": {"name": "required"}})
        key = self.headers.get("idempotency-key")
        with LOCK:
            if key and key in STATE["idempotency"]:
                return 201, full(STATE["projects"][STATE["idempotency"][key]]), {}
            if any(p["name"] == name for p in STATE["projects"].values()):
                raise ApiError(409, "conflict", "A project named %s already exists" % name,
                               "Run acme project list --filter name=%s" % name)
            pid = "prj_" + uuid.uuid4().hex[:6]
            stamp = now_iso()
            project = {
                "id": pid,
                "name": name,
                "status": "active",
                "owner": "omer@acme.com",
                "created_at": stamp,
                "updated_at": stamp,
                "description": body.get("description", ""),
                "settings": body.get("settings", {"region": "us-east-1", "retention_days": 30}),
                "counts": {"deployments": 0, "members": 1},
                "metadata": body.get("metadata", {"tier": "free"}),
            }
            STATE["projects"][pid] = project
            STATE["created"] += 1
            if key:
                STATE["idempotency"][key] = pid
            return 201, full(project), {}

    def _update_project(self, pid, body):
        if not isinstance(body, dict):
            raise ApiError(400, "validation", "JSON body is required")
        allowed = {"name", "description", "status", "owner", "settings", "metadata"}
        unknown = sorted(set(body) - allowed)
        if unknown:
            raise ApiError(422, "validation", "Unknown field(s): " + ", ".join(unknown),
                           "Allowed: " + ", ".join(sorted(allowed)),
                           {"fields": {key: "unknown" for key in unknown}})
        if "status" in body and body["status"] not in ("active", "paused", "archived"):
            raise ApiError(422, "validation", "Invalid status %s" % body["status"],
                           "Use active, paused, or archived")
        with LOCK:
            project = STATE["projects"].get(pid)
            if not project:
                raise ApiError(404, "not_found", "Project %s not found" % pid,
                               "Run acme project list")
            if "name" in body and body["name"] != project["name"]:
                if any(p["name"] == body["name"] and p["id"] != pid for p in STATE["projects"].values()):
                    raise ApiError(409, "conflict", "A project named %s already exists" % body["name"])
            project.update(body)
            project["updated_at"] = now_iso()
            return 200, full(project), {}

    def _delete_project(self, pid):
        with LOCK:
            project = STATE["projects"].pop(pid, None)
            if not project:
                raise ApiError(404, "not_found", "Project %s not found" % pid,
                               "Run acme project list")
            for key, value in list(STATE["idempotency"].items()):
                if value == pid:
                    del STATE["idempotency"][key]
            STATE["deleted"] += 1
        return 200, {"ok": True, "id": pid}, {}


def first(query, key):
    values = query.get(key)
    return values[0] if values else None


def encode_cursor(offset):
    return "cur_" + base64.urlsafe_b64encode(str(offset).encode()).decode().rstrip("=")


def decode_cursor(cursor):
    if not cursor:
        return 0
    if cursor.startswith("cur_"):
        raw = cursor[4:]
        padded = raw + "=" * (-len(raw) % 4)
        try:
            return int(base64.urlsafe_b64decode(padded.encode()).decode())
        except (ValueError, TypeError):
            raise ApiError(400, "validation", "Invalid cursor")
    raise ApiError(400, "validation", "Invalid cursor")


def main():
    parser = argparse.ArgumentParser(description="CLIA mock SaaS API")
    parser.add_argument("--port", type=int, default=int(os.environ.get("MOCK_API_PORT", "0")))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--device-only", action="store_true",
                        help="reject static tokens so only the device flow works")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.daemon_threads = True
    server.quiet = args.quiet
    server.device_only = args.device_only
    port = server.server_address[1]
    sys.stdout.write(json.dumps({"port": port}) + "\n")
    sys.stdout.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

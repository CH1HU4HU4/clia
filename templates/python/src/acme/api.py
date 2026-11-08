"""HTTP client: one place for URLs, auth, retries, refresh, timeouts, errors."""

from __future__ import annotations

import json
import socket
import sys
import time
from datetime import datetime, timedelta, timezone
from http.client import HTTPException
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from . import config
from .constants import ENV, TOOL, VERSION
from .errors import CliError, code_for_status
from .redact import mask, redact_headers, redact_text

LOOPBACK = ("localhost", "127.0.0.1", "::1")


def parse_time(value):
    if not value:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def platform_tag():
    import platform
    return "%s; %s" % (platform.system().lower() or "unknown", platform.machine() or "unknown")


class Api:
    def __init__(self, ctx):
        self.ctx = ctx
        self._refreshed = False

    # -- URL and headers --------------------------------------------------
    def url(self, path, query=None):
        base = self.ctx.base_url.rstrip("/")
        target = base + (path if path.startswith("/") else "/" + path)
        pairs = []
        for key, value in (query or []):
            if value is None:
                continue
            if isinstance(value, (list, tuple)):
                for item in value:
                    if item is not None:
                        pairs.append((key, item))
            else:
                pairs.append((key, value))
        if pairs:
            target += "?" + urlencode(pairs, doseq=True)
        return target

    def _check_base_url(self):
        parsed = urlparse(self.ctx.base_url)
        if parsed.scheme not in ("http", "https"):
            raise CliError("usage", "Base URL must be http or https, got %r" % self.ctx.base_url,
                           "Set --base-url https://api.example.com")
        if parsed.scheme == "http" and not self.ctx.allow_http:
            host = parsed.hostname or ""
            if host not in LOOPBACK:
                raise CliError("usage", "Refusing plain http base URL %s" % self.ctx.base_url,
                               "Use https, or pass --allow-http for a trusted loopback host")

    def headers(self, has_body=False, idempotency_key=None):
        headers = {
            "accept": "application/json",
            "user-agent": "%s/%s (%s)" % (TOOL, VERSION, platform_tag()),
            "x-api-version": self.ctx.api_version,
        }
        if self.ctx.token:
            headers["authorization"] = "Bearer " + self.ctx.token
        if has_body:
            headers["content-type"] = "application/json"
        if idempotency_key:
            headers["idempotency-key"] = idempotency_key
        return headers

    def preview(self, method, path, query=None, body=None, idempotency_key=None):
        headers = redact_headers(self.headers(body is not None, idempotency_key))
        return {
            "method": method,
            "url": self.url(path, query),
            "headers": headers,
            "body": body,
        }

    def debug(self, line):
        if self.ctx.debug:
            secrets = [self.ctx.token, self.ctx.refresh_token]
            sys.stderr.write("debug: " + redact_text(line, secrets) + "\n")

    # -- token refresh ----------------------------------------------------
    def _ensure_fresh(self):
        if self._refreshed or not self.ctx.expires_at or not self.ctx.refresh_token:
            return
        expires = parse_time(self.ctx.expires_at)
        if expires is None:
            return
        if expires - datetime.now(timezone.utc) > timedelta(seconds=60):
            return
        self._refreshed = True
        payload = self._raw_request(
            "POST", "/v1/auth/refresh", None, {"refresh_token": self.ctx.refresh_token}, None, False
        )
        token = payload.get("access_token")
        if not token:
            raise CliError("auth_required", "Token refresh returned no access token",
                           "Run %s auth login" % TOOL)
        self.ctx.token = token
        self.ctx.expires_at = payload.get("expires_at")
        try:
            config.set_value(self.ctx.profile, "access_token", token, create=False)
            if self.ctx.expires_at:
                config.set_value(self.ctx.profile, "expires_at", self.ctx.expires_at, create=False)
        except CliError:
            pass
        self.debug("token refreshed for profile %s" % self.ctx.profile)

    # -- requests ---------------------------------------------------------
    def request(self, method, path, query=None, body=None, idempotency_key=None):
        self._check_base_url()
        self._ensure_fresh()
        return self._raw_request(method, path, query, body, idempotency_key, True)

    def _raw_request(self, method, path, query, body, idempotency_key, with_auth):
        if with_auth and not self.ctx.token:
            raise CliError(
                "auth_required",
                "No API token configured",
                "Run %s auth login, set %s_TOKEN, or pass --token" % (TOOL, ENV),
            )
        url = self.url(path, query)
        headers = self.headers(body is not None, idempotency_key)
        if not with_auth:
            headers.pop("authorization", None)
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
        self.debug("%s %s" % (method, url))
        if self.ctx.debug:
            self.debug("headers: " + json.dumps(redact_headers(headers), separators=(",", ":")))
        can_retry = with_auth and (method in ("GET", "HEAD") or bool(idempotency_key))
        attempt = 0
        while True:
            attempt += 1
            started = time.time()
            try:
                request = Request(url, data=data, headers=headers, method=method)
                with urlopen(request, timeout=self.ctx.timeout) as response:
                    raw = response.read()
                    self.debug("< %d %s (%d ms)" % (
                        response.status, method, int((time.time() - started) * 1000)))
                    if not raw:
                        return {}
                    return json.loads(raw.decode("utf-8"))
            except HTTPError as err:
                raw = err.read()
                retry_after = err.headers.get("retry-after") if err.headers else None
                if err.code in (429, 500, 502, 503, 504) and can_retry and attempt < 3:
                    self._backoff(attempt, retry_after)
                    continue
                raise self._http_error(err.code, raw, err.headers)
            except (socket.timeout, TimeoutError):
                if can_retry and attempt < 3:
                    self._backoff(attempt, None)
                    continue
                raise CliError("timeout", "Request timed out after %ss" % self.ctx.timeout,
                               "Retry, or raise --timeout", retryable=True)
            except URLError as err:
                reason = getattr(err, "reason", err)
                if isinstance(reason, (socket.timeout, TimeoutError)):
                    if can_retry and attempt < 3:
                        self._backoff(attempt, None)
                        continue
                    raise CliError("timeout", "Request timed out after %ss" % self.ctx.timeout,
                                   "Retry, or raise --timeout", retryable=True)
                if can_retry and attempt < 3:
                    self._backoff(attempt, None)
                    continue
                raise CliError("network_error", "Cannot reach %s: %s" % (self.ctx.base_url, reason),
                               "Check the base URL and your network", retryable=True)
            except (HTTPException, ValueError) as err:
                raise CliError("network_error", "Invalid response: %s" % err,
                               "Retry, then run %s doctor" % TOOL, retryable=True)

    def _backoff(self, attempt, retry_after):
        delay = 0.25 * (2 ** (attempt - 1))
        if retry_after:
            try:
                delay = max(delay, float(retry_after))
            except ValueError:
                pass
        delay = min(delay, 2.0)
        self.debug("retrying in %.2fs" % delay)
        time.sleep(delay)

    def _http_error(self, status, raw, headers):
        code = code_for_status(status)
        message = "HTTP %d" % status
        hint = None
        extra = {}
        try:
            payload = json.loads(raw.decode("utf-8"))
            error = payload.get("error") or {}
            message = error.get("message") or message
            hint = error.get("hint")
            if error.get("supported_versions"):
                extra["supported_versions"] = error["supported_versions"]
            if error.get("fields"):
                extra["fields"] = error["fields"]
        except (ValueError, UnicodeDecodeError):
            if raw:
                message = raw.decode("utf-8", "replace").strip()[:300] or message
        retry_after = None
        if status == 429:
            header = headers.get("retry-after") if headers else None
            try:
                retry_after = int(header) if header is not None else 1
            except ValueError:
                retry_after = 1
            extra["retry_after"] = retry_after
        if code == "auth_required" and hint is None:
            hint = "Run %s auth login" % TOOL
        if code == "rate_limited" and hint is None:
            hint = "Retry after %s seconds" % retry_after
        return CliError(
            code,
            message,
            hint,
            status=status,
            retryable=code in ("rate_limited", "server_error"),
            request_id=headers.get("x-request-id") if headers else None,
            extra=extra,
        )

    # -- verbs ------------------------------------------------------------
    def get(self, path, query=None):
        return self.request("GET", path, query=query)

    def post(self, path, body=None, idempotency_key=None):
        return self.request("POST", path, body=body, idempotency_key=idempotency_key)

    def patch(self, path, body):
        return self.request("PATCH", path, body=body)

    def delete(self, path):
        return self.request("DELETE", path)

    def me(self):
        return self.get("/v1/me", [("org", self.ctx.org or None)])

    def public_post(self, path, body=None):
        """Unauthenticated POST for device login and token exchange."""
        self._check_base_url()
        return self._raw_request("POST", path, None, body, None, False)

    def token_masked(self):
        return mask(self.ctx.token)

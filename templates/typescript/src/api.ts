import * as config from "./config.ts";
import { ENV, TOOL, VERSION } from "./constants.ts";
import { platformTag } from "./context.ts";
import { CliError, authHint, codeForStatus } from "./errors.ts";
import { mask, redactHeaders, redactText } from "./redact.ts";

type Method = "GET" | "POST" | "PATCH" | "DELETE";
type Query = Array<[string, string | number | null | undefined]>;
type Target = { profile: string; base_url: string; org: string; project: string; api_version: string };

const LOOPBACK = ["localhost", "127.0.0.1", "::1"];

export function parseTime(value: string | null | undefined): number | null {
  if (!value) return null;
  const stamp = Date.parse(String(value).replace("Z", "+00:00"));
  return Number.isNaN(stamp) ? null : stamp;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export class Api {
  ctx: any;
  refreshed: boolean;
  target: Target | null;

  constructor(ctx: any) {
    this.ctx = ctx;
    this.refreshed = false;
    this.target = null;
  }

  url(path: string, query: Query = []): string {
    const base = String(this.ctx.baseUrl).replace(/\/+$/, "");
    const target = base + (path.startsWith("/") ? path : "/" + path);
    const params = new URLSearchParams();
    for (const [key, value] of query) {
      if (value === null || value === undefined) continue;
      params.append(key, String(value));
    }
    const encoded = params.toString();
    return encoded ? `${target}?${encoded}` : target;
  }

  checkBaseUrl(): void {
    let parsed: URL;
    try {
      parsed = new URL(this.ctx.baseUrl);
    } catch {
      throw new CliError("usage", `Base URL is not valid: ${this.ctx.baseUrl}`, "Set --base-url https://api.example.com");
    }
    if (!["http:", "https:"].includes(parsed.protocol)) {
      throw new CliError("usage", `Base URL must be http or https, got ${this.ctx.baseUrl}`, "Set --base-url https://api.example.com");
    }
    if (parsed.protocol === "http:" && !this.ctx.allowHttp) {
      const host = parsed.hostname;
      if (!LOOPBACK.includes(host)) {
        throw new CliError("usage", `Refusing plain http base URL ${this.ctx.baseUrl}`,
          "Use https, or pass --allow-http for a trusted loopback host");
      }
    }
  }

  headers(hasBody = false, idempotencyKey: string | null = null): Record<string, string> {
    const headers: Record<string, string> = {
      accept: "application/json",
      "user-agent": `${TOOL}/${VERSION} (${platformTag()})`,
      "x-api-version": this.ctx.apiVersion,
    };
    if (this.ctx.token) headers.authorization = "Bearer " + this.ctx.token;
    if (hasBody) headers["content-type"] = "application/json";
    if (idempotencyKey) headers["idempotency-key"] = idempotencyKey;
    return headers;
  }

  preview(method: Method, path: string, query: Query = [], body: unknown = null,
          idempotencyKey: string | null = null): Record<string, unknown> {
    return {
      method,
      url: this.url(path, query),
      headers: redactHeaders(this.headers(body !== null, idempotencyKey)),
      body,
    };
  }

  debug(line: string): void {
    if (!this.ctx.debug) return;
    process.stderr.write("debug: " + redactText(line, [this.ctx.token, this.ctx.refreshToken]) + "\n");
  }

  async ensureFresh(): Promise<void> {
    if (this.refreshed || !this.ctx.expiresAt || !this.ctx.refreshToken) return;
    const expires = parseTime(this.ctx.expiresAt);
    if (expires === null) return;
    if (expires - Date.now() > 60_000) return;
    this.refreshed = true;
    let payload: Record<string, any>;
    try {
      payload = await this.rawRequest("POST", "/v1/auth/refresh", [],
        { refresh_token: this.ctx.refreshToken }, null, false);
    } catch (err) {
      throw new CliError("auth_required", "Token refresh failed", authHint());
    }
    const token = payload.access_token;
    if (!token) throw new CliError("auth_required", "Token refresh returned no access token", authHint());
    this.ctx.token = token;
    this.ctx.expiresAt = payload.expires_at ?? null;
    try {
      config.setValue(this.ctx.profile, "access_token", token, false);
      if (this.ctx.expiresAt) config.setValue(this.ctx.profile, "expires_at", this.ctx.expiresAt, false);
    } catch {
      // The refreshed token still works for this run.
    }
    this.debug(`token refreshed for profile ${this.ctx.profile}`);
  }

  async request(method: Method, path: string, query: Query = [], body: unknown = null,
                idempotencyKey: string | null = null): Promise<Record<string, any>> {
    this.checkBaseUrl();
    await this.ensureFresh();
    return this.rawRequest(method, path, query, body, idempotencyKey, true);
  }

  async rawRequest(method: Method, path: string, query: Query, body: unknown,
                   idempotencyKey: string | null, withAuth: boolean): Promise<Record<string, any>> {
    if (withAuth && !this.ctx.token) {
      throw new CliError("auth_required", "No API token configured",
        `Run ${TOOL} auth login, set ${ENV}_TOKEN, or pass --token`);
    }
    const url = this.url(path, query);
    const headers = this.headers(body !== null, idempotencyKey);
    if (!withAuth) delete headers.authorization;
    const payloadBody = body === null ? undefined : JSON.stringify(body);
    this.debug(`${method} ${url}`);
    if (this.ctx.debug) this.debug("headers: " + JSON.stringify(redactHeaders(headers)));

    const canRetry = withAuth && (method === "GET" || Boolean(idempotencyKey));
    let attempt = 0;
    for (;;) {
      attempt += 1;
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), this.ctx.timeout * 1000);
      const started = Date.now();
      try {
        const response = await fetch(url, {
          method,
          headers,
          body: payloadBody,
          signal: controller.signal,
          redirect: "follow",
        });
        const text = await response.text();
        this.debug(`< ${response.status} ${method} (${Date.now() - started} ms)`);
        if (!response.ok) {
          const retryAfter = response.headers.get("retry-after");
          if ([429, 500, 502, 503, 504].includes(response.status) && canRetry && attempt < 3) {
            await this.backoff(attempt, retryAfter);
            continue;
          }
          throw this.httpError(response.status, text, response.headers);
        }
        if (!text) return {};
        try {
          return JSON.parse(text);
        } catch {
          throw new CliError("network_error", "Invalid JSON response", "Retry, then run acme doctor", null, true);
        }
      } catch (err) {
        if (err instanceof CliError) throw err;
        const name = (err as Error)?.name;
        const aborted = name === "AbortError" || name === "TimeoutError";
        if (aborted) {
          if (canRetry && attempt < 3) {
            await this.backoff(attempt, null);
            continue;
          }
          throw new CliError("timeout", `Request timed out after ${this.ctx.timeout}s`, "Retry, or raise --timeout");
        }
        const cause = (err as any)?.cause;
        const code = cause?.code || (err as Error)?.message || "network failure";
        if (canRetry && attempt < 3) {
          await this.backoff(attempt, null);
          continue;
        }
        throw new CliError("network_error", `Cannot reach ${this.ctx.baseUrl}: ${code}`,
          "Check the base URL and your network", null, true);
      } finally {
        clearTimeout(timer);
      }
    }
  }

  async backoff(attempt: number, retryAfter: string | null): Promise<void> {
    let delay = 250 * 2 ** (attempt - 1);
    if (retryAfter) {
      const parsed = Number(retryAfter);
      if (!Number.isNaN(parsed)) delay = Math.max(delay, parsed * 1000);
    }
    delay = Math.min(delay, 2000);
    this.debug(`retrying in ${delay}ms`);
    await sleep(delay);
  }

  httpError(status: number, text: string, headers: Headers): CliError {
    const code = codeForStatus(status);
    let message = `HTTP ${status}`;
    let hint: string | null = null;
    const extra: Record<string, unknown> = {};
    try {
      const payload = JSON.parse(text);
      const error = payload?.error || {};
      if (error.message) message = error.message;
      if (error.hint) hint = error.hint;
      if (error.supported_versions) extra.supported_versions = error.supported_versions;
      if (error.fields) extra.fields = error.fields;
    } catch {
      if (text) message = text.trim().slice(0, 300) || message;
    }
    if (status === 429) {
      const header = headers.get("retry-after");
      const retryAfter = header === null ? 1 : Number(header);
      extra.retry_after = Number.isNaN(retryAfter) ? 1 : retryAfter;
      if (!hint) hint = `Retry after ${extra.retry_after} seconds`;
    }
    if (code === "auth_required" && !hint) hint = authHint();
    return new CliError(code, message, hint, status,
      ["rate_limited", "server_error"].includes(code), headers.get("x-request-id"), null, extra);
  }

  get(path: string, query: Query = []): Promise<Record<string, any>> {
    return this.request("GET", path, query);
  }

  post(path: string, body: unknown, idempotencyKey: string | null = null): Promise<Record<string, any>> {
    return this.request("POST", path, [], body, idempotencyKey);
  }

  patch(path: string, body: unknown): Promise<Record<string, any>> {
    return this.request("PATCH", path, [], body);
  }

  delete(path: string): Promise<Record<string, any>> {
    return this.request("DELETE", path);
  }

  me(): Promise<Record<string, any>> {
    return this.get("/v1/me", [["org", this.ctx.org || null]]);
  }

  publicPost(path: string, body: unknown): Promise<Record<string, any>> {
    this.checkBaseUrl();
    return this.rawRequest("POST", path, [], body, null, false);
  }

  tokenMasked(): unknown {
    return mask(this.ctx.token);
  }
}

import { TOOL } from "./constants.ts";

export const EXIT_BY_CODE: Record<string, number> = {
  unexpected: 1,
  job_failed: 1,
  usage: 2,
  auth_required: 3,
  forbidden: 4,
  not_found: 5,
  conflict: 6,
  validation: 6,
  rate_limited: 7,
  server_error: 7,
  network_error: 8,
  timeout: 8,
  partial_success: 9,
  confirmation_required: 10,
  ambiguous_target: 11,
  diagnostic_failed: 12,
  cancelled: 130,
};

const HTTP_TO_CODE: Record<number, string> = {
  400: "validation",
  401: "auth_required",
  403: "forbidden",
  404: "not_found",
  409: "conflict",
  422: "validation",
  429: "rate_limited",
};

export function codeForStatus(status: number): string {
  if (HTTP_TO_CODE[status]) return HTTP_TO_CODE[status];
  if (status >= 500) return "server_error";
  if (status >= 400) return "validation";
  return "unexpected";
}

type Target = {
  profile: string;
  base_url: string;
  org: string;
  project: string;
  api_version: string;
};

export class CliError extends Error {
  code: string;
  hint: string | null;
  status: number | null;
  requestId: string | null;
  retryable: boolean;
  target: Target | null;
  extra: Record<string, unknown>;
  exit: number;

  constructor(
    code: string,
    message: string,
    hint: string | null = null,
    status: number | null = null,
    retryable: boolean | null = null,
    requestId: string | null = null,
    target: Target | null = null,
    extra: Record<string, unknown> | null = null,
  ) {
    super(message);
    this.code = code;
    this.hint = hint;
    this.status = status;
    this.requestId = requestId;
    this.retryable = retryable ?? ["rate_limited", "server_error", "network_error", "timeout"].includes(code);
    this.target = target;
    this.extra = extra ?? {};
    this.exit = EXIT_BY_CODE[code] ?? 1;
  }
}

export class UsageError extends CliError {
  constructor(message: string, hint: string | null = null) {
    super("usage", message, hint);
  }
}

export function targetDict(ctx: any): Target | null {
  if (!ctx || !ctx.profile) return null;
  return {
    profile: ctx.profile,
    base_url: ctx.baseUrl,
    org: ctx.org,
    project: ctx.project,
    api_version: ctx.apiVersion,
  };
}

export function errorPayload(err: CliError, ctx: any = null): Record<string, unknown> {
  const target = err.target ?? targetDict(ctx);
  const error: Record<string, unknown> = { code: err.code, message: err.message };
  if (err.hint) error.hint = err.hint;
  if (err.status !== null) error.status = err.status;
  if (err.requestId) error.request_id = err.requestId;
  error.retryable = Boolean(err.retryable);
  if (target) error.target = target;
  Object.assign(error, err.extra);
  return { error };
}

export function emitError(err: CliError, ctx: any = null, jsonMode = false): void {
  if (jsonMode) {
    process.stderr.write(JSON.stringify(errorPayload(err, ctx)) + "\n");
    return;
  }
  process.stderr.write("error: " + err.message + "\n");
  if (err.hint) process.stderr.write("hint: " + err.hint + "\n");
  const target = err.target ?? targetDict(ctx);
  if (target) {
    process.stderr.write(
      `target: profile ${target.profile}, ${target.base_url}, org ${target.org}, project ${target.project}, API ${target.api_version}\n`,
    );
  }
}

export function authHint(): string {
  return `Run ${TOOL} auth login`;
}

import * as os from "node:os";

import * as config from "./config.ts";
import { DEFAULT_API_VERSION, DEFAULT_BASE_URL, ENV, TOOL } from "./constants.ts";
import { CliError } from "./errors.ts";

export class Context {
  profile: string;
  baseUrl: string;
  org: string;
  project: string;
  apiVersion: string;
  output: string;
  token: string | null;
  expiresAt: string | null;
  refreshToken: string | null;
  timeout: number;
  allowHttp: boolean;
  debug: boolean;
  configData: config.ConfigData;

  constructor(values: {
    profile: string;
    baseUrl: string;
    org: string;
    project: string;
    apiVersion: string;
    output: string;
    token: string | null;
    expiresAt: string | null;
    refreshToken: string | null;
    timeout: number;
    allowHttp: boolean;
    debug: boolean;
    configData: config.ConfigData;
  }) {
    this.profile = values.profile;
    this.baseUrl = values.baseUrl;
    this.org = values.org;
    this.project = values.project;
    this.apiVersion = values.apiVersion;
    this.output = values.output;
    this.token = values.token;
    this.expiresAt = values.expiresAt;
    this.refreshToken = values.refreshToken;
    this.timeout = values.timeout;
    this.allowHttp = values.allowHttp;
    this.debug = values.debug;
    this.configData = values.configData;
  }
}

function env(name: string): string | undefined {
  return process.env[ENV + "_" + name];
}

function first(...values: Array<string | undefined | null>): string | null {
  for (const value of values) {
    if (value !== undefined && value !== null && value !== "") return value;
  }
  return null;
}

export function resolveContext(opts: Record<string, any>, allowMissingProfile = false): Context {
  const data = config.load();
  const explicitProfile = first(opts.profile, env("PROFILE"));
  const profile = explicitProfile || String(data.profile || "default");
  let values = config.profileValues(data, profile);
  if (values === null) {
    if (explicitProfile && !allowMissingProfile) {
      const known = Object.keys(data.profiles).sort().join(", ") || "(none)";
      throw new CliError(
        "validation",
        `Profile ${profile} is not configured`,
        `Configured profiles: ${known}. Run ${TOOL} config set profile ${profile}`,
      );
    }
    values = {};
  }

  const baseUrl = String(first(opts.base_url, env("BASE_URL"), values.base_url, DEFAULT_BASE_URL));
  const apiVersion = String(first(opts.api_version, env("API_VERSION"), values.api_version, DEFAULT_API_VERSION));
  const org = String(first(opts.org, env("ORG"), values.org, "") || "");
  const project = String(first(opts.project, env("PROJECT"), values.project, "") || "");

  let output = String(first(env("OUTPUT"), values.output, "table"));
  if (opts.json) output = "json";
  else if (opts.quiet) output = "quiet";
  if (!["table", "json", "quiet"].includes(output)) {
    throw new CliError("validation", `Unsupported output mode ${JSON.stringify(output)}`, "Use table, json, or quiet");
  }

  const token = first(opts.token, env("TOKEN"), env("API_KEY"), values.access_token);
  const timeoutRaw = String(first(opts.timeout, env("TIMEOUT"), "30"));
  const timeout = Number(timeoutRaw);
  if (!Number.isFinite(timeout) || timeout <= 0) {
    throw new CliError("usage", "--timeout must be a positive number", "Pass seconds, for example --timeout 30");
  }

  return new Context({
    profile,
    baseUrl,
    org,
    project,
    apiVersion,
    output,
    token,
    expiresAt: values.expires_at ?? null,
    refreshToken: values.refresh_token ?? null,
    timeout,
    allowHttp: Boolean(opts.allow_http),
    debug: Boolean(opts.debug),
    configData: data,
  });
}

export function platformTag(): string {
  return `${os.platform()}; ${os.arch()}`;
}

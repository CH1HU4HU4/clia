import * as fs from "node:fs";

import * as config from "../../config.ts";
import { ENV } from "../../constants.ts";
import { UsageError } from "../../errors.ts";
import { mask } from "../../redact.ts";

export const KEYS = ["profile", "base_url", "api_version", "org", "project", "output",
  "access_token", "refresh_token", "expires_at"];
const SECRETS = ["access_token", "refresh_token"];
const ENV_FOR: Record<string, string> = {
  base_url: ENV + "_BASE_URL",
  api_version: ENV + "_API_VERSION",
  org: ENV + "_ORG",
  project: ENV + "_PROJECT",
  output: ENV + "_OUTPUT",
  profile: ENV + "_PROFILE",
  access_token: ENV + "_TOKEN",
};
const OUTPUT_CHOICES = ["table", "json", "quiet"];

export function normalize(key: string): string {
  return String(key).replace(/-/g, "_");
}

export function validateKey(key: string): string {
  const normalized = normalize(key);
  if (!KEYS.includes(normalized)) {
    throw new UsageError(`unknown config key "${normalized}"`, "Allowed: " + KEYS.join(", "));
  }
  return normalized;
}

export function validateValue(key: string, value: string): string {
  if (key === "output" && !OUTPUT_CHOICES.includes(value)) {
    throw new UsageError("output must be table, json, or quiet", `Got '${value}'`);
  }
  if (key === "base_url" && !value.startsWith("http://") && !value.startsWith("https://")) {
    throw new UsageError("base_url must start with http:// or https://", `Got '${value}'`);
  }
  if (key === "profile" && !value) throw new UsageError("profile cannot be empty");
  return value;
}

export function source(profile: string, key: string): string {
  const envName = ENV_FOR[key];
  if (envName && process.env[envName]) return "env";
  let flat: Record<string, unknown> = {};
  try {
    flat = config.parseToml(fs.readFileSync(config.configPath(), "utf8"));
  } catch {
    flat = {};
  }
  if (key === "profile" && "profile" in flat) return "file";
  if (`profiles.${profile}.${key}` in flat) return "file";
  return "default";
}

export function display(key: string, value: unknown): unknown {
  if (SECRETS.includes(key) && value) return mask(value);
  return value;
}

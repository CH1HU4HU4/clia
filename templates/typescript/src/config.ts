import * as fs from "node:fs";
import * as os from "node:os";
import * as path from "node:path";

import { DEFAULT_API_VERSION, DEFAULT_BASE_URL, TOOL } from "./constants.ts";
import { CliError } from "./errors.ts";

export const TOKEN_KEYS = ["access_token", "refresh_token"];
const SECRET_KEYS = [...TOKEN_KEYS, "api_key"];

export type ProfileValues = Record<string, string>;
export type ConfigData = { profile: string; profiles: Record<string, ProfileValues> };

export function configHome(): string {
  return process.env.XDG_CONFIG_HOME || path.join(os.homedir(), ".config");
}

export function configPath(): string {
  return path.join(configHome(), TOOL, "config.toml");
}

export function projectConfigPath(): string {
  return path.join(process.cwd(), "." + TOOL, "config.toml");
}

export function defaults(): ConfigData {
  return {
    profile: "default",
    profiles: {
      default: {
        base_url: DEFAULT_BASE_URL,
        api_version: DEFAULT_API_VERSION,
        org: "",
        project: "",
        output: "table",
      },
    },
  };
}

function parseValue(raw: string): string | number | boolean {
  const text = raw.trim();
  if (text.startsWith("\"") && text.endsWith("\"") && text.length >= 2) {
    try {
      return JSON.parse(text);
    } catch {
      return text.slice(1, -1);
    }
  }
  if (text === "true" || text === "false") return text === "true";
  if (/^-?\d+$/.test(text)) return Number(text);
  return text;
}

function stripComment(line: string): string {
  let quoted = false;
  let escaped = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (escaped) {
      escaped = false;
      continue;
    }
    if (char === "\\") {
      escaped = true;
      continue;
    }
    if (char === "\"") {
      quoted = !quoted;
      continue;
    }
    if (char === "#" && !quoted) return line.slice(0, index);
  }
  return line;
}

export function parseToml(text: string): Record<string, string | number | boolean> {
  const data: Record<string, string | number | boolean> = {};
  let section: string[] = [];
  for (const rawLine of text.split(/\r?\n/)) {
    const line = stripComment(rawLine).trim();
    if (!line) continue;
    if (line.startsWith("[") && line.endsWith("]")) {
      section = line.slice(1, -1).trim().split(".");
      continue;
    }
    const equals = line.indexOf("=");
    if (equals < 0) continue;
    const key = line.slice(0, equals).trim();
    if (!key) continue;
    data[[...section, key].join(".")] = parseValue(line.slice(equals + 1));
  }
  return data;
}

function formatValue(value: unknown): string {
  if (typeof value === "boolean") return value ? "true" : "false";
  if (typeof value === "number") return String(value);
  return JSON.stringify(String(value));
}

export function dumpToml(flat: Record<string, string | number | boolean>): string {
  const top: Record<string, string | number | boolean> = {};
  const sections: Record<string, Record<string, string | number | boolean>> = {};
  for (const [key, value] of Object.entries(flat)) {
    const dot = key.lastIndexOf(".");
    if (dot >= 0) {
      const section = key.slice(0, dot);
      sections[section] = sections[section] || {};
      sections[section][key.slice(dot + 1)] = value;
    } else {
      top[key] = value;
    }
  }
  const lines: string[] = [];
  for (const key of Object.keys(top).sort()) lines.push(`${key} = ${formatValue(top[key])}`);
  for (const section of Object.keys(sections).sort()) {
    if (lines.length) lines.push("");
    lines.push(`[${section}]`);
    for (const key of Object.keys(sections[section]).sort()) {
      lines.push(`${key} = ${formatValue(sections[section][key])}`);
    }
  }
  return lines.join("\n") + "\n";
}

export function load(): ConfigData {
  const file = configPath();
  const data = defaults();
  if (!fs.existsSync(file)) return data;
  const stat = fs.statSync(file);
  if (stat.mode & 0o077) {
    const text = fs.readFileSync(file, "utf8");
    if (SECRET_KEYS.some((key) => text.includes(key))) {
      throw new CliError(
        "validation",
        `Refusing to read ${file}: it is readable by other users and contains a token`,
        `Run: chmod 600 ${file}`,
      );
    }
  }
  const flat = parseToml(fs.readFileSync(file, "utf8"));
  if (typeof flat.profile === "string") data.profile = flat.profile;
  for (const [key, value] of Object.entries(flat)) {
    if (!key.startsWith("profiles.")) continue;
    const parts = key.split(".");
    const profile = parts[1];
    const leaf = parts.slice(2).join(".");
    data.profiles[profile] = data.profiles[profile] || {};
    data.profiles[profile][leaf] = String(value);
  }
  return data;
}

export function save(data: ConfigData): void {
  const file = configPath();
  fs.mkdirSync(path.dirname(file), { recursive: true, mode: 0o700 });
  const flat: Record<string, string | number | boolean> = { profile: data.profile };
  for (const [profile, values] of Object.entries(data.profiles)) {
    for (const [key, value] of Object.entries(values)) flat[`profiles.${profile}.${key}`] = value;
  }
  const temp = file + ".tmp";
  fs.writeFileSync(temp, dumpToml(flat), { mode: 0o600 });
  fs.renameSync(temp, file);
  fs.chmodSync(file, 0o600);
}

export function profileValues(data: ConfigData, profile: string): ProfileValues | null {
  const values = data.profiles[profile];
  if (values === undefined) return null;
  return { ...(data.profiles.default || {}), ...values };
}

export function setValue(profile: string, key: string, value: string, create = false): void {
  const data = load();
  if (key === "profile") {
    data.profile = value;
    save(data);
    return;
  }
  let values = data.profiles[profile];
  if (values === undefined) {
    if (!create) {
      throw new CliError(
        "validation",
        `Profile ${profile} is not configured`,
        `Run: ${TOOL} config set profile ${profile}`,
      );
    }
    values = {};
    data.profiles[profile] = values;
  }
  values[key] = value;
  save(data);
}

export function unsetValue(profile: string, key: string): void {
  const data = load();
  if (key === "profile") {
    delete (data as Partial<ConfigData>).profile;
    save(data);
    return;
  }
  const values = data.profiles[profile];
  if (values === undefined) throw new CliError("validation", `Profile ${profile} is not configured`);
  delete values[key];
  save(data);
}

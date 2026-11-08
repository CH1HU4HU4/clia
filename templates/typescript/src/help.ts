import * as fs from "node:fs";

import * as config from "./config.ts";
import { DOCS_URL, ENV, TOOL, VERSION } from "./constants.ts";
import { GLOBAL_FLAGS, type FlagDef, type Spec } from "./args.ts";

const ROOT_ORDER = ["auth", "config", "project", "whoami", "version", "completion", "schema", "help"];
const EXIT_LINE =
  "0 success, 2 usage, 3 auth, 4 forbidden, 5 not found, 6 conflict, " +
  "7 rate limit/server, 8 network, 10 confirmation, 11 ambiguous";

let SPECS: Record<string, Spec> = {};

export function haveSpecs(specs: Record<string, Spec>): void {
  SPECS = specs;
}

function flagSyntax(item: FlagDef): string {
  let text = item.long;
  if (item.kind === "value") text += " " + (item.metavar || "<value>");
  if (item.short) text = item.short + ", " + text;
  return text;
}

function flagLine(item: FlagDef): string {
  const extras: string[] = [];
  if (item.kind === "value" && item.default !== null && item.default !== undefined && item.default !== "") {
    extras.push("default: " + item.default);
  }
  if (item.env) extras.push("env: " + item.env);
  let description = item.desc || "";
  if (extras.length) description = `${description} (${extras.join("; ")})`.trim();
  return "  " + flagSyntax(item).padEnd(30) + description.trimEnd();
}

function globalFlags(): FlagDef[] {
  return GLOBAL_FLAGS.filter((item) => item.long !== "--version");
}

function targetLine(): string | null {
  try {
    const configured = fs.existsSync(config.configPath()) || process.env[ENV + "_PROFILE"] || process.env[ENV + "_BASE_URL"];
    if (!configured) return null;
    const data = config.load();
    const profile = process.env[ENV + "_PROFILE"] || String(data.profile || "default");
    const values = config.profileValues(data, profile) || {};
    const base = process.env[ENV + "_BASE_URL"] || values.base_url || "";
    const org = process.env[ENV + "_ORG"] || values.org || "-";
    const project = process.env[ENV + "_PROJECT"] || values.project || "-";
    const version = process.env[ENV + "_API_VERSION"] || values.api_version || "-";
    return `Profile: ${profile} (${base}, org ${org}, project ${project}, API ${version})`;
  } catch {
    return null;
  }
}

export function rootHelp(): string {
  const lines = [
    `${TOOL} ${VERSION} \u2014 Command line for Acme`,
    "",
    "Manage Acme projects from a terminal or an agent.",
    "",
    "Usage:",
    `  ${TOOL} <command> [flags]`,
    "",
    "Commands:",
  ];
  const top = Object.keys(SPECS).filter((path) => !path.includes(" "));
  const ordered = ROOT_ORDER.filter((name) => top.includes(name));
  ordered.push(...top.filter((name) => !ROOT_ORDER.includes(name)).sort());
  for (const name of ordered) lines.push("  " + name.padEnd(12) + SPECS[name].summary);
  lines.push("", "Global flags:");
  for (const item of globalFlags()) lines.push(flagLine(item));
  lines.push(
    "",
    "Examples:",
    `  ${TOOL} auth login --token $` + ENV + "_TOKEN",
    `  ${TOOL} project list --limit 5 --json`,
    `  ${TOOL} project get prj_001`,
    "",
    "Exit codes:",
    "  " + EXIT_LINE,
    "",
    "Docs: " + DOCS_URL,
  );
  const target = targetLine();
  if (target) {
    lines.splice(4, 0, target, "");
  }
  return lines.join("\n");
}

export function commandHelp(spec: Spec): string {
  const lines = [spec.description || spec.summary, ""];
  if (spec.group) {
    lines.push("Usage:", `  ${TOOL} ${spec.path.join(" ")} <command> [flags]`, "", "Commands:");
    for (const child of childLines(spec)) lines.push(child);
    return lines.join("\n");
  }
  const tail = (spec.arguments || []).map((argument) =>
    argument.required === false ? `[${argument.name}]` : `<${argument.name}>`,
  );
  tail.push("[flags]");
  lines.push("Usage:", `  ${TOOL} ${spec.path.join(" ")} ${tail.join(" ")}`, "");
  if (spec.arguments && spec.arguments.length) {
    lines.push("Arguments:");
    for (const argument of spec.arguments) {
      lines.push("  " + argument.name.padEnd(14) + (argument.description || ""));
    }
    lines.push("");
  }
  lines.push("Flags:");
  for (const item of [...(spec.flags || []), ...globalFlags()]) lines.push(flagLine(item));
  lines.push("", "Examples:");
  for (const example of spec.examples || []) lines.push("  " + example);
  if (spec.related && spec.related.length) {
    lines.push("", "Related:");
    for (const item of spec.related) lines.push("  " + item);
  }
  return lines.join("\n");
}

function childLines(spec: Spec): string[] {
  const prefix = spec.path.join(" ") + " ";
  const lines: string[] = [];
  for (const path of Object.keys(SPECS).filter((item) => item.startsWith(prefix))) {
    const child = path.split(" ").slice(-1)[0];
    lines.push("  " + child.padEnd(12) + SPECS[path].summary);
  }
  return lines;
}

export function specByPath(path: string): Spec | null {
  return SPECS[path] || null;
}

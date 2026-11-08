import * as fs from "node:fs";

import { ALL_CAP, DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE } from "../../constants.ts";
import { CliError, UsageError } from "../../errors.ts";
import type { Api } from "../../api.ts";
import type { Column } from "../../output.ts";

export const SUMMARY_FIELDS = ["id", "name", "status", "owner", "created_at", "updated_at"];
export const FULL_FIELDS = [...SUMMARY_FIELDS, "description", "settings", "counts", "metadata"];

export const LIST_COLUMNS: Column[] = [
  ["id", "id", null],
  ["name", "name", 30],
  ["status", "status", 10],
  ["owner", "owner", 28],
  ["updated", "updated_at", 20],
];

export const GET_FIELDS: Array<[string, string]> = [
  ["id", "id"],
  ["name", "name"],
  ["status", "status"],
  ["owner", "owner"],
  ["description", "description"],
  ["created_at", "created_at"],
  ["updated_at", "updated_at"],
  ["settings", "settings"],
  ["counts", "counts"],
];

export function pathFor(projectId: string): string {
  return "/v1/projects/" + encodeURIComponent(String(projectId));
}

export async function resolveProject(api: Api, value: string): Promise<Record<string, any>> {
  try {
    return await api.get(pathFor(value));
  } catch (err) {
    if (!(err instanceof CliError) || err.code !== "not_found") throw err;
  }
  const page = await api.get("/v1/projects", [["name", value], ["limit", "2"]]);
  const matches = page.data || [];
  if (matches.length === 1) return api.get(pathFor(matches[0].id));
  if (matches.length > 1) {
    const candidates = matches.map((item: any) => ({ id: item.id, name: item.name }));
    throw new CliError(
      "ambiguous_target",
      `Multiple projects match "${value}"`,
      `Retry with a project ID, for example: acme project get ${matches[0].id}`,
      null, null, null, null, { candidates },
    );
  }
  throw new CliError("not_found", `Project ${value} not found`, "Run acme project list");
}

export function pageLimit(opts: Record<string, any>): number {
  const limit = Number(opts.limit);
  if (!Number.isInteger(limit)) {
    throw new UsageError("--limit must be an integer", `Pass a number from 1 to ${MAX_PAGE_SIZE}`);
  }
  if (limit < 1 || limit > MAX_PAGE_SIZE) {
    throw new UsageError(`--limit must be between 1 and ${MAX_PAGE_SIZE}`, `Default is ${DEFAULT_PAGE_SIZE}`);
  }
  return limit;
}

export function listQuery(opts: Record<string, any>, cursor: string | null = null): Array<[string, string | number | null]> {
  const query: Array<[string, string | number | null]> = [["limit", pageLimit(opts)]];
  const selected = cursor ?? opts.cursor;
  if (selected) query.push(["cursor", selected]);
  if (opts.sort) query.push(["sort", opts.sort]);
  for (const item of opts.filter || []) query.push(["filter", item]);
  for (const name of ["search", "status", "owner", "since", "until"]) {
    if (opts[name]) query.push([name, opts[name]]);
  }
  if (opts.full) query.push(["full", "1"]);
  return query;
}

export function requestedFields(opts: Record<string, any>): string[] | null {
  if (!opts.fields) return null;
  const allowed = opts.full ? FULL_FIELDS : SUMMARY_FIELDS;
  const fields = String(opts.fields).split(",").map((part) => part.trim()).filter(Boolean);
  const unknown = fields.filter((field) => !allowed.includes(field));
  if (unknown.length) {
    const extra = opts.full ? "" : ` (use --full for ${FULL_FIELDS.slice(SUMMARY_FIELDS.length).join(", ")})`;
    throw new UsageError(`unknown field '${unknown[0]}'`, "Allowed now: " + allowed.join(", ") + extra);
  }
  return fields;
}

export function shape(item: Record<string, any>, full = false, fields: string[] | null = null): Record<string, any> {
  let source = full ? { ...item } : Object.fromEntries(
    Object.entries(item).filter(([key]) => SUMMARY_FIELDS.includes(key)),
  );
  if (fields) {
    const picked: Record<string, any> = {};
    for (const field of fields) picked[field] = source[field] ?? null;
    source = picked;
  }
  return source;
}

export async function fetchAll(
  api: Api,
  opts: Record<string, any>,
): Promise<{ items: Array<Record<string, any>>; hasMore: boolean; nextCursor: string | null; truncated: boolean }> {
  const items: Array<Record<string, any>> = [];
  let cursor: string | null = opts.cursor ?? null;
  let hasMore = false;
  let truncated = false;
  for (;;) {
    const page = await api.get("/v1/projects", listQuery(opts, cursor));
    const batch = page.data || [];
    const room = ALL_CAP - items.length;
    items.push(...batch.slice(0, room));
    hasMore = Boolean(page.has_more);
    cursor = page.next_cursor ?? null;
    if (items.length >= ALL_CAP && (hasMore || opts.all)) {
      truncated = true;
      break;
    }
    if (!opts.all || !hasMore || !cursor) break;
  }
  return { items, hasMore, nextCursor: cursor, truncated };
}

export function bodyFlags(opts: Record<string, any>): Record<string, any> {
  let body: Record<string, any> = {};
  if (opts.data) {
    try {
      body = JSON.parse(opts.data);
    } catch (err) {
      throw new UsageError(`--data is not valid JSON: ${(err as Error).message}`, "Pass a JSON object");
    }
    if (!body || typeof body !== "object" || Array.isArray(body)) {
      throw new UsageError("--data must be a JSON object");
    }
  }
  if (opts.file) {
    if (opts.data) process.stderr.write("warning: --file wins over --data\n");
    let raw: string;
    try {
      raw = opts.file === "-" ? fs.readFileSync(0, "utf8") : fs.readFileSync(opts.file, "utf8");
    } catch (err) {
      throw new UsageError(`cannot read --file ${opts.file}: ${(err as Error).message}`);
    }
    try {
      body = JSON.parse(raw);
    } catch (err) {
      throw new UsageError(`--file is not valid JSON: ${(err as Error).message}`);
    }
    if (!body || typeof body !== "object" || Array.isArray(body)) {
      throw new UsageError("--file must contain a JSON object");
    }
  }
  return body;
}

export function coerce(value: string): string | number | boolean | null {
  if (value === "true") return true;
  if (value === "false") return false;
  if (value === "null") return null;
  if (/^-?\d+$/.test(value)) return Number(value);
  const numeric = Number(value);
  if (value !== "" && Number.isFinite(numeric) && /^-?\d*\.\d+$/.test(value)) return numeric;
  return value;
}

export function nestedSet(target: Record<string, any>, dotted: string, value: unknown): void {
  const parts = dotted.split(".");
  let cursor = target;
  for (const part of parts.slice(0, -1)) {
    if (!cursor[part] || typeof cursor[part] !== "object") cursor[part] = {};
    cursor = cursor[part];
  }
  cursor[parts[parts.length - 1]] = value;
}

export function patchFromFlags(opts: Record<string, any>): Record<string, any> {
  const patch = bodyFlags(opts);
  for (const item of opts.set || []) {
    if (!item.includes("=")) {
      throw new UsageError(`--set expects key=value, got '${item}'`, "Example: --set status=active");
    }
    const equals = item.indexOf("=");
    nestedSet(patch, item.slice(0, equals).trim(), coerce(item.slice(equals + 1)));
  }
  for (const item of opts.unset || []) nestedSet(patch, String(item).trim(), null);
  return patch;
}

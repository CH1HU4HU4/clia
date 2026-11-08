import { targetDict } from "./errors.ts";

const MAX_TABLE_WIDTH = 120;

export type Column = [string, string, number | null];

export function printJson(payload: unknown): void {
  process.stdout.write(JSON.stringify(payload) + "\n");
}

export function printText(text: string, stream: { write(text: string): unknown } = process.stdout): void {
  stream.write(text + "\n");
}

function cell(value: unknown, cap: number | null): string {
  if (value === null || value === undefined) return "-";
  const text = String(value);
  if (cap && text.length > cap) return text.slice(0, Math.max(1, cap - 1)) + "\u2026";
  return text;
}

export function renderTable(columns: Column[], rows: Array<Record<string, any>>): string {
  const widths: number[] = [];
  for (const [header, columnKey, cap] of columns) {
    let width = header.length;
    for (const row of rows) {
      const value = row[columnKey] === null || row[columnKey] === undefined ? "" : String(row[columnKey]);
      width = Math.max(width, Math.min(value.length, cap ?? 10 ** 9));
    }
    widths.push(width);
  }
  const total = widths.reduce((sum, width) => sum + width, 0) + 3 * (columns.length - 1);
  if (total > MAX_TABLE_WIDTH) {
    let excess = total - MAX_TABLE_WIDTH;
    columns.forEach(([_header, _columnKey, cap], index) => {
      if (cap && excess > 0) {
        const squeeze = Math.min(excess, Math.max(0, widths[index] - columns[index][0].length));
        widths[index] -= squeeze;
        excess -= squeeze;
      }
    });
  }
  const headerLine = columns
    .map(([header], index) => header.toUpperCase().padEnd(widths[index]))
    .join("   ")
    .trimEnd();
  const lines = [headerLine];
  for (const row of rows) {
    const cells = columns.map(([_header, columnKey, cap], index) => {
      let text = cell(row[columnKey], cap);
      if (text.length > widths[index]) text = text.slice(0, Math.max(1, widths[index] - 1)) + "\u2026";
      return text.padEnd(widths[index]);
    });
    lines.push(cells.join("   ").trimEnd());
  }
  return lines.join("\n");
}

export function listEnvelope(
  items: unknown[],
  hasMore: boolean,
  nextCursor: string | null,
  truncated: boolean,
): Record<string, unknown> {
  return { data: items, has_more: Boolean(hasMore), next_cursor: nextCursor, truncated: Boolean(truncated) };
}

export function emitList(
  items: Array<Record<string, any>>,
  ctx: any,
  opts: Record<string, any>,
  columns: Column[],
  label: string,
  options: {
    idKey?: string;
    hasMore?: boolean;
    nextCursor?: string | null;
    truncated?: boolean;
    emptyMessage?: string;
  } = {},
): void {
  const idKey = options.idKey || "id";
  if (ctx.output === "json") {
    printJson(listEnvelope(items, Boolean(options.hasMore), options.nextCursor ?? null, Boolean(options.truncated)));
    return;
  }
  if (ctx.output === "quiet") {
    for (const item of items) {
      if (item[idKey] !== undefined && item[idKey] !== null) printText(String(item[idKey]));
    }
    return;
  }
  if (!items.length) {
    printText(options.emptyMessage || `No ${label} found.`, process.stderr);
    return;
  }
  printText(renderTable(columns, items));
  if (options.truncated) {
    const hint = options.nextCursor ? ` Next: --cursor ${options.nextCursor}` : "";
    printText(`warning: stopped at the 10,000 item cap; results are truncated.${hint}`, process.stderr);
  } else if (options.hasMore && options.nextCursor) {
    printText(`Showing ${items.length}. Next: --cursor ${options.nextCursor}`, process.stderr);
  }
}

export function emitObject(
  object: Record<string, any>,
  ctx: any,
  opts: Record<string, any>,
  fields: Array<[string, string]> = [],
): void {
  if (ctx.output === "json") {
    printJson(object);
    return;
  }
  if (ctx.output === "quiet") {
    if (object.id !== undefined && object.id !== null) printText(String(object.id));
    return;
  }
  for (const [fieldKey, label] of fields) {
    let value = object[fieldKey];
    if (value === null || value === undefined) value = "-";
    else if (typeof value === "object") value = JSON.stringify(value);
    printText(`${label}: ${value}`);
  }
}

export function emitAction(payload: Record<string, any>, ctx: any, message: string): void {
  if (ctx.output === "json") {
    printJson(payload);
    return;
  }
  printText(message);
}

export function emitDryRun(preview: Record<string, any>, ctx: any, opts: Record<string, any>): void {
  const payload = { ...preview };
  const target = targetDict(ctx);
  if (target) payload.target = target;
  if (ctx.output === "json") {
    printJson(payload);
    return;
  }
  printText("Dry run: no request sent", process.stderr);
  printText(`${payload.method} ${payload.url}`, process.stderr);
  if (payload.headers) printText("headers: " + JSON.stringify(payload.headers), process.stderr);
  if (payload.body !== null && payload.body !== undefined) {
    printText("body: " + JSON.stringify(payload.body), process.stderr);
  }
  if (target) {
    printText(
      `target: profile ${target.profile}, ${target.base_url}, org ${target.org}, project ${target.project}, API ${target.api_version}`,
      process.stderr,
    );
  }
}

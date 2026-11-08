import { Api } from "../../api.ts";
import { flag, type Spec } from "../../args.ts";
import { emitDryRun, emitList } from "../../output.ts";
import * as common from "./common.ts";

export const SPEC: Spec = {
  path: ["project", "list"],
  summary: "List projects",
  description: "List projects in the current org. Returns summary fields; use --full for full objects.",
  arguments: [],
  flags: [
    flag("--limit", "value", "Results per page", "<n>", "50"),
    flag("--cursor", "value", "Continue after this cursor", "<cursor>"),
    flag("--all", "bool", "Fetch every page (cap: 10,000)"),
    flag("--sort", "value", "Sort field; prefix - for descending", "<field>"),
    flag("--filter", "value", "Exact match filter", "<key=value>", null, null, null, true),
    flag("--search", "value", "Server-side text search", "<text>"),
    flag("--status", "value", "Filter by status: active, paused, archived", "<status>"),
    flag("--owner", "value", "Filter by owner email", "<email>"),
    flag("--since", "value", "Created at or after (RFC 3339 or 24h)", "<time>"),
    flag("--until", "value", "Created at or before (RFC 3339 or 24h)", "<time>"),
    flag("--fields", "value", "Project top-level keys", "<id,name,status>"),
    flag("--full", "bool", "Return full objects instead of summaries"),
  ],
  examples: [
    "acme project list --limit 5",
    "acme project list --status active --sort -created_at --json",
    "acme project list --all --fields id,name",
  ],
  related: ["acme project get <id>", "acme project create --name web"],
  data: true,
  run(ctx, opts) {
    return run(ctx, opts);
  },
};

export async function run(ctx: any, opts: Record<string, any>): Promise<number> {
  const api = new Api(ctx);
  const query = common.listQuery(opts);
  if (opts.dry_run) {
    emitDryRun(api.preview("GET", "/v1/projects", query), ctx, opts);
    return 0;
  }
  const fields = common.requestedFields(opts);
  const { items, hasMore, nextCursor, truncated } = await common.fetchAll(api, opts);
  const shaped = items.map((item) => common.shape(item, Boolean(opts.full), fields));
  emitList(shaped, ctx, opts, common.LIST_COLUMNS, "projects", {
    hasMore, nextCursor, truncated,
  });
  return 0;
}

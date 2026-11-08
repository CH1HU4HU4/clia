import * as config from "../../config.ts";
import { type Spec } from "../../args.ts";
import type { Column } from "../../output.ts";
import { emitList } from "../../output.ts";
import * as common from "./common.ts";

export const SPEC: Spec = {
  path: ["config", "list"],
  summary: "List config values",
  description: "List every known key in the selected profile with its source. Secrets are masked.",
  arguments: [],
  flags: [],
  examples: ["acme config list", "acme config list --json"],
  related: ["acme config get <key>", "acme auth status"],
  data: true,
  run(ctx, opts) {
    return run(ctx, opts);
  },
};

const COLUMNS: Column[] = [["key", "key", 22], ["value", "value", 50], ["source", "source", 10]];

export function run(ctx: any, opts: Record<string, any>): number {
  const values = config.profileValues(ctx.configData, ctx.profile) || {};
  const rows = common.KEYS.map((key) => {
    let value: unknown;
    if (key === "profile") value = ctx.profile;
    else if (key === "access_token" && ctx.token) value = ctx.token;
    else value = values[key];
    return { key, value: common.display(key, value), source: common.source(ctx.profile, key) };
  });
  emitList(rows, ctx, opts, COLUMNS, "config keys", {
    hasMore: false, nextCursor: null, truncated: false, emptyMessage: "No config values.",
  });
  return 0;
}

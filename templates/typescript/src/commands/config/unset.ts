import * as config from "../../config.ts";
import { type Spec } from "../../args.ts";
import { emitObject } from "../../output.ts";
import * as common from "./common.ts";

export const SPEC: Spec = {
  path: ["config", "unset"],
  summary: "Remove a config value",
  description: "Remove one key from the selected profile and fall back to the default.",
  arguments: [{ name: "key", description: "Config key" }],
  flags: [],
  examples: ["acme config unset project", "acme config unset access-token --json"],
  related: ["acme config list", "acme config get <key>"],
  data: true,
  run(ctx, opts, positionals) {
    return run(ctx, opts, positionals);
  },
};

const FIELDS: Array<[string, string]> = [["ok", "ok"], ["key", "key"], ["profile", "profile"]];

export function run(ctx: any, opts: Record<string, any>, positionals: string[]): number {
  const key = common.validateKey(positionals[0]);
  config.unsetValue(ctx.profile, key);
  emitObject({ ok: true, key, profile: ctx.profile }, ctx, opts, FIELDS);
  return 0;
}

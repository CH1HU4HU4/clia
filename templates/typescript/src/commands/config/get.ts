import * as config from "../../config.ts";
import { type Spec } from "../../args.ts";
import { emitObject } from "../../output.ts";
import * as common from "./common.ts";

export const SPEC: Spec = {
  path: ["config", "get"],
  summary: "Read a config value",
  description: "Print one resolved config value and its source (flag, env, file, default).",
  arguments: [{ name: "key", description: "Config key" }],
  flags: [],
  examples: ["acme config get base-url", "acme config get output --json"],
  related: ["acme config list", "acme config set <key> <value>"],
  data: true,
  run(ctx, opts, positionals) {
    return run(ctx, opts, positionals);
  },
};

const FIELDS: Array<[string, string]> = [
  ["key", "key"], ["value", "value"], ["source", "source"], ["profile", "profile"],
];

export function run(ctx: any, opts: Record<string, any>, positionals: string[]): number {
  const key = common.validateKey(positionals[0]);
  let value: unknown;
  if (key === "profile") value = ctx.profile;
  else if (key === "access_token" && ctx.token) value = ctx.token;
  else value = (config.profileValues(ctx.configData, ctx.profile) || {})[key];
  emitObject({
    key,
    value: common.display(key, value),
    source: common.source(ctx.profile, key),
    profile: ctx.profile,
  }, ctx, opts, FIELDS);
  return 0;
}

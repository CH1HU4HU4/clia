import * as config from "../../config.ts";
import { type Spec } from "../../args.ts";
import { emitObject } from "../../output.ts";
import * as common from "./common.ts";

export const SPEC: Spec = {
  path: ["config", "set"],
  summary: "Write a config value",
  description: "Write one value to the user config (0600). Creates the profile section if needed.",
  arguments: [
    { name: "key", description: "Config key" },
    { name: "value", description: "New value" },
  ],
  flags: [],
  examples: [
    "acme config set base-url https://api.acme.com",
    "acme config set output json --profile ci",
  ],
  related: ["acme config get <key>", "acme config unset <key>"],
  data: true,
  run(ctx, opts, positionals) {
    return run(ctx, opts, positionals);
  },
};

const FIELDS: Array<[string, string]> = [["key", "key"], ["profile", "profile"], ["ok", "ok"]];

export function run(ctx: any, opts: Record<string, any>, positionals: string[]): number {
  const key = common.validateKey(positionals[0]);
  const value = common.validateValue(key, positionals[1]);
  config.setValue(ctx.profile, key, value, true);
  emitObject({ ok: true, key, profile: ctx.profile }, ctx, opts, FIELDS);
  return 0;
}

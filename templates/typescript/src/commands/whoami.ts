import { Api } from "../api.ts";
import { type Spec } from "../args.ts";
import { emitObject } from "../output.ts";

export const SPEC: Spec = {
  path: ["whoami"],
  summary: "Show the current user and target",
  description: "Show the user, org, profile, environment, and token expiry for the selected target.",
  arguments: [],
  flags: [],
  examples: ["acme whoami", "acme whoami --json"],
  related: ["acme auth status", "acme project list"],
  data: true,
  run(ctx, opts) {
    return run(ctx, opts);
  },
};

const FIELDS: Array<[string, string]> = [
  ["user", "user"],
  ["org", "org"],
  ["profile", "profile"],
  ["environment", "environment"],
  ["token_expires_at", "token_expires_at"],
  ["base_url", "base_url"],
  ["api_version", "api_version"],
];

export async function run(ctx: any, opts: Record<string, any>): Promise<number> {
  const api = new Api(ctx);
  const me = await api.me();
  emitObject({
    user: me.user?.email ?? null,
    user_id: me.user?.id ?? null,
    org: me.org || ctx.org,
    profile: ctx.profile,
    environment: me.environment ?? null,
    token_expires_at: ctx.expiresAt || me.token_expires_at,
    base_url: ctx.baseUrl,
    api_version: ctx.apiVersion,
  }, ctx, opts, FIELDS);
  return 0;
}

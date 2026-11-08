import { Api } from "../../api.ts";
import { type Spec } from "../../args.ts";
import { emitObject } from "../../output.ts";

export const SPEC: Spec = {
  path: ["auth", "status"],
  summary: "Show authentication status",
  description: "Show whether the selected profile is authenticated and which target it uses.",
  arguments: [],
  flags: [],
  examples: ["acme auth status", "acme auth status --json"],
  related: ["acme whoami", "acme auth login"],
  data: true,
  run(ctx, opts) {
    return run(ctx, opts);
  },
};

const FIELDS: Array<[string, string]> = [
  ["authenticated", "authenticated"],
  ["profile", "profile"],
  ["base_url", "base_url"],
  ["org", "org"],
  ["project", "project"],
  ["api_version", "api_version"],
  ["environment", "environment"],
  ["user", "user"],
  ["expires_at", "expires_at"],
];

export async function run(ctx: any, opts: Record<string, any>): Promise<number> {
  if (!ctx.token) {
    emitObject({
      authenticated: false,
      profile: ctx.profile,
      base_url: ctx.baseUrl,
      org: ctx.org || null,
      project: ctx.project || null,
      api_version: ctx.apiVersion,
      environment: null,
      user: null,
      expires_at: null,
    }, ctx, opts, FIELDS);
    return 0;
  }
  const api = new Api(ctx);
  const me = await api.me();
  emitObject({
    authenticated: true,
    profile: ctx.profile,
    base_url: ctx.baseUrl,
    org: me.org || ctx.org,
    project: ctx.project || null,
    api_version: ctx.apiVersion,
    environment: me.environment ?? null,
    user: me.user?.email ?? null,
    expires_at: ctx.expiresAt || me.token_expires_at,
  }, ctx, opts, FIELDS);
  return 0;
}

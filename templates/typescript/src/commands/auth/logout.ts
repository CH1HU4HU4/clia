import * as config from "../../config.ts";
import { type Spec } from "../../args.ts";
import { printJson, printText } from "../../output.ts";

export const SPEC: Spec = {
  path: ["auth", "logout"],
  summary: "Log out",
  description: "Remove the stored access and refresh tokens for the selected profile.",
  arguments: [],
  flags: [],
  examples: ["acme auth logout", "acme auth logout --json"],
  related: ["acme auth login", "acme auth status"],
  data: true,
  run(ctx) {
    return run(ctx);
  },
};

export function run(ctx: any): number {
  for (const key of ["access_token", "refresh_token", "expires_at"]) {
    try {
      config.unsetValue(ctx.profile, key);
    } catch {
      // Profile may have no stored credential.
    }
  }
  const payload = { ok: true, logged_out: true, profile: ctx.profile };
  if (ctx.output === "json") printJson(payload);
  else printText(`Logged out of profile ${ctx.profile}.`);
  return 0;
}

import { createInterface } from "node:readline/promises";
import { stdin, stderr } from "node:process";

import { Api } from "../../api.ts";
import { flag, type Spec } from "../../args.ts";
import * as config from "../../config.ts";
import { CliError, UsageError } from "../../errors.ts";
import { printJson, printText } from "../../output.ts";

export const SPEC: Spec = {
  path: ["auth", "login"],
  summary: "Log in",
  description: "Store an API token, or run the device flow. Off a TTY, pass --token or --device.",
  arguments: [],
  flags: [flag("--device", "bool", "Use the OAuth device flow (never prompts)")],
  examples: ["acme auth login --token $ACME_TOKEN", "acme auth login --device"],
  related: ["acme auth status", "acme whoami"],
  data: true,
  run(ctx, opts) {
    return run(ctx, opts);
  },
};

function save(ctx: any, accessToken: string, refreshToken: string | null = null, expiresAt: string | null = null): void {
  config.setValue(ctx.profile, "access_token", accessToken, false);
  if (refreshToken) config.setValue(ctx.profile, "refresh_token", refreshToken, false);
  else config.unsetValue(ctx.profile, "refresh_token");
  if (expiresAt) config.setValue(ctx.profile, "expires_at", expiresAt, false);
  else config.unsetValue(ctx.profile, "expires_at");
}

async function deviceLogin(api: Api): Promise<Record<string, any>> {
  const device = await api.publicPost("/v1/auth/device", { client: "acme-cli" });
  stderr.write(`Open ${device.verification_uri || ""} and enter code ${device.user_code || ""}\n`);
  const interval = Math.max(1, Number(device.interval || 1));
  const deadline = Date.now() + 120_000;
  while (Date.now() < deadline) {
    try {
      return await api.publicPost("/v1/auth/token", { device_code: device.device_code });
    } catch (err) {
      if (err instanceof CliError && err.status === 428) {
        await new Promise((resolve) => setTimeout(resolve, interval * 1000));
        continue;
      }
      throw err;
    }
  }
  throw new CliError("auth_required", "Device login timed out", "Run acme auth login --device again");
}

export async function run(ctx: any, opts: Record<string, any>): Promise<number> {
  const api = new Api(ctx);
  if (opts.device) {
    const token = await deviceLogin(api);
    ctx.token = token.access_token;
    ctx.refreshToken = token.refresh_token || null;
    ctx.expiresAt = token.expires_at || null;
    save(ctx, token.access_token, token.refresh_token || null, token.expires_at || null);
  } else {
    let token = opts.token;
    if (!token) {
      if (!stdin.isTTY) {
        throw new UsageError("no token provided", "Pass --token, set ACME_TOKEN, or use --device");
      }
      const readline = createInterface({ input: stdin, output: stderr });
      token = (await readline.question("Paste API token: ")).trim();
      readline.close();
    }
    if (!token) throw new UsageError("no token provided", "Pass --token or set ACME_TOKEN");
    ctx.token = token;
    ctx.expiresAt = null;
    ctx.refreshToken = null;
    save(ctx, token);
  }

  const me = await api.me();
  const payload = {
    ok: true,
    authenticated: true,
    user: me.user?.email ?? null,
    org: me.org || ctx.org,
    profile: ctx.profile,
    token: null,
  };
  if (ctx.output === "json") printJson(payload);
  else printText(`Logged in as ${payload.user} (org ${payload.org}, profile ${ctx.profile})`);
  return 0;
}

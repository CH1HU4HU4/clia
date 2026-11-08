import { randomUUID } from "node:crypto";

import { Api } from "../../api.ts";
import { flag, type Spec } from "../../args.ts";
import { UsageError } from "../../errors.ts";
import { emitDryRun, emitObject } from "../../output.ts";
import * as common from "./common.ts";

export const SPEC: Spec = {
  path: ["project", "create"],
  summary: "Create a project",
  description: "Create a project. Sends an Idempotency-Key so retries never duplicate it.",
  arguments: [],
  flags: [
    flag("--name", "value", "Project name (required)", "<name>"),
    flag("--description", "value", "Project description", "<text>"),
    flag("--file", "value", "JSON body file, or - for stdin", "<path>"),
    flag("--data", "value", "Inline JSON body", "<json>"),
    flag("--idempotency-key", "value", "Reuse an external idempotency key", "<key>"),
  ],
  examples: [
    "acme project create --name web",
    'acme project create --name web --description "Customer-facing app" --json',
    "acme project create --file project.json --dry-run",
  ],
  related: ["acme project list", "acme project delete <id> --yes"],
  data: true,
  run(ctx, opts) {
    return run(ctx, opts);
  },
};

export async function run(ctx: any, opts: Record<string, any>): Promise<number> {
  const api = new Api(ctx);
  const body = common.bodyFlags(opts);
  if (opts.name) body.name = opts.name;
  if (opts.description) body.description = opts.description;
  if (!body.name) {
    throw new UsageError('missing required flag "--name"', 'Pass --name "web" or --file project.json');
  }
  const key = opts.idempotency_key || randomUUID();
  if (opts.dry_run) {
    emitDryRun(api.preview("POST", "/v1/projects", [], body, key), ctx, opts);
    return 0;
  }
  const project = await api.post("/v1/projects", body, key);
  emitObject(common.shape(project, true), ctx, opts, common.GET_FIELDS);
  return 0;
}

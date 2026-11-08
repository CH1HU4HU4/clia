import { Api } from "../../api.ts";
import { flag, type Spec } from "../../args.ts";
import { emitDryRun, emitObject } from "../../output.ts";
import * as common from "./common.ts";

export const SPEC: Spec = {
  path: ["project", "get"],
  summary: "Get one project",
  description: "Get one project by ID or unique name. Name ambiguity exits 11 with candidates.",
  arguments: [{ name: "project", description: "Project ID or name" }],
  flags: [flag("--fields", "value", "Project top-level keys", "<id,name,status>")],
  examples: ["acme project get prj_001", "acme project get web --json"],
  related: ["acme project list", "acme project update <id> --set status=paused"],
  data: true,
  run(ctx, opts, positionals) {
    return run(ctx, opts, positionals);
  },
};

export async function run(ctx: any, opts: Record<string, any>, positionals: string[]): Promise<number> {
  const api = new Api(ctx);
  const value = positionals[0];
  if (opts.dry_run) {
    emitDryRun(api.preview("GET", common.pathFor(value)), ctx, opts);
    return 0;
  }
  const fields = common.requestedFields(opts);
  const project = await common.resolveProject(api, value);
  emitObject(common.shape(project, true, fields), ctx, opts, common.GET_FIELDS);
  return 0;
}

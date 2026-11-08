import { Api } from "../../api.ts";
import { flag, type Spec } from "../../args.ts";
import { UsageError } from "../../errors.ts";
import { emitDryRun, emitObject } from "../../output.ts";
import * as common from "./common.ts";

export const SPEC: Spec = {
  path: ["project", "update"],
  summary: "Update a project",
  description: "Update only the fields you pass. Use --set key=value and --unset key.",
  arguments: [{ name: "project", description: "Project ID or name" }],
  flags: [
    flag("--set", "value", "Set a field (repeatable, dotted keys allowed)", "<key=value>", null, null, null, true),
    flag("--unset", "value", "Clear a field", "<key>", null, null, null, true),
    flag("--file", "value", "JSON patch file, or - for stdin", "<path>"),
    flag("--data", "value", "Inline JSON patch", "<json>"),
  ],
  examples: [
    "acme project update prj_001 --set status=paused",
    'acme project update web --set description="New copy" --unset settings.region --json',
  ],
  related: ["acme project get <id>", "acme project delete <id> --yes"],
  data: true,
  run(ctx, opts, positionals) {
    return run(ctx, opts, positionals);
  },
};

export async function run(ctx: any, opts: Record<string, any>, positionals: string[]): Promise<number> {
  const api = new Api(ctx);
  const patch = common.patchFromFlags(opts);
  if (!Object.keys(patch).length) {
    throw new UsageError("nothing to update", "Pass --set key=value or --unset key");
  }
  const project = await common.resolveProject(api, positionals[0]);
  if (opts.dry_run) {
    emitDryRun(api.preview("PATCH", common.pathFor(project.id), [], patch), ctx, opts);
    return 0;
  }
  const updated = await api.patch(common.pathFor(project.id), patch);
  emitObject(common.shape(updated, true), ctx, opts, common.GET_FIELDS);
  return 0;
}

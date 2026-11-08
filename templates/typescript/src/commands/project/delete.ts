import { createInterface } from "node:readline/promises";
import { stdin, stderr } from "node:process";

import { Api } from "../../api.ts";
import { type Spec } from "../../args.ts";
import { CliError } from "../../errors.ts";
import { emitAction, emitDryRun } from "../../output.ts";
import * as common from "./common.ts";

export const SPEC: Spec = {
  path: ["project", "delete"],
  summary: "Delete a project",
  description: "Delete a project and everything it owns. Destructive: needs --yes off a TTY.",
  arguments: [{ name: "project", description: "Project ID or name" }],
  flags: [],
  examples: ["acme project delete prj_001 --yes", "acme project delete web --dry-run --json"],
  related: ["acme project list", "acme project get <id>"],
  data: true,
  destructive: true,
  run(ctx, opts, positionals) {
    return run(ctx, opts, positionals);
  },
};

async function confirm(ctx: any, project: Record<string, any>, opts: Record<string, any>): Promise<void> {
  if (ctx.output !== "table" || opts.no_input || !process.stdin.isTTY) {
    throw new CliError(
      "confirmation_required",
      `Refusing to delete project "${project.name}" (${project.id}) without --yes`,
      `Re-run with --yes to delete project ${project.id}`,
    );
  }
  stderr.write(`About to delete project "${project.name}" (${project.id})\n`);
  stderr.write(
    `target: profile ${ctx.profile}, ${ctx.baseUrl}, org ${ctx.org}, project ${ctx.project}, API ${ctx.apiVersion}\n`,
  );
  const readline = createInterface({ input: stdin, output: stderr });
  const answer = (await readline.question("Continue? [y/N] ")).trim().toLowerCase();
  readline.close();
  if (answer !== "y" && answer !== "yes") {
    throw new CliError("confirmation_required", "Deletion cancelled", "No changes were made");
  }
}

export async function run(ctx: any, opts: Record<string, any>, positionals: string[]): Promise<number> {
  const api = new Api(ctx);
  const project = await common.resolveProject(api, positionals[0]);
  if (opts.dry_run) {
    emitDryRun(api.preview("DELETE", common.pathFor(project.id)), ctx, opts);
    return 0;
  }
  if (!opts.yes) await confirm(ctx, project, opts);
  const result = await api.delete(common.pathFor(project.id));
  emitAction(result, ctx, `Deleted project ${project.id}.`);
  return 0;
}

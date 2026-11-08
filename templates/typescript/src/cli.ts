import { parse } from "./args.ts";
import { allSpecs } from "./commands/index.ts";
import { TOOL, ENV, VERSION } from "./constants.ts";
import { resolveContext } from "./context.ts";
import { CliError, UsageError, emitError } from "./errors.ts";
import { commandHelp, haveSpecs, rootHelp } from "./help.ts";
import { printText } from "./output.ts";
import { redactText } from "./redact.ts";

const NO_CONTEXT = new Set(["help", "version", "completion", "schema"]);

function jsonRequested(argv: string[], opts: Record<string, any>, ctx: any): boolean {
  if (opts.json) return true;
  if (ctx && ctx.output === "json") return true;
  if (process.env[ENV + "_OUTPUT"] === "json") return true;
  return argv.includes("--json");
}

export async function main(argv: string[]): Promise<number> {
  const specs = allSpecs();
  haveSpecs(specs);
  let ctx: any = null;
  let opts: Record<string, any> = {};
  try {
    const parsed = parse(argv, specs);
    const spec = parsed.spec;
    opts = parsed.opts;
    if (!spec) {
      if (opts.version) {
        printText(VERSION);
        return 0;
      }
      printText(rootHelp());
      return 0;
    }
    if (opts.help) {
      printText(commandHelp(spec));
      return 0;
    }
    if (opts.version) throw new UsageError("--version is a root flag", `Run: ${TOOL} --version`);

    const path = spec.path.join(" ");
    if (NO_CONTEXT.has(path)) {
      return (await spec.run!(null, opts, parsed.positionals)) || 0;
    }
    ctx = resolveContext(opts, path === "config set");
    return (await spec.run!(ctx, opts, parsed.positionals)) || 0;
  } catch (err) {
    if (err instanceof CliError) {
      const secrets = [ctx?.token, ctx?.refreshToken];
      err.message = redactText(err.message, secrets);
      if (err.hint) err.hint = redactText(err.hint, secrets);
      emitError(err, ctx, jsonRequested(argv, opts, ctx));
      return err.exit;
    }
    if (opts.debug) console.error(err);
    const message = redactText(String((err as Error)?.message ?? err), [ctx?.token, ctx?.refreshToken]);
    const wrapped = new CliError("unexpected", "Internal error: " + message, "Run with --debug for a traceback");
    emitError(wrapped, ctx, jsonRequested(argv, opts, ctx));
    return 1;
  }
}

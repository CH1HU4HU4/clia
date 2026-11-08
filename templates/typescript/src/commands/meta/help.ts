import { type Spec } from "../../args.ts";
import { UsageError } from "../../errors.ts";
import { commandHelp, haveSpecs, rootHelp, specByPath } from "../../help.ts";
import { printText } from "../../output.ts";
import { allSpecs } from "../index.ts";

export const SPEC: Spec = {
  path: ["help"],
  summary: "Show help",
  description: "Show root help or help for one command.",
  arguments: [
    { name: "command", description: "Command path", required: false },
    { name: "subcommand", description: "Subcommand", required: false },
  ],
  flags: [],
  examples: ["acme help", "acme help project list"],
  data: false,
  run(_ctx, _opts, positionals) {
    return run(positionals);
  },
};

export function run(positionals: string[]): number {
  const specs = allSpecs();
  haveSpecs(specs);
  if (!positionals.length) {
    printText(rootHelp());
    return 0;
  }
  const spec = specByPath(positionals.join(" "));
  if (!spec) throw new UsageError(`unknown command "${positionals.join(" ")}"`, "Run acme --help");
  printText(commandHelp(spec));
  return 0;
}

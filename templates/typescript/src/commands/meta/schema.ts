import { GLOBAL_FLAGS, type FlagDef, type Spec } from "../../args.ts";
import { TOOL, VERSION } from "../../constants.ts";
import { printJson } from "../../output.ts";
import { allSpecs } from "../index.ts";

export const SPEC: Spec = {
  path: ["schema"],
  summary: "Describe the command tree",
  description: "Print the command tree, arguments, flags, defaults, and examples as one JSON document.",
  arguments: [],
  flags: [],
  examples: ["acme schema", "acme schema | jq '.commands[].path'"],
  data: false,
  run() {
    return run();
  },
};

function flagPayload(item: FlagDef): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    name: item.long,
    type: item.kind,
    description: item.desc || "",
  };
  if (item.metavar) payload.metavar = item.metavar;
  if (item.default !== null && item.default !== undefined && item.default !== "") payload.default = item.default;
  if (item.env) payload.env = item.env;
  if (item.short) payload.short = item.short;
  return payload;
}

export function run(): number {
  const commands = Object.keys(allSpecs()).sort().map((path) => {
    const spec = allSpecs()[path];
    return {
      path: spec.path,
      summary: spec.summary,
      description: spec.description || "",
      arguments: spec.arguments || [],
      flags: (spec.flags || []).map(flagPayload),
      examples: spec.examples || [],
      data: spec.data !== false,
      destructive: Boolean(spec.destructive),
    };
  }).filter((item) => !allSpecs()[item.path.join(" ")].group);
  printJson({
    name: TOOL,
    version: VERSION,
    global_flags: GLOBAL_FLAGS.map(flagPayload),
    commands,
  });
  return 0;
}

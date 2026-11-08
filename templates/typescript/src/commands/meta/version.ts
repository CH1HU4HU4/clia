import { type Spec } from "../../args.ts";
import { VERSION } from "../../constants.ts";
import { printText } from "../../output.ts";

export const SPEC: Spec = {
  path: ["version"],
  summary: "Print the version",
  description: "Print the semantic version and nothing else.",
  arguments: [],
  flags: [],
  examples: ["acme version", "acme --version"],
  data: false,
  run() {
    printText(VERSION);
    return 0;
  },
};

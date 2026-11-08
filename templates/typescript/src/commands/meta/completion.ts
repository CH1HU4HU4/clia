import { GLOBAL_FLAGS, type Spec } from "../../args.ts";
import { TOOL } from "../../constants.ts";
import { UsageError } from "../../errors.ts";
import { printText } from "../../output.ts";
import { allSpecs } from "../index.ts";

export const SPEC: Spec = {
  path: ["completion"],
  summary: "Generate shell completions",
  description: "Print a completion script for bash, zsh, or fish.",
  arguments: [{ name: "shell", description: "bash, zsh, or fish" }],
  flags: [],
  examples: ["acme completion bash", "acme completion zsh > ~/.zsh/completions/_acme"],
  data: false,
  run(_ctx, _opts, positionals) {
    return run(positionals);
  },
};

function words(): string[] {
  return Object.keys(allSpecs())
    .filter((path) => !allSpecs()[path].group)
    .sort();
}

function flags(): string[] {
  const names = GLOBAL_FLAGS.map((item) => item.long);
  for (const spec of Object.values(allSpecs())) {
    for (const item of spec.flags || []) names.push(item.long);
  }
  return [...new Set(names)].sort();
}

export function run(positionals: string[]): number {
  const shell = positionals[0];
  const commandWords = words();
  const flagWords = flags();
  if (shell === "bash") {
    printText(
      `_${TOOL}_completions() {\n` +
      `  local cur="\${COMP_WORDS[COMP_CWORD]}"\n` +
      `  local words="${commandWords.join(" ")}"\n` +
      `  local flags="${flagWords.join(" ")}"\n` +
      `  COMPREPLY=( $(compgen -W "$words $flags" -- "$cur") )\n` +
      `}\n` +
      `complete -F _${TOOL}_completions ${TOOL}`,
    );
  } else if (shell === "zsh") {
    printText(
      `#compdef ${TOOL}\n` +
      `_${TOOL}() {\n` +
      `  local -a words\n` +
      `  words=(${commandWords.join(" ")})\n` +
      `  _describe 'command' words\n` +
      `}\n` +
      `_${TOOL}`,
    );
  } else if (shell === "fish") {
    const lines = [`# fish completions for ${TOOL}`];
    for (const word of commandWords) {
      const parts = word.split(" ");
      if (parts.length === 1) lines.push(`complete -c ${TOOL} -f -a ${parts[0]}`);
      else lines.push(`complete -c ${TOOL} -f -n '__fish_seen_subcommand_from ${parts[0]}' -a ${parts[1]}`);
    }
    printText(lines.join("\n"));
  } else {
    throw new UsageError(`unknown shell '${shell}'`, "Use bash, zsh, or fish");
  }
  return 0;
}

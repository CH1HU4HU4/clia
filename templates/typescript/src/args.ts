import { UsageError } from "./errors.ts";

export type FlagKind = "bool" | "value";

export type FlagDef = {
  long: string;
  kind: FlagKind;
  desc: string;
  metavar?: string | null;
  default?: string | null;
  env?: string | null;
  short?: string | null;
  repeat?: boolean;
};

export type Argument = { name: string; description: string; required?: boolean };

export type Spec = {
  path: string[];
  summary: string;
  description?: string;
  arguments: Argument[];
  flags: FlagDef[];
  examples: string[];
  related?: string[];
  data?: boolean;
  destructive?: boolean;
  group?: boolean;
  run?: (ctx: any, opts: Record<string, any>, positionals: string[]) => number | Promise<number>;
};

const TRUE_WORDS = ["1", "true", "yes", "on"];
const FALSE_WORDS = ["0", "false", "no", "off"];

export function flag(
  long: string,
  kind: FlagKind = "bool",
  desc = "",
  metavar: string | null = null,
  defaultValue: string | null = null,
  env: string | null = null,
  short: string | null = null,
  repeat = false,
): FlagDef {
  return { long, kind, desc, metavar, default: defaultValue, env, short, repeat };
}

export const GLOBAL_FLAGS: FlagDef[] = [
  flag("--json", "bool", "Print one JSON document on stdout"),
  flag("--quiet", "bool", "Print identifiers only"),
  flag("--no-color", "bool", "Disable ANSI color (also NO_COLOR)"),
  flag("--no-input", "bool", "Fail instead of prompting"),
  flag("--yes", "bool", "Confirm destructive actions without a prompt"),
  flag("--dry-run", "bool", "Print the request and send nothing"),
  flag("--debug", "bool", "Verbose logs to stderr, redacted"),
  flag("--timeout", "value", "Request timeout in seconds", "<seconds>", "30", "ACME_TIMEOUT"),
  flag("--profile", "value", "Config profile", "<name>", null, "ACME_PROFILE"),
  flag("--org", "value", "Override the org for this command", "<id>", null, "ACME_ORG"),
  flag("--project", "value", "Override the project for this command", "<id>", null, "ACME_PROJECT"),
  flag("--api-version", "value", "Override the pinned API version", "<version>", null, "ACME_API_VERSION"),
  flag("--base-url", "value", "Override the API base URL", "<url>", null, "ACME_BASE_URL"),
  flag("--allow-http", "bool", "Allow plain http for a non-loopback host"),
  flag("--token", "value", "API token (prefer ACME_TOKEN)", "<token>", null, "ACME_TOKEN"),
  flag("--help", "bool", "Show help", null, null, null, "-h"),
  flag("--version", "bool", "Print the version (root command only)"),
];

export function key(name: string): string {
  return name.replace(/^--?/, "").replace(/-/g, "_");
}

type Occurrence = { def: FlagDef | null; name: string; value: string | boolean | boolean };

function indexFlags(specs: Record<string, Spec>): {
  byLong: Record<string, FlagDef>;
  byShort: Record<string, FlagDef>;
} {
  const byLong: Record<string, FlagDef> = {};
  const byShort: Record<string, FlagDef> = {};
  const all: Array<FlagDef[] | null> = [GLOBAL_FLAGS];
  for (const spec of Object.values(specs)) all.push(spec.flags || []);
  for (const group of all) {
    for (const item of group || []) {
      if (!byLong[item.long]) byLong[item.long] = item;
      if (item.short && !byShort[item.short]) byShort[item.short] = item;
    }
  }
  return { byLong, byShort };
}

function tokenize(
  argv: string[],
  byLong: Record<string, FlagDef>,
  byShort: Record<string, FlagDef>,
): { occurrences: Occurrence[]; words: string[] } {
  const occurrences: Occurrence[] = [];
  const words: string[] = [];
  let index = 0;
  let afterDashdash = false;
  while (index < argv.length) {
    const token = argv[index];
    if (afterDashdash) {
      words.push(token);
      index += 1;
      continue;
    }
    if (token === "--") {
      afterDashdash = true;
      index += 1;
      continue;
    }
    if (token.startsWith("--")) {
      const equals = token.indexOf("=");
      const name = equals >= 0 ? token.slice(0, equals) : token;
      const inline = equals >= 0 ? token.slice(equals + 1) : null;
      let definition = byLong[name];
      if (!definition && name.startsWith("--no-")) {
        const base = "--" + name.slice(5);
        const baseDef = byLong[base];
        if (baseDef && baseDef.kind === "bool") {
          occurrences.push({ def: baseDef, name: base, value: false });
          index += 1;
          continue;
        }
      }
      if (!definition) {
        const guess = suggest(name, Object.keys(byLong).sort());
        throw new UsageError(`unknown flag "${name}"`, guess ? `did you mean "${guess}"?` : null);
      }
      if (definition.kind === "value") {
        let value: string;
        if (inline !== null) {
          value = inline;
        } else {
          if (index + 1 >= argv.length) {
            throw new UsageError(`Flag ${name} needs a value`, `Pass ${name} <value>`);
          }
          value = argv[index + 1];
          index += 1;
        }
        occurrences.push({ def: definition, name, value });
      } else {
        let value: boolean | string = true;
        if (inline !== null) {
          const lowered = inline.trim().toLowerCase();
          if (TRUE_WORDS.includes(lowered)) value = true;
          else if (FALSE_WORDS.includes(lowered)) value = false;
          else throw new UsageError(`Flag ${name} takes true or false, got ${JSON.stringify(inline)}`);
        }
        occurrences.push({ def: definition, name, value });
      }
      index += 1;
      continue;
    }
    if (token.startsWith("-") && token !== "-") {
      const definition = byShort[token];
      if (!definition) {
        throw new UsageError(`unknown flag "${token}"`, "Run acme --help for global flags");
      }
      if (definition.kind === "value") {
        if (index + 1 >= argv.length) {
          throw new UsageError(`Flag ${token} needs a value`, `Pass ${token} <value>`);
        }
        occurrences.push({ def: definition, name: definition.long, value: argv[index + 1] });
        index += 1;
      } else {
        occurrences.push({ def: definition, name: definition.long, value: true });
      }
      index += 1;
      continue;
    }
    words.push(token);
    index += 1;
  }
  return { occurrences, words };
}

export function levenshtein(left: string, right: string): number {
  if (left === right) return 0;
  if (!left) return right.length;
  if (!right) return left.length;
  let previous = Array.from({ length: right.length + 1 }, (_value, index) => index);
  for (let i = 1; i <= left.length; i += 1) {
    const current = [i];
    for (let j = 1; j <= right.length; j += 1) {
      const cost = left[i - 1] === right[j - 1] ? 0 : 1;
      current.push(Math.min(previous[j] + 1, current[j - 1] + 1, previous[j - 1] + cost));
    }
    previous = current;
  }
  return previous[right.length];
}

export function suggest(word: string, candidates: string[]): string | null {
  let best: string | null = null;
  let bestDistance = 99;
  for (const candidate of candidates) {
    const distance = levenshtein(word, candidate);
    if (distance < bestDistance) {
      best = candidate;
      bestDistance = distance;
    }
  }
  if (best !== null && bestDistance <= Math.max(2, Math.floor(word.length / 3) + 1)) return best;
  return null;
}

function usageTail(spec: Spec): string {
  const parts = (spec.arguments || []).map((argument) =>
    argument.required === false ? `[${argument.name}]` : `<${argument.name}>`,
  );
  parts.push("[flags]");
  return parts.join(" ");
}

export function parse(
  argv: string[],
  specs: Record<string, Spec>,
): { spec: Spec | null; opts: Record<string, any>; positionals: string[] } {
  const { byLong, byShort } = indexFlags(specs);
  const { occurrences, words } = tokenize(argv, byLong, byShort);

  let spec: Spec | null = null;
  let consumed = 0;
  if (words.length) {
    if (words.length >= 2 && specs[words.slice(0, 2).join(" ")]) {
      spec = specs[words.slice(0, 2).join(" ")];
      consumed = 2;
    } else if (specs[words[0]]) {
      spec = specs[words[0]];
      consumed = 1;
    } else {
      const top = Object.keys(specs).filter((path) => !path.includes(" "));
      const guess = suggest(words[0], top);
      throw new UsageError(
        `unknown command "${words.slice(0, 2).join(" ")}"`,
        guess ? `did you mean "${guess}"?` : null,
      );
    }
  }

  const positionals = words.slice(consumed);
  if (spec && spec.group && positionals.length) {
    const children = Object.keys(specs)
      .filter((pathKey) => pathKey.startsWith(spec!.path.join(" ") + " "))
      .map((pathKey) => pathKey.split(" ").slice(-1)[0]);
    const guess = suggest(positionals[0], children);
    throw new UsageError(
      `unknown command "${[...spec.path, positionals[0]].join(" ")}"`,
      guess ? `did you mean "${spec.path[0]} ${guess}"?` : null,
    );
  }

  const allowedFlags = [...GLOBAL_FLAGS, ...((spec?.flags as FlagDef[]) || [])];
  const allowedLongs = new Set(allowedFlags.map((item) => item.long));
  const opts: Record<string, any> = {};
  for (const item of allowedFlags) {
    opts[key(item.long)] = item.repeat && item.default === null ? [] : item.default ?? null;
  }
  for (const occurrence of occurrences) {
    const definition = occurrence.def;
    if (!definition || !allowedLongs.has(definition.long)) {
      const guess = suggest(occurrence.name, [...allowedLongs].sort());
      throw new UsageError(
        `unknown flag "${occurrence.name}"`,
        guess ? `did you mean "${guess}"?` : null,
      );
    }
    const optionKey = key(definition.long);
    if (definition.repeat) {
      if (!Array.isArray(opts[optionKey])) opts[optionKey] = [];
      opts[optionKey].push(occurrence.value);
    } else {
      opts[optionKey] = occurrence.value;
    }
  }

  if (opts.help) return { spec, opts, positionals };

  if (spec) {
    const args = spec.arguments || [];
    const required = args.filter((argument) => argument.required !== false).length;
    if (positionals.length > args.length) {
      throw new UsageError(
        `unexpected argument ${JSON.stringify(positionals[args.length])}`,
        `Usage: acme ${spec.path.join(" ")} ${usageTail(spec)}`,
      );
    }
    if (positionals.length < required) {
      const missing = args[positionals.length].name;
      throw new UsageError(
        `missing required argument <${missing}>`,
        `Usage: acme ${spec.path.join(" ")} ${usageTail(spec)}`,
      );
    }
  }
  return { spec, opts, positionals };
}

# CLI Guidelines for SaaS Products

**The manual inside the CLIA skill.**

| | |
|---|---|
| Status | Draft |
| Version | 0.1 |
| Applies to | Any SaaS product exposing an HTTP API |
| Normative language | MUST, SHOULD, MAY (RFC 2119 style) |

## How to use this document

Read the whole document before writing command code. Follow the phases in order. Rules marked MUST are enforced by the conformance checker. Rules marked SHOULD are reviewed by a human. Rules marked MAY are optional.

When a product constraint conflicts with a rule, follow the rule for the interface and record the exception in `CLI.md` with the reason. An exception that is written down is fine. An exception that is discovered later is a bug.

Three words drive every decision:

- **Lean:** smallest surface that covers the product. Few commands, few dependencies, fast startup.
- **Efficient:** one request per command where possible. Output sized for the task. Flags that avoid extra round trips.
- **Effective:** the command does what its name says, fails loudly, and leaves state consistent.

## 1. The contract

A CLI is finished when it keeps these seven guarantees:

1. Every documented product capability has a command.
2. Given flags and a token, every command runs without interaction.
3. `stdout` carries data. `stderr` carries progress, hints, and errors.
4. Every data command supports `--json` with a stable shape.
5. Exit codes separate success from failure class.
6. `--help` teaches usage with real examples.
7. Failure never leaves partial state silently.

If a rule later in this document conflicts with these guarantees, the guarantees win.

## 2. Before code: inventory the product

Do not start from endpoints. Start from jobs a user does in the product.

### 2.1 Sources

Read, in this order:

1. The product UI navigation and main screens. Each screen is a capability.
2. The route definitions or OpenAPI/GraphQL schema.
3. The official SDK or internal API client in the repo.
4. The docs, changelog, and support macros for capabilities the docs forget.

### 2.2 Surface map

Write `CLI.md` in the repo root with this table before writing command code:

| Capability | User job | API call | Class | Command | Notes |
|---|---|---|---|---|---|
| List projects | Find a project | `GET /v1/projects` | read | `acme project list` | paginated |
| Create project | Start a project | `POST /v1/projects` | write | `acme project create` | idempotency key |
| Delete project | Remove a project | `DELETE /v1/projects/{id}` | destructive | `acme project delete` | needs `--yes` |
| Read logs | Debug a deploy | `GET /v1/deploys/{id}/logs` | read | `acme deploy logs` | stream |

Rules:

- One row per user job. Two jobs can share an endpoint and get two commands.
- Class every row as `read`, `write`, or `destructive`.
- List gaps at the bottom. A gap is a UI capability with no public API.
- Cover at least 90% of the rows with a command before implementation starts.

### 2.3 Gaps

When the UI uses an endpoint the product does not document, you have three options. Use a documented endpoint, leave the capability out with a note, or ask the product team to expose it. Do not scrape the UI and do not call private endpoints.

## 3. Command grammar and naming

### 3.1 Shape

```
<tool> <resource> <verb> [identifier] [flags]
```

```sh
acme project list
acme project get prj_123
acme deploy create web --ref v1.4.2
acme deploy logs dep_456 --follow
acme token revoke tok_789 --yes
```

Rules:

- The tool name is the product name, lowercased and hyphenated. `acme`, `acme-cloud`, `acme-cli` only when the bare name is taken.
- Resources are lowercase singular nouns: `project`, not `projects` or `Project`.
- Verbs are imperative: `list`, `get`, `create`, `update`, `delete`, plus domain verbs such as `cancel`, `retry`, `rotate`, `invite`, `archive`.
- Use kebab-case for multiword commands and flags: `access-token`, `--dry-run`.
- Nest at most two resource levels. Beyond that, use flags: `acme deploy logs dep_456`, not `acme project deploy log get`.

### 3.2 CRUD vocabulary

| Operation | Verb | Notes |
|---|---|---|
| Collection read | `list` | Supports pagination |
| Single read | `get` | Takes an ID or slug |
| Create | `create` | Required fields as flags, or `--file` |
| Partial update | `update` | Only changed fields |
| Full replace | `replace` | Rare, name it explicitly |
| Delete | `delete` | Destructive, supports `--dry-run` and `--yes` |

Do not invent a second word for the same operation. `fetch`, `show`, `ls`, and `rm` are hidden aliases at most, and the primary name stays canonical.

### 3.3 Domain verbs

Name the action the product uses in its UI. `cancel` and `revoke` mean different things to users even when both call `DELETE`. If the UI says "Archive", the command is `archive`, not `update --archived`.

### 3.4 Top-level commands

Reserve these names for cross-cutting tools:

```
auth        login, logout, status
config      get, set, list, unset
whoami      current user and org
completion  bash, zsh, fish
version     print version
help        same as --help
```

### 3.5 Predictability test

A user who knows one resource should guess the commands for another. Run this test before implementation: write the command names for three resources, hide the resource, and check that the pattern is identical.

Avoid abbreviations that collide. Disable prefix matching on command names. If two commands start with the same letters, typing the shorter one is an error, not a guess.

## 4. Arguments and flags

### 4.1 Positionals and flags

- Positionals identify the target: IDs, slugs, names.
- Flags change behavior or supply optional data.
- One positional at most for reads and deletes. `get <id>`, not `get <org> <project> <id>`.
- Required creation fields can be flags when there are five or fewer. Above that, accept `--file` with a JSON body.

### 4.2 Flag rules

- Every flag has a long form. Short forms only for the five most used flags in the tool.
- Accept both `--limit 10` and `--limit=10`.
- Booleans use `--force` and `--no-<name>`. Accept `--force=true` and `--force=false`.
- Repeatable flags collect arrays: `--tag a --tag b`. Never require comma-separated values.
- Show the default in help: `--limit <n>  Results per page (default: 50)`.
- Show the env fallback in help: `--token <token>  API token [env: ACME_TOKEN]`.
- Support `--` to stop flag parsing.
- A missing required flag prints the flag name and exits 2. Do not print the whole help page.

### 4.3 Global flags

Data commands accept these. `completion` and `version` print text by definition and ignore output flags.

| Flag | Behavior |
|---|---|
| `--json` | Machine output: one JSON document on stdout, no color, no prompts |
| `--quiet` | Suppress human chrome. Print the primary identifier only |
| `--no-color` | Disable ANSI color. Also honor `NO_COLOR` |
| `--no-input` | Fail instead of prompting |
| `--yes` | Confirm destructive actions without a prompt |
| `--dry-run` | Resolve the request and print it, send nothing |
| `--debug` | Verbose logs to stderr, redacted |
| `--timeout <seconds>` | Request timeout |
| `--profile <name>` | Select a config profile |
| `--help`, `-h` | Help for the current command |
| `--version` | Version, root command only |

`--json` implies `--no-color`, `--no-input`, and no progress spinners. An agent that passes `--json` must never be blocked by a prompt.

### 4.4 Stdin and files

- `-` means stdin for any flag that takes a file.
- `--file <path>` reads a JSON body from a file. `--file -` reads stdin.
- Large payloads use a file, not a shell argument.
- Never read stdin implicitly. A command that expects input says so in help.

## 5. Output

### 5.1 Streams

| Stream | Contents |
|---|---|
| `stdout` | The requested data, and nothing else |
| `stderr` | Progress, warnings, prompts, hints, errors |

Rules:

- No spinners, banners, or "Fetching..." on stdout. Pipes must contain clean data.
- Disable color when stdout is not a TTY, when `NO_COLOR` is set, or when `--json` is passed.
- Human output goes to stdout. A one-line hint such as `Run with --json for machine output` goes to stderr and appears once.
- Empty human result: `No projects found.` on stderr, exit 0.

### 5.2 Human output

The default is a table with a header row, aligned columns, and no wrapping beyond 120 columns. IDs stay whole. If a table would exceed the width, drop low-value columns and show them in `get`. Do not truncate an ID or a name because the terminal is narrow.

### 5.3 JSON output

`--json` prints exactly one JSON document to stdout and exits.

Single resource:

```json
{"id": "prj_123", "name": "web", "created_at": "2026-11-07T09:12:00Z"}
```

List:

```json
{"data": [{"id": "prj_123"}], "has_more": true, "next_cursor": "cur_456"}
```

Action:

```json
{"ok": true, "id": "dep_123", "status": "queued"}
```

Error, on stderr:

```json
{"error": {"code": "not_found", "message": "Project prj_123 not found", "hint": "Run acme project list", "status": 404, "request_id": "req_abc"}}
```

JSON rules:

- Keys are `snake_case` and match the product API. Pick one convention per tool and keep it.
- Timestamps are RFC 3339 in UTC with `Z`.
- Money is an integer in minor units, and the key names the unit: `amount_cents`.
- IDs are strings, even when they look numeric.
- Arrays are always arrays. Empty is `[]`, never `null`.
- Keys are always present. Missing values are `null`.
- No ANSI, no HTML, no trailing prose, no BOM.
- Field names, types, and shapes do not change in a minor version.

### 5.4 Lists and pagination output

- Default `--limit` is 50, maximum 200. Document both.
- `--cursor` continues from a previous page.
- `--all` follows cursors until exhausted, with a safety cap.
- JSON includes `has_more` and `next_cursor` on every list response.
- Human output prints `Showing 50 of 214. Next: --cursor cur_456` to stderr.
- Never truncate silently.

### 5.5 Streaming

- `--ndjson` prints one JSON object per line, one per event.
- Streaming commands flush per line and exit 0 on clean end.
- `--follow` keeps the stream open. Ctrl-C exits 130.
- Progress bars go to stderr and are disabled with `--json` or `--no-progress`.

### 5.6 Size control

- `--fields id,name,status` limits the top-level keys in JSON output. The shape stays an object, and unknown fields are an error, not silently ignored.
- `--quiet` on a list prints one ID per line, suitable for `xargs`.

## 6. Errors and exit codes

### 6.1 Human error format

```
error: project prj_123 not found
hint: run `acme project list` to see available projects
```

Rules:

- Name what failed and the value that failed.
- Give the next command when one exists.
- No stack traces unless `--debug`.
- No "An error occurred", "Request failed", or raw HTTP dumps.

### 6.2 Exit codes

| Code | Meaning | Typical cause |
|---|---|---|
| 0 | Success | |
| 1 | Unexpected error | Bug or unhandled case |
| 2 | Usage error | Bad flag, missing argument, unknown command |
| 3 | Authentication required | 401, missing or expired token |
| 4 | Forbidden | 403, plan limit, insufficient role |
| 5 | Not found | 404 |
| 6 | Conflict or invalid input | 409, 422, failed precondition |
| 7 | Rate limited or server error | 429, 5xx after retries |
| 8 | Network or timeout | DNS, connection, read timeout |
| 9 | Partial success | Bulk operation where some items failed |
| 130 | Interrupted | SIGINT |

Rules:

- Map HTTP status to exit codes in one function. Commands never call `process.exit` with arbitrary numbers.
- Partial success in a bulk operation exits non-zero and lists what failed. Do not report success when some items failed.
- Unknown commands and flags exit 2 and suggest the nearest match.

### 6.3 Error codes

Use a small stable set in the JSON error envelope: `usage`, `auth_required`, `forbidden`, `not_found`, `conflict`, `validation`, `rate_limited`, `server_error`, `network_error`, `timeout`, `cancelled`. Agents branch on `code`, not on the message.

## 7. Auth and config

### 7.1 Commands

```
acme auth login          # device flow or token paste
acme auth logout
acme auth status         # works with --json
acme whoami
```

- `auth login` on a TTY can open a browser. Off a TTY it prints the URL and code, or accepts `--token`.
- `auth status --json` returns `{"authenticated": true, "profile": "default", "org": "acme", "user": "omer@acme.com", "expires_at": "2026-12-01T00:00:00Z"}`.
- `auth logout` removes the local credential and confirms.

### 7.2 Credential precedence

1. `--token` (explicit, warn in help that it is visible in process lists)
2. `<TOOL>_TOKEN` or `<TOOL>_API_KEY`
3. Per-project config
4. User config
5. OS keychain

Document the order in `auth --help`. CI uses env. Humans use the keychain or config.

### 7.3 Config

- User config lives at `$XDG_CONFIG_HOME/<tool>/config.toml`, defaulting to `~/.config/<tool>/config.toml`.
- File permissions are `0600`. Refuse to read a world-readable file that contains a token.
- Project config lives at `.<tool>/config.toml` in the repo and never contains secrets.
- `config get`, `set`, `list`, and `unset` operate on the same file. `config list --json` exposes keys and sources.
- Profiles group base URL, org, and credentials: `--profile staging`, `<TOOL>_PROFILE=staging`.
- `--base-url` and `<TOOL>_BASE_URL` support self-hosted and staging environments.
- Validate credentials only in commands that need them. `--help` and `--version` never touch config or network.

### 7.4 Secrets

- Never print a token. Redact to `acme_****9f2a` when the value must be shown.
- Redact `Authorization`, cookies, and any key named `token`, `secret`, `password`, or `key` in `--debug` and `--dry-run`.
- Never write tokens to logs, crash reports, or telemetry.

## 8. Safety and state

### 8.1 Destructive commands

Destructive means data can be lost: delete, revoke, cancel, rotate, bulk update.

- On a TTY, print the target name and ID and ask for confirmation.
- Off a TTY, refuse without `--yes` and exit 2 with a hint.
- Support `--dry-run` on every destructive command. It prints the resolved request and exits 0.
- `delete --all` requires `--yes` and prints the count before acting.
- Never delete child resources implicitly. Show the cascade in help.

### 8.2 Dry run

`--dry-run` prints method, URL, and body to stderr with secrets redacted. It runs the same validation and auth checks as the real call, then stops before the request. Exit 0 means "would have run", not "ran".

### 8.3 Updates

- `update` sends only the fields the user passed. No read-modify-write unless the API requires it.
- Do not require a full object for a partial change.
- Conflicts exit 6 with the server message and a hint to `get` the current state.

### 8.4 Idempotency

- `create` sends an idempotency key. Derive it from the request and expose `--idempotency-key` for retries.
- Retries of writes happen only with an idempotency key.
- `--wait` blocks on long operations and prints progress to stderr.

### 8.5 Bulk operations

- `--all` acts on the full result set. It requires `--yes` off a TTY.
- `--max <n>` caps the work.
- Print a summary: succeeded, failed, skipped.
- Exit 9 when any item fails, even if others succeeded.

## 9. Network behavior

- Default timeout is 30 seconds. `--timeout` overrides.
- Retry idempotent requests twice on 429, 5xx, and network errors. Honor `Retry-After`. Use exponential backoff with jitter.
- Never retry a write without an idempotency key.
- Send a stable `User-Agent`: `<tool>/<version> (<os>; <arch>)`.
- Follow redirects only for safe methods, and never forward the token to another host.
- Use HTTP/2 when the client supports it. Reuse connections within one command.
- Parallelize independent lookups, not writes.
- Stream downloads to disk with progress on stderr. Do not buffer an entire file in memory.

## 10. Help and discoverability

`--help` is the product's documentation for agents. Treat it as a feature with tests.

### 10.1 Root help

Show usage, a two-line description, command groups, global flags, three examples, and a docs URL. Keep it under 60 lines.

### 10.2 Command help

Every command shows:

```
Create a deployment for a project.

Usage:
  acme deploy create <project> [flags]

Arguments:
  project   Project ID or slug

Flags:
  --ref <ref>          Git ref to deploy (default: main)
  --env <env>          Target environment: production, staging (default: production)
  --wait               Block until the deployment finishes
  --timeout <seconds>  Wait timeout (default: 600)
  --json               Print JSON
  --dry-run            Print the request without sending it
  -h, --help           Show this help

Examples:
  acme deploy create web --ref v1.4.2
  acme deploy create web --env staging --wait --json
  acme deploy create web --dry-run
```

Rules:

- At least two examples with realistic values. No `<your-id>` placeholders.
- Show defaults and env fallbacks.
- Show exit codes once at the root, not on every command.
- List related commands at the bottom when the next step is non-obvious.
- `--help` works at every level, offline, without auth.
- `acme help <command>` behaves the same as `acme <command> --help`.
- Unknown command: `error: unknown command "projet"` plus `hint: did you mean "project"?`, exit 2.
- Unknown flag: name it, list close matches, exit 2.

### 10.3 Machine-readable help

SHOULD ship `acme schema --json`, which prints the command tree with arguments, flags, defaults, and examples. Agents can load this once instead of running `--help` for every command. This is the single highest-leverage affordance for agent use.

### 10.4 Version

`--version` prints a semver string and nothing else: `1.4.2`. Build metadata is allowed after `+`. Do not print the tool name or a banner.

### 10.5 Completions

Ship `completion bash|zsh|fish`. Completions include subcommands and flag names. Completion generation never calls the network.

## 11. Stack, layout, and code

### 11.1 Stack selection

| Repo already uses | Build with | Ship as |
|---|---|---|
| TypeScript or Node | TypeScript + `commander` or `clipanion` | npm package with `npx`, optional Bun-compiled binary |
| Go | Go + `cobra` | static binary |
| Python | Python + `typer` | `uv tool` / `pipx` / wheel |
| Rust | Rust + `clap` | static binary |
| No preference | Go or Bun-compiled TypeScript | static binary |

Match the language of the API client when one exists. A CLI in the repo's language gets maintained. A CLI in a new language gets abandoned.

### 11.2 Layout

```
src/
  cli.ts               # entry, command registration, global flags
  commands/
    project/
      list.ts
      get.ts
      create.ts
      update.ts
      delete.ts
    deploy/
      ...
  lib/
    api.ts             # HTTP client, retries, auth header
    config.ts          # paths, profiles, precedence
    output.ts          # json, table, ndjson writers
    errors.ts          # error types, HTTP map, exit codes
    redact.ts
  index.ts
```

Rules:

- One file per command. Register commands in one place.
- Four layers: parse, command, client, format. Commands orchestrate. They do not format strings or build URLs.
- The output module writes. The error module maps. The client handles HTTP. No layer reaches around another.
- A command returns data. The wrapper prints it and sets the exit code.
- No business logic that belongs in the API. No client-side computation the UI does not do.
- Generate types from OpenAPI when available. Hand-write only what the schema misses.

### 11.3 Command skeleton

```ts
import { Command } from "commander";
import { client } from "../../lib/api";
import { emit } from "../../lib/output";

export const list = new Command("list")
  .description("List projects")
  .option("--limit <n>", "results per page", "50")
  .option("--cursor <cursor>", "start after this cursor")
  .option("--all", "fetch every page")
  .option("--json", "print JSON")
  .action(async (opts) => {
    const page = await client.projects.list({
      limit: Number(opts.limit),
      cursor: opts.cursor,
    });
    emit(page, { json: opts.json, human: "projects" });
  });
```

The wrapper handles `--dry-run`, errors, redaction, and exit codes. Command files stay short.

### 11.4 `CLI.md`

Every CLI repo carries `CLI.md` with the surface map, command tree, output shapes, safety classes, auth precedence, exit codes, and open gaps. It is the design record and the review artifact.

## 12. Performance

- Startup budgets: native under 50 ms, Node or Bun under 150 ms, Python under 300 ms, measured p95 with `hyperfine` on a warm cache.
- `--help`, `--version`, and `completion` do no network calls and no heavy imports.
- Lazy-load command modules and SDKs.
- Cache config reads for the life of the process.
- Do not check for updates on every run. Check once per 24 hours, cache the result, and allow `--no-update-check` and `<TOOL>_NO_UPDATE_CHECK=1`.
- Default page size 50, not 1000. Fetch more only when asked.
- Stop pagination when the caller has enough.
- One request per command where the API allows it. Batch lookups when the API supports it.

## 13. Distribution and versioning

- Ship at least one install path that needs no language runtime: a signed binary from GitHub Releases, or a package manager. Add npm, PyPI, or Homebrew when the ecosystem expects it.
- Publish checksums for every artifact. Sign releases when the platform allows.
- `curl | sh` installers detect OS and architecture and print the install path.
- Semver. Breaking changes to commands, flags, exit codes, or JSON fields require a major version.
- Deprecate before removal: warn on stderr for one minor release, then remove.
- Telemetry is off by default. If added, make it opt-in, document what is sent, and support `--no-telemetry`.
- Pin the version in CI examples. Document the upgrade path.

## 14. Testing

| Layer | What to test |
|---|---|
| Unit | Flag parsing, defaults, table formatter, JSON shaper, redaction, HTTP-to-exit mapping |
| Contract | Each command against a mock server with recorded fixtures |
| Golden | `--help` and `--json` snapshots for every command |
| Integration | Real binary, non-TTY, env token, no prompts |
| Smoke | Read-only run against staging in CI on a schedule |
| Conformance | The skill's checker against the built binary |

Rules:

- Test exit codes, not only output.
- Test the failure path: 401, 403, 404, 409, 429, 500, timeout.
- Run the suite with stdin closed and no TTY. Any hang is a failure.
- Snapshot JSON and fail on shape changes. A snapshot update is a deliberate review.
- Keep one script that a human can run by hand in under two minutes.

## 15. Documentation

- README: what the CLI is, install, auth, five copy-paste examples, command reference link, agent usage note.
- Generate the command reference from the command definitions when possible. Hand-written references drift.
- Changelog with Added, Changed, Deprecated, Removed, Fixed.
- `AGENTS.md` snippet: "Use the `acme` CLI for product operations. Prefer `--json`. Run `acme <command> --help` before guessing flags. Never pass `--yes` to a destructive command without confirming the target."
- Quickstart ends with a real result, not an install message.

## 16. Anti-patterns

| Pattern | Why it hurts | Do instead |
|---|---|---|
| Interactive-only login | Blocks CI and agents | Token or device flow with a non-TTY path |
| Tables with `--json` | Breaks parsers | JSON only on stdout |
| Silent truncation | Agents act on partial data | `has_more`, `next_cursor`, stderr note |
| "Request failed" | No next step | Name the failure, give a hint |
| Full object required for update | Extra reads, race conditions | Partial update with explicit fields |
| Org ID on every command | Noise, copy-paste errors | Persist it in config, allow override |
| One command per endpoint | Unguessable surface | One command per user job |
| Token in debug output | Credential leak | Central redaction |
| Retrying writes blindly | Duplicate resources | Idempotency key or no retry |
| TTY-dependent JSON | Pipelines break | Explicit `--json` |
| Spinners on stdout | Corrupts pipes | stderr only |
| Prompts in non-TTY | Hangs agents | Fail with a hint |
| Breaking field renames | Agents break | Major version |
| Hidden global state | Unreproducible runs | Visible config and `--profile` |
| `--force` everywhere | Data loss | `--dry-run`, `--yes`, target echo |

## 17. Definition of done

The CLI is done when every box is checked.

**Surface**

- [ ] `CLI.md` exists with a surface map and command tree.
- [ ] Every user-reachable capability has a command or a documented gap.
- [ ] Every command name follows the grammar and CRUD vocabulary.

**Interface**

- [ ] Every command has `--help` with arguments, flags, defaults, env fallbacks, and two real examples.
- [ ] `--version` prints semver only.
- [ ] Unknown commands and flags exit 2 with a suggestion.
- [ ] Shell completions exist for bash, zsh, and fish.

**Output**

- [ ] Every data command supports `--json` and emits one document.
- [ ] JSON uses stable `snake_case` keys, UTC timestamps, string IDs, and integer minor units for money.
- [ ] Lists include `has_more` and `next_cursor`; `--limit`, `--cursor`, and `--all` work.
- [ ] `--quiet` prints identifiers only.
- [ ] No ANSI codes when piped, when `--json`, or when `NO_COLOR` is set.
- [ ] Errors print to stderr with a code, message, and hint.

**Safety**

- [ ] Destructive commands prompt on a TTY and require `--yes` off a TTY.
- [ ] Destructive commands support `--dry-run` with redacted output.
- [ ] Writes send idempotency keys; retries never duplicate resources.
- [ ] Bulk operations print a summary and exit non-zero on any failure.

**Auth and config**

- [ ] `auth login`, `auth logout`, `auth status`, and `whoami` work.
- [ ] Precedence is flag, env, project config, user config, keychain, and it is documented.
- [ ] Config is `0600`; secrets never appear in logs or errors.
- [ ] Profiles and `--base-url` work.
- [ ] `--help` and `--version` work offline and without auth.

**Operations**

- [ ] Startup meets the budget for the stack.
- [ ] Update checks are cached and can be disabled.
- [ ] Release artifacts have checksums and a documented install path.
- [ ] Tests cover parsing, formatting, redaction, exit codes, and HTTP failures.
- [ ] Golden snapshots cover help and JSON for every command.
- [ ] The conformance checker passes.

**Agent path**

- [ ] With `ACME_TOKEN` set and stdin closed, every command runs without a prompt.
- [ ] `acme schema --json` describes the command tree.
- [ ] README includes the `AGENTS.md` snippet.
- [ ] Five canonical tasks complete using only `--help` and `--json`.

## 18. Reference: first session

A first working CLI in one session looks like this:

1. Read the repo and identify the API client, auth, and language.
2. Fill `CLI.md` with 20 to 40 capabilities and mark the gaps.
3. Write the command tree on one screen. Fix names until the pattern repeats.
4. Scaffold from the stack template: config, auth, client, output, errors.
5. Implement `auth status`, `whoami`, and one `list` command end to end.
6. Add `--json`, `--limit`, `--cursor`, and help examples to that command.
7. Implement reads, then writes, then destructive commands.
8. Run the conformance checker and fix every MUST failure.
9. Run the five canonical tasks with stdin closed.
10. Write the README and the agent snippet.

The first command proves the shape. Every command after it copies the shape.

## 19. Reference: canonical tasks

Use these five tasks to test any CLI:

```sh
# 1. Discover and authenticate
acme --help
acme auth status --json

# 2. Read a collection
acme project list --limit 5 --json

# 3. Read one resource
acme project get prj_123 --json

# 4. Preview a write, then perform it
acme project create --name test --dry-run
acme project create --name test --json

# 5. Fail safely
printf '' | acme project delete prj_123
# Expect exit 2 with a hint about --yes, not a hang.
```

An agent that can complete these five without reading the source can operate the product.

# CLI Guidelines for SaaS Products

**The manual inside the CLIA skill.**

| | |
|---|---|
| Status | Draft |
| Version | 0.2 |
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

### 2.4 Blocked conditions

Stop and report instead of guessing when any of these is true:

- A primary job needs a capability with no documented API, and no documented alternative covers it.
- Auth cannot be completed without a browser and the product has no token or device flow.
- The API does not document what a destructive call removes or cascades to.
- A resource can be identified by name, the API allows duplicates, and no ID path exists.
- Rate limits or quotas make a bulk command unsafe without a product decision.

A blocked report names the missing input, the commands that are safe to build now, and the smallest decision needed to unblock. Building a wrong command costs more than leaving a row open.

### 2.5 Definition of ready

Answer these in `CLI.md` before writing command code:

1. Tool name and binary name, checked against the package registry and `PATH`.
2. Repo language, package manager, and build command.
3. API style, base URLs, and API version header.
4. Auth method with a non-TTY path.
5. Surface map at 90% coverage, gaps listed.
6. Command tree that fits on one screen.
7. Output convention: key case, timestamps, IDs, money units.
8. Safety class for every write.
9. The first vertical slice, named.

A missing answer is a blocked condition, not an invitation to invent.

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

### 3.6 Resource resolution

Commands take an ID when the API has one. Accept a slug or name only when it is unique and documented.

- Resolve a name with one lookup call. Zero matches exits 5. Multiple matches exits 6 with the candidate IDs and a hint to retry with `--id`.
- Never act on the first match when several exist.
- Treat IDs as opaque strings. Do not parse a prefix to decide the resource type.
- `--project` and `--org` override context for one command. They do not persist.
- When no project or org is configured and several are available, exit 2 with the choices. Never pick a default silently.

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
| `--org <id>` | Override the org for this command |
| `--project <id>` | Override the project for this command |
| `--api-version <version>` | Override the pinned API version |
| `--help`, `-h` | Help for the current command |
| `--version` | Version, root command only |

`--json` implies `--no-color`, `--no-input`, and no progress spinners. An agent that passes `--json` must never be blocked by a prompt.

### 4.4 Stdin and files

- `-` means stdin for any flag that takes a file.
- `--file <path>` reads a JSON body from a file. `--file -` reads stdin.
- Large payloads use a file, not a shell argument.
- Never read stdin implicitly. A command that expects input says so in help.

### 4.5 List flags

Every `list` command accepts the same core set:

| Flag | Purpose | Notes |
|---|---|---|
| `--limit <n>` | Page size | Default 50, max 200 |
| `--cursor <cursor>` | Continue after a cursor | Opaque string |
| `--all` | Fetch every page | Safety cap, requires `--yes` off a TTY for large sets |
| `--sort <field>` | Sort order | Prefix `-` for descending |
| `--filter key=value` | Exact match | Repeatable |
| `--search <text>` | Server-side text search | Only when the API supports it |
| `--since <time>` / `--until <time>` | Time bounds | RFC 3339 or relative such as `24h` |
| `--fields <list>` | Project top-level keys | Comma-separated |
| `--full` | Full objects instead of summaries | Heavier response |

Rules:

- Add typed flags for the two or three filters users need most: `--status`, `--env`, `--owner`. Keep `--filter` for the long tail.
- Run filtering and search on the server. If the API has no option, say so in help before filtering on the client.
- Sort order is stable. When the API does not define one, sort by `created_at` descending and state it.
- `--all` has a cap, default 10,000 items, and exits 9 when it hits the cap.

### 4.6 Mutating data

- `create` uses typed flags for common fields and `--file` for nested objects.
- `update` uses `--set key=value` for scalar changes, repeatable, and `--unset key` to clear a field. Typed flags are sugar over the same patch.
- `--data '<json>'` is allowed for small inline bodies. `--file` wins when both are passed, and the tool says so.
- Never require a full object for a partial update.
- Send only the fields the user passed. A read-modify-write is allowed only when the API documents that it requires one.

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
{"error": {"code": "not_found", "message": "Project prj_123 not found", "hint": "Run acme project list", "status": 404, "request_id": "req_abc", "retryable": false}}
```

JSON rules:

- Keys use one convention per tool, inherited from the product API and documented in `CLI.md`. Do not mix conventions between commands.
- Timestamps are RFC 3339 in UTC with `Z`.
- Money is an integer in minor units, and the key names the unit: `amount_cents`.
- IDs are strings, even when they look numeric.
- Arrays are always arrays. Empty is `[]`, never `null`.
- Keys are always present unless `--fields` removed them. Missing values are `null`.
- Errors include `retryable` and, on a 429, `retry_after` in seconds.
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

### 5.7 Result shapes by command

Keep the shape of a result tied to the verb, not to the endpoint:

| Verb | JSON result |
|---|---|
| `list` | `{"data": [...], "has_more": false, "next_cursor": null}` |
| `get` | The full resource object |
| `create` | The created resource object |
| `update` | The updated resource object |
| `delete` | `{"ok": true, "id": "prj_123"}` |
| Action | `{"ok": true, "id": "dep_123", "status": "queued"}` |
| Job | `{"id": "job_123", "status": "running", ...}` |

Rules:

- `list` returns summary fields: identity, name, status, owner, timestamps. It omits bodies, logs, and nested collections. `get` returns the full object. `--full` opts a list into full objects.
- `create` and `update` return the object as the server sees it, including server-generated fields.
- `delete` returns the ID and `ok`. It does not echo the deleted object.
- A job result includes `status` and, when known, `terminal` as a boolean. Status values come from a documented enum.

### 5.8 Context economy

Agents pay for every token on stdout. Keep responses small enough to reason about.

- Never embed logs, file contents, or nested collections in a list response. Return counts and a follow-up command instead.
- Cap the default page at 50 items with summary fields.
- Truncate long text in human tables with an ellipsis and a hint to `get`. Never truncate JSON.
- Return the IDs and status the next command needs, so the agent does not make a second lookup.
- Warn on stderr when a single response exceeds 1 MB, and suggest `--fields`, `--limit`, or `--output`.
- `--output <path>` writes large payloads or downloads to a file and prints the path. It does not print the body.

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
- `auth status --json` returns `{"authenticated": true, "profile": "default", "base_url": "https://api.acme.com", "org": "acme", "user": "omer@acme.com", "expires_at": "2026-12-01T00:00:00Z"}`.
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
- Pin the API version in config, expose `--api-version`, and send it on every request in the header the API expects.
- Validate credentials only in commands that need them. `--help` and `--version` never touch config or network.

### 7.4 Secrets

- Never print a token. Redact to `acme_****9f2a` when the value must be shown.
- Redact `Authorization`, cookies, and any key named `token`, `secret`, `password`, or `key` in `--debug` and `--dry-run`.
- Never write tokens to logs, crash reports, or telemetry.

### 7.5 Environment visibility

An agent must know which product, org, and environment a command will act on before it runs.

- Root help shows the active profile, base URL, org, and API version when configured.
- `auth status` shows the same set, plus the user and token expiry.
- Destructive confirmation repeats the profile, environment, target name, and target ID.
- `whoami` is the one-command check: user, org, profile, environment, token expiry.
- When the target is ambiguous, exit 2 and list the choices. Never fall back to the first profile.
- Refresh tokens before they expire when expiry is under 60 seconds. If refresh fails, exit 3 with the `auth login` command.

### 7.6 Doctor

SHOULD ship `doctor`:

```
acme doctor
acme doctor --json
```

It checks the installed version, config path and permissions, credential presence and expiry, DNS and TLS to the base URL, proxy settings, clock skew over 5 minutes, and API reachability. It prints one line per check with pass, warn, or fail, and exits 1 if any check fails. `--json` returns a list of checks with `name`, `status`, `detail`, and `fix`.

`doctor` saves support time and gives an agent a single diagnostic command.

## 8. Safety and state

### 8.1 Destructive commands

Destructive means data can be lost: delete, revoke, cancel, rotate, bulk update.

- On a TTY, print the target name, ID, profile, and environment, then ask for confirmation.
- Off a TTY, refuse without `--yes` and exit 2 with a hint.
- Support `--dry-run` on every destructive command. It prints the resolved request and exits 0.
- `delete --all` requires `--yes` and prints the count before acting.
- Never delete child resources implicitly. Show the cascade in help.

### 8.2 Dry run

`--dry-run` prints method, URL, and body to stderr with secrets redacted. It runs the same validation and auth checks as the real call, then stops before the request. Exit 0 means "would have run", not "ran".

`--dry-run --json` prints a structured request to stdout instead:

```json
{"method": "POST", "url": "https://api.acme.com/v1/projects", "headers": {"content-type": "application/json"}, "body": {"name": "web"}}
```

The structured form lets an agent inspect a write without parsing prose. Secrets are redacted in both forms.

### 8.3 Updates

- `update` sends only the fields the user passed. No read-modify-write unless the API requires it.
- Do not require a full object for a partial change.
- Conflicts exit 6 with the server message and a hint to `get` the current state.

### 8.4 Idempotency

- `create` sends an idempotency key: a UUID generated once per invocation and reused for retries inside that invocation. `--idempotency-key` accepts an external key for a caller that retries across runs.
- Retries of writes happen only with an idempotency key.
- `--wait` blocks on long operations and prints progress to stderr.

### 8.5 Bulk operations

- `--all` acts on the full result set. It requires `--yes` off a TTY.
- `--max <n>` caps the work.
- Print a summary: succeeded, failed, skipped.
- Exit 9 when any item fails, even if others succeeded.

### 8.6 Asynchronous jobs

Some writes return a job instead of a finished resource. Handle them with one pattern:

- `create` prints the job object immediately with `{"id", "status", "terminal"}` and a hint to wait.
- `--wait` polls until a terminal status, then prints the finished resource when the API provides one.
- A `wait <id>` command exists for jobs created earlier: `acme deploy wait dep_123`.
- Poll with backoff: 1s, 2s, 4s, 8s, capped at 15s. Default timeout 600 seconds.
- Terminal statuses come from a documented enum. Success exits 0. Failure exits 1 and prints the server message. Cancellation exits 130 only when the user interrupted.
- Progress goes to stderr. `--json --wait` prints one final document, not a stream of polls.

## 9. Network behavior

- Default timeout is 30 seconds. `--timeout` overrides.
- Retry reads, and writes that carry an idempotency key, twice on 429, 5xx, and network errors. Honor `Retry-After`. Use exponential backoff with jitter.
- Never retry a write without an idempotency key.
- Send a stable `User-Agent`: `<tool>/<version> (<os>; <arch>)`.
- Follow redirects only for safe methods, and never forward the token to another host.
- Use HTTP/2 when the client supports it. Reuse connections within one command.
- Parallelize independent lookups, not writes.
- Stream downloads to disk with progress on stderr. Do not buffer an entire file in memory.
- Honor `HTTPS_PROXY`, `HTTP_PROXY`, and `NO_PROXY`.
- Verify TLS by default. Support `--cacert <path>` for a private CA. Do not ship an `--insecure` flag.
- Refuse a plain `http://` base URL unless the host is loopback or the user passes `--allow-http`.
- Write downloads to a temp file and rename on success. Never leave a partial file at the target path.
- For uploads, stream the body, set the content type from the file or `--content-type`, and support `--checksum` when the API accepts one.

## 10. Help and discoverability

`--help` is the product's documentation for agents. Treat it as a feature with tests.

### 10.1 Root help

Show usage, a two-line description, command groups, global flags, three examples, and a docs URL. Keep it under 60 lines. When a profile is configured, add one line with the active profile, base URL, org, and API version, for example `Profile: default (https://api.acme.com, org acme, API 2026-01-01)`.

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

### 10.6 Examples are tested

Help examples are fixtures, not decoration.

- Run each example with `--dry-run` where the command writes, and assert exit 0 and the request shape.
- Run read examples against a mock or sandbox and assert the exit code and JSON keys.
- Use realistic IDs and names. Never use `abc123`, `<id>`, or `foo`.
- When a product changes a flag, the example test fails before a user sees the stale help.

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
| Interactive REPL | Cannot be scripted or composed | One command per invocation |
| Silent profile or org choice | Writes land in the wrong account | Exit 2 with the choices |
| `tool@latest` in CI | Unreproducible builds | Pin the version |
| Client-side filtering by default | Wrong counts, missing records | Server-side filter or a warning |
| `--insecure` TLS flag | Silent credential exposure | Custom CA via `--cacert` |
| Auto-update on every run | Slow startup, surprise changes | Cached check, opt out |
| Terminal-width-dependent JSON | Parsers break across environments | Fixed shape, width only affects tables |

## 17. Definition of done

The CLI is done when every box is checked.

**Surface**

- [ ] `CLI.md` exists with a surface map and command tree.
- [ ] Every user-reachable capability has a command or a documented gap.
- [ ] Every command name follows the grammar and CRUD vocabulary.

**Interface**

- [ ] Every command has `--help` with arguments, flags, defaults, env fallbacks, and two real examples.
- [ ] Help examples are executed by the test suite.
- [ ] `--version` prints semver only.
- [ ] Unknown commands and flags exit 2 with a suggestion.
- [ ] Shell completions exist for bash, zsh, and fish.
- [ ] Root help shows the active profile, base URL, org, and API version.

**Output**

- [ ] Every data command supports `--json` and emits one document.
- [ ] JSON uses one stable key convention, UTC timestamps, string IDs, and integer minor units for money.
- [ ] Lists include `has_more` and `next_cursor`; `--limit`, `--cursor`, and `--all` work.
- [ ] Lists return summaries; `get` returns the full object; `--full` exists.
- [ ] `--quiet` prints identifiers only.
- [ ] No ANSI codes when piped, when `--json`, or when `NO_COLOR` is set.
- [ ] Errors print to stderr with a code, message, and hint.
- [ ] `--dry-run --json` prints a structured request.

**Safety**

- [ ] Destructive commands prompt on a TTY and require `--yes` off a TTY.
- [ ] Destructive commands support `--dry-run` with redacted output.
- [ ] Writes send idempotency keys; retries never duplicate resources.
- [ ] Bulk operations print a summary and exit 9 on any failure.
- [ ] `update` supports `--set` and `--unset`; no full object is required.
- [ ] Async commands expose a job, `--wait`, and a `wait` command.
- [ ] Name resolution never picks the first match when several exist.

**Auth and config**

- [ ] `auth login`, `auth logout`, `auth status`, and `whoami` work.
- [ ] Precedence is flag, env, project config, user config, keychain, and it is documented.
- [ ] Config is `0600`; secrets never appear in logs or errors.
- [ ] Profiles and `--base-url` work.
- [ ] `whoami` and `doctor` report the target and diagnose setup.
- [ ] Token refresh happens before expiry.
- [ ] `--help` and `--version` work offline and without auth.

**Operations**

- [ ] Startup meets the budget for the stack.
- [ ] Update checks are cached and can be disabled.
- [ ] Release artifacts have checksums and a documented install path.
- [ ] Tests cover parsing, formatting, redaction, exit codes, and HTTP failures.
- [ ] Golden snapshots cover help and JSON for every command.
- [ ] The conformance checker passes.
- [ ] HTTPS is enforced; proxy variables work; no `--insecure` flag exists.
- [ ] Downloads write atomically; uploads stream.

**Agent path**

- [ ] With `ACME_TOKEN` set and stdin closed, every command runs without a prompt.
- [ ] `acme schema --json` describes the command tree.
- [ ] README includes the `AGENTS.md` snippet.
- [ ] Five canonical tasks complete using only `--help` and `--json`.

## 18. Build loop

### 18.1 First session

A first working CLI in one session looks like this:

1. Read the repo and identify the API client, auth, and language.
2. Fill `CLI.md` with 20 to 40 capabilities and mark the gaps.
3. Write the command tree on one screen. Fix names until the pattern repeats.
4. Scaffold from the stack template: config, auth, client, output, errors.
5. Implement `auth status`, `whoami`, and one `list` command end to end.
6. Add `--json`, `--limit`, `--cursor`, `--fields`, and tested help examples to that command.
7. Run the per-command checklist below against it. Fix the shape before copying it.
8. Implement reads, then writes, then destructive commands, then streaming and bulk.
9. Run the conformance checker and fix every MUST failure.
10. Run the five canonical tasks with stdin closed.
11. Write the README, the agent snippet, and the changelog.

The first command proves the shape. Every command after it copies the shape.

### 18.2 Per-command checklist

Run this before marking any command done:

- [ ] The command comes from a row in the surface map and does one job.
- [ ] The name follows the grammar and the CRUD vocabulary.
- [ ] Usage fits on one line and names the argument type.
- [ ] Help has two tested examples with realistic values.
- [ ] Defaults and env fallbacks appear in help.
- [ ] `--json` returns the documented shape for its verb.
- [ ] Lists paginate and include `has_more` and `next_cursor`.
- [ ] Empty results exit 0 with an empty array in JSON.
- [ ] Errors use the shared envelope and the correct exit code.
- [ ] The command works with stdin closed and no TTY.
- [ ] Writes support `--dry-run` and redact secrets.
- [ ] Destructive commands echo profile, environment, name, and ID.
- [ ] Tests cover success, one failure, and the non-TTY path.
- [ ] The row is marked done in `CLI.md`.

### 18.3 Order of work

Build reads before writes, and writes before destructive commands. Reads prove the client, auth, config, and output modules with low risk. Writes prove idempotency, dry-run, and validation. Destructive commands prove confirmation and bulk safety. Streaming and bulk come last because they combine every earlier concern.

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

## 20. Scoring a CLI

Use this rubric to judge a finished CLI or a work in progress. Score from evidence: run the binary, read the help, inspect the JSON, break the auth. Do not score from the README.

| Dimension | Points | Full marks |
|---|---|---|
| Surface | 20 | ≥ 90% coverage, one command per job, gaps documented in `CLI.md` |
| Agent contract | 20 | `--json`, no non-TTY prompts, stable fields, exit codes, `--dry-run`, `schema --json` |
| Output | 15 | Correct shapes, pagination, summaries, context economy, no truncation |
| Safety | 15 | Confirmation, `--yes`, idempotency, ambiguity errors, environment echo |
| Auth and config | 10 | Non-TTY login, precedence, profiles, refresh, `doctor` |
| Help | 10 | Tested examples, defaults, env fallbacks, suggestions on error |
| Engineering | 10 | Clean layers, tests, startup budget, distribution, changelog |

Each dimension scores `0` when absent, half when partial, full when a reviewer can point to the behavior in a run. A CLI passes at **90/100 with zero MUST failures**. Two independent reviewers score within 5 points, or the gap is investigated.

Common score losses:

- `--json` exists but errors are prose.
- Lists truncate at 50 with no cursor.
- Login only works with a browser.
- `delete` prompts in CI.
- Help examples use placeholder IDs.
- Startup spends 300 ms loading every command module.

## 21. Exemplars

Study these CLIs for patterns. Copy the pattern, not the surface.

| CLI | Copy | Avoid |
|---|---|---|
| GitHub CLI (`gh`) | `--json` with field selection, `auth status`, grouped help, exit codes | Large flag surfaces on some commands |
| Fly.io (`flyctl`) | App and org context flags, `--yes`, machine output, deployment waits | Hiding context in implicit config |
| Vercel (`vercel`) | `--scope`, `--token`, `--yes`, production flags, project linking | Interactive defaults on first run |
| Stripe (`stripe`) | Test and live mode visibility, clear resource verbs, webhook tooling | Treating the CLI as a thin HTTP shell |
| AWS (`aws`) | Profiles, output selection, consistent pagination | Help depth and inconsistent short flags |

Read one exemplar before designing the command tree. Read the guidelines again before shipping.

## 22. Final check

Before you call the CLI done, run these five commands with a test token and no TTY:

```sh
acme doctor --json
acme whoami --json
acme project list --limit 1 --json
acme project create --name test --dry-run --json
printf '' | acme project delete prj_123
```

Expected: doctor passes, whoami shows the target, list returns one item with pagination fields, dry-run returns a request object, delete exits 2 with a `--yes` hint. Anything else is a bug.

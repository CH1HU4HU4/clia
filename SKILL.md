---
name: clia
description: Build or extend a CLI for this SaaS product. Use when the repo contains a SaaS app with an HTTP API and the user asks for a CLI, a command line tool, a terminal interface, or agent access to the product. Do not use for generic shell scripting or MCP server requests.
---

# CLIA: build the product CLI

You are building a product-specific CLI inside the user's SaaS repo. The CLI
must cover the product surface, run without interaction, return stable JSON,
report failure through exit codes, and teach itself through `--help`.

`CLI-GUIDELINES.md` is normative. This skill is the workflow around it. Read
section 1, section 2, and section 17 first, then load sections by phase.

## Non-negotiables

1. Every user-reachable capability has a command, or a gap recorded with a reason.
2. Given flags and a token, every command runs with no TTY and no prompt.
3. `stdout` is data. `stderr` is progress, hints, and errors.
4. Every data command supports `--json` with one stable document.
5. Exit codes separate usage, auth, permission, missing, conflict, rate limit, and network failures.
6. `--help` has real examples, defaults, and env fallbacks.
7. A failure never leaves partial state silently.

If a later rule conflicts with these, these win.

## Workflow

### Phase 0: Preflight

Read, in this order: README, route definitions or OpenAPI, the API client or SDK,
auth code, any existing CLI or scripts.

Decide and record in `CLI.md`:

- Tool name and binary name, checked against the package registry and `PATH`.
- Repo language, package manager, build command. Match the repo; do not add a runtime.
- API style, base URLs, API version header.
- Auth method and a token path that needs no browser.
- Existing CLI path: **adopt**, **extend**, or **rebuild**. Default: extend.

Exit: you can name the language, package manager, API style, and auth method.

### Phase 1: Surface map

Inventory from two directions: UI navigation and the API. Read
`references/surface-map.md` now.

Write `CLI.md` with one row per user job:

| Capability | Source | User job | API call | Class | Command | Notes |
|---|---|---|---|---|---|---|

Cite every row to a UI route or an API operation. Classify each as `read`,
`write`, or `destructive`. List gaps at the bottom. Reach at least 90% coverage
before writing command code. Never use a private or undocumented endpoint.

Exit: coverage at least 90%, gaps listed, API capability inventory filled.

### Phase 2: Design

Read `CLI-GUIDELINES.md` sections 3, 4, 5, 10.

- Pick the product binary name and group commands by resource.
- Write the command tree so it fits on one screen.
- Name the output shape for every command and the exit-code map.
- Mark safety classes for every write: `--dry-run`, `--yes`, `--wait`.
- Name the first vertical slice, usually `auth status` plus `<resource> list`.

Exit: command tree, output conventions, safety classes, and vertical slice are
written in `CLI.md`.

### Phase 3: Scaffold

Read the stack guide for the repo language:

- `references/stacks/typescript.md`
- `references/stacks/go.md`
- `references/stacks/python.md`

Copy `templates/<stack>/` into the repo, normally as `cli/`, and rename the
sample `acme` to the product binary. Keep the module boundaries:

```
parse -> command -> client -> format
```

Wire config, auth, HTTP, output, and errors before writing resource commands.
Ship one live vertical slice. A mock-only success does not exit this phase: the
slice must hit a real sandbox or a recorded live response, and 401, 404, and 429
must map to the documented exits.

Exit: `--version`, `--help`, one live command, and mapped 401/404/429.

### Phase 4: Implement

Read `CLI-GUIDELINES.md` sections 6, 7, 8, 9, 11.

Build reads first, then writes, then destructive commands, then streaming and
bulk. One command at a time, through this loop:

1. Write the command spec in `CLI.md`: usage, arguments, flags, output, exits, safety.
2. Write help with two realistic, runnable examples.
3. Implement the client call, command, and formatter. No formatting in the command.
4. Add tests: success, one failure class, non-TTY, and `--dry-run` for writes.
5. Run the command-scoped P0 checks from `CLI-GUIDELINES.md` section 18.2:
   M03, M07, M08, M13, M14, M15, M16, M19, M20, M21, M22, M23, M25, M26, M27.
6. Mark the row done in `CLI.md`.

Exit: all applicable P0 checks pass.

### Phase 5: Verify

Read `CLI-GUIDELINES.md` sections 12, 14, 17, 18, 19.

Run the checker from the skill root:

```sh
scripts/conformance --bin ./cli/bin/acme --repo ./cli --report report.json
```

It starts the bundled mock API, drives the binary, inspects `CLI.md`, config,
tests, and CI, and reports every rule by ID. Fix every applicable P0 failure.
N/A is allowed only where `CLI.md` cites an unsupported API capability
(M23 idempotency, M26 async jobs, M44 files).

Then run the five canonical tasks with stdin closed:

```sh
acme --help
acme auth status --json
acme <resource> list --limit 5 --json
acme <resource> get <id> --json
acme <resource> create --name test --dry-run --json
printf '' | acme <resource> delete <id>     # expect exit 10, no hang
```

Exit: checker P0 pass, five canonical tasks pass non-interactively.

### Phase 6: Hand off

Read `CLI-GUIDELINES.md` sections 13, 15, 20, 21, 22.

- README: install, auth, five copy-paste examples, command reference, agent note.
- Generated command reference from the command definitions.
- `AGENTS.md` / `CLAUDE.md` snippet: use the CLI, prefer `--json`, read `--help`,
  never pass `--yes` without confirming the target.
- Changelog and semver.
- CI workflow: tests, goldens, checker, artifact with checksums.
- Release script or workflow with a documented install line.

Exit: a new user reaches a result in three commands; CI runs the full suite.

## Decision order

When several orders are possible:

1. Extend an existing CLI before rebuilding.
2. Match the repo language before choosing a nicer stack.
3. One command per user job before one command per endpoint.
4. Server-side filtering before client-side filtering.
5. An explicit error before a silent fallback.
6. A recorded gap before a private endpoint.
7. A tested example before prose.

## Stop conditions

Stop and report instead of guessing when:

- A primary job needs a capability with no documented API and no documented alternative.
- Auth cannot complete without a browser and there is no token or device flow.
- The API does not document what a destructive call removes or cascades to.
- A name can match several resources, the API allows duplicates, and no ID path exists.
- Rate limits or quotas make a bulk command unsafe without a product decision.

Write the blocked report with: the missing input, the commands that are safe to
build now, and the smallest decision needed to unblock. Do not invent behavior.

## Read by phase

| Phase | Read |
|---|---|
| Preflight | `CLI-GUIDELINES.md` 1, 2; `references/surface-map.md` |
| Design | `CLI-GUIDELINES.md` 3, 4, 5, 10 |
| Scaffold | stack guide in `references/stacks/`; template README |
| Implement | `CLI-GUIDELINES.md` 6-9, 11 |
| Verify | `CLI-GUIDELINES.md` 12, 14, 17-19; `references/checker.md` |
| Hand off | `CLI-GUIDELINES.md` 13, 15, 20-22 |

## Skill map

```text
SKILL.md                  this workflow
CLI-GUIDELINES.md         normative rules, including section 17 checks
references/surface-map.md inventory method, tables, definition of ready
references/stacks/        TypeScript, Go, Python setup guides
references/checker.md     checker usage, config, evidence model
templates/                runnable acme skeletons that pass P0
scripts/conformance       checker: runs the binary and reports rules by ID
scripts/mock_api.py       mock SaaS API used by checks and evals
evals/                    positive and negative fixtures; run-evals
```

## Rules of engagement

- Do not generate the CLI from OpenAPI without the surface map and design pass.
- Do not add an MCP server here. CLIA builds the CLI; a server can share the client later.
- Do not prompt off a TTY. `--json` implies no color, no prompts, no spinners.
- Do not print a token, ever. Redact `authorization`, cookies, and any key named
  `token`, `secret`, `password`, or `key` in logs, errors, and dry runs.
- Do not let an agent delete data with a bare `--yes`. Echo the target and
  support `--dry-run`.
- Keep startup inside budget: native 50 ms, Node 150 ms, Python 300 ms.
- Keep the JSON contract stable. A field rename is a major version.

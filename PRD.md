# CLIA PRD

**CLI Anything: an agent skill for building a SaaS CLI.**

| | |
|---|---|
| Status | Draft |
| Version | 0.1 |
| Owner | Omer |
| Last updated | 2026-11-07 |
| Repo | `CH1HU4HU4/clia` |

## 1. Summary

CLIA is a skill that teaches a coding agent to build a lean, efficient, effective CLI for the SaaS product in its repo. The skill ships a workflow, a normative manual (`CLI-GUIDELINES.md`), stack templates, a surface map format, and a conformance checker. The CLI it produces covers at least 90% of the capabilities a user can reach in the product UI, runs without interaction, prints stable JSON, and teaches its own usage through `--help`.

CLIA is a manual plus a verification loop. It does not generate a generic CLI from an OpenAPI file. It gives the agent decisions it can follow and a standard it can be held to.

## 2. Problem

A SaaS product ships two interfaces: a UI for people and an HTTP API for machines. Agents get neither. A browser is slow and brittle. The raw API forces the agent to rediscover auth, endpoints, pagination, and error shapes on every task. A CLI in the middle turns the product into composable commands, and an agent already knows how to run commands.

Most SaaS CLIs fail in one of three ways:

1. **Partial surface.** The CLI wraps the easy endpoints and leaves the rest to curl. Agents fall back to raw HTTP for the work that matters.
2. **Human-only design.** Login opens a browser, destructive actions prompt, output is a table. None of it works in a non-TTY session.
3. **Unstable contract.** JSON keys drift, errors say "request failed", lists truncate without warning. An agent cannot branch on any of it.

Each failure pushes the agent back to the UI or to hand-written HTTP, which defeats the purpose of the CLI.

## 3. Users

| User | Context | Needs |
|---|---|---|
| **Coding agent** (primary) | Works inside a SaaS repo, asked to "give us a CLI" | A manual it can follow without guessing, templates that run, a way to check its own work |
| **SaaS engineer** | Reviews and maintains the CLI | Code that fits the repo, tests that catch API drift, few dependencies |
| **Customer operator or agent** | Installs the shipped CLI | Stable commands, JSON, exit codes, no prompts |
| **Support engineer** | Inspects and fixes customer state | Fast read commands, clear errors, safe writes |

The primary user is the agent. Every document and template in CLIA is written to be read by an agent with shell access and the product source.

## 4. What CLIA is

CLIA is a skill, not a generator. The agent reads it, inspects the product, designs the command surface, scaffolds, implements, and verifies.

### 4.1 Skill anatomy

| Component | Purpose |
|---|---|
| `SKILL.md` | Trigger, short workflow, decision order, links to references |
| `CLI-GUIDELINES.md` | Normative rules for the CLI. The manual the agent follows |
| `references/surface-map.md` | How to inventory product capabilities and fill the map |
| `references/stacks/` | One setup guide per language: TypeScript, Go, Python |
| `templates/` | Runnable skeletons with auth, config, output, errors, and one working command |
| `scripts/conformance` | Checks a produced CLI against the MUST rules |
| `evals/` | Fixture products with expected outcomes for testing the skill |

The skill targets harnesses that support folder-based skills (OpenCode, Claude Code, Codex). It stays portable by using plain markdown and a single `SKILL.md` entry point. `SKILL.md` stays under 300 lines and loads references per phase, so the agent reads the surface map before the stack guide and the guidelines only when it designs or checks commands.

### 4.2 Skill trigger

`SKILL.md` opens with a description close to this:

> Build or extend a CLI for this SaaS product. Use when the repo contains a SaaS app with an HTTP API and the user asks for a CLI, a command line tool, a terminal interface, or agent access to the product.

The trigger names the repo condition, the artifact, and the user phrasing. It avoids firing on generic shell scripting or on MCP server requests.

### 4.3 What the produced CLI is

A product-specific command line tool, named after the product, that:

- exposes the same capabilities as the product UI
- authenticates with an API token or a device flow, no browser required
- returns JSON on every data command
- reports failure through exit codes and structured errors
- carries help text complete enough for an agent to use it without reading source

## 5. Goals and non-goals

### 5.1 Goals

| Goal | Measure |
|---|---|
| Cover the product surface | ≥ 90% of user-reachable capabilities have a command |
| Make every command scriptable | 0 prompts when stdin is not a TTY |
| Make output machine-usable | 100% of commands support `--json` with a stable shape |
| Make help sufficient | An agent completes 5 canonical tasks from `--help` alone |
| Keep the CLI lean | Startup p95 under 150 ms for Node, 50 ms for native binaries |
| Catch drift | Conformance checker passes 100% of MUST rules in CI |

### 5.2 Non-goals

- A GUI or TUI for the product
- An MCP server (a CLI and an MCP server can share a client, but CLIA builds the CLI)
- Hosting, deployment, or package registry publishing for the product
- Replacing the product API or SDK
- Auto-generating a CLI from OpenAPI with no design pass
- Supporting every language in v1. TypeScript first, then Go and Python
- Reverse-engineering private endpoints the product does not document

## 6. Workflow

The skill walks the agent through six phases. Each phase has an exit criterion, so the agent knows when to move on.

| Phase | Input | Output | Exit criterion |
|---|---|---|---|
| 0. Preflight | Repo, API docs, existing client | Stack and auth decision | The agent can name the language, package manager, API style, and auth method |
| 1. Surface map | UI nav, routes, OpenAPI, SDK | `CLI.md` surface table | ≥ 90% of capabilities mapped, gaps listed |
| 2. Design | Surface map | Command tree, output shapes, safety classes | Tree fits on one screen, every command has one job |
| 3. Scaffold | Design, stack guide | Runnable skeleton with one vertical slice | `--version`, `--help`, and one real command work |
| 4. Implement | Command tree | Every command with help, JSON, tests | Conformance checker passes |
| 5. Verify | CLI | Golden snapshots, smoke script, agent run | 5 canonical tasks pass non-interactively |
| 6. Hand off | Verified CLI | README, reference, agent snippet, changelog | A new user reaches a result in 3 commands |

### 6.1 Phase detail

**Preflight.** Read the README, the API client, the route definitions, and the auth code. Find the existing CLI or scripts if any. Decide the language from what the repo already uses. Record the decision in `CLI.md`.

**Surface map.** Enumerate capabilities from two directions: the UI navigation and the API. Every row names the capability, the API call, the risk class (read, write, destructive), and the command that will cover it. Gaps are first-class: if the UI uses a private endpoint, write it down and either use a documented alternative or leave the capability out with a note.

**Design.** Name the tool after the product binary. Group commands by resource. Decide the output shape for each command, the exit code map, and which commands need `--dry-run`, `--yes`, or `--wait`. The whole tree should fit on one screen.

**Scaffold.** Start from the stack template. Wire config, auth, the HTTP client, the output module, and the error mapper before writing commands. Implement one vertical slice end to end, usually `<tool> <resource> list`, so the shape is proven.

**Implement.** Reads first, then writes, then destructive commands, then streaming and bulk. Each command gets `--help`, `--json`, tests, and a `--dry-run` if it changes state.

**Verify.** Run the conformance checker, golden snapshots for help and JSON, a non-TTY smoke script with a test token, and the five canonical tasks. Fix failures before handoff.

**Hand off.** README with install, auth, and five examples. Generated command reference. A short snippet for `AGENTS.md` or `CLAUDE.md` telling future agents to use the CLI and prefer `--json`.

## 7. Requirements

### 7.1 Skill requirements

| ID | Requirement |
|---|---|
| R1 | Detect the repo stack and match it. No new runtime for users when the repo already has one |
| R2 | Produce a surface map before writing command code |
| R3 | Scaffold auth, config, output, errors, and HTTP client as shared modules |
| R4 | Ship one complete vertical slice in the template |
| R5 | Enforce `CLI-GUIDELINES.md` through a conformance checker, not prose alone |
| R6 | Add tests for parsing, formatting, error mapping, and exit codes |
| R7 | Generate docs an agent can consume: help text, README, agent snippet |
| R8 | Handle missing or undocumented API capabilities without inventing behavior |
| R9 | Keep secrets out of source, logs, and error output |
| R10 | Make `--help` and `--version` work offline and without auth |

### 7.2 Quality bar for the produced CLI

`CLI-GUIDELINES.md` is normative. These are the outcomes the skill is accountable for:

- **Surface parity.** Every user-reachable read and write has a command, or a documented reason it does not.
- **Non-interactive.** Given flags and a token, every command runs to completion with no TTY.
- **Stable data.** JSON fields, types, and shapes change only in a major version.
- **Honest failure.** Exit codes distinguish usage, auth, permission, not found, conflict, rate limit, and network errors.
- **Self-teaching help.** Every command has real examples, defaults, env vars, and exit codes.
- **Safe writes.** Destructive commands confirm on a TTY, require `--yes` off a TTY, and support `--dry-run`.
- **Lean runtime.** Startup stays inside budget, dependencies stay few, help and version do no network work.

## 8. Success metrics

| Metric | Target | Measurement |
|---|---|---|
| Time to first working command | < 30 min | Timed agent run on a fixture repo |
| Surface coverage | ≥ 90% | Surface map rows with a command |
| Conformance | 100% of MUST rules | Checker output |
| Canonical agent tasks | 5 of 5 | Non-TTY scripted run using only `--help` and `--json` |
| Interactive prompts in non-TTY | 0 | Test suite scans stderr and process state |
| Startup latency | p95 < 150 ms Node, < 50 ms native | Hyperfine on the built binary |
| Human onboarding | 3 commands to first result | README walkthrough |
| JSON stability | 0 breaking changes in minor releases | Snapshot diff in CI |

## 9. Scope and milestones

### 9.1 This change

Phase 0: the two source documents.

- `PRD.md`: product definition, users, workflow, requirements, metrics.
- `CLI-GUIDELINES.md`: the manual the skill will carry.

The skill itself is not built in this change.

### 9.2 Roadmap

| Phase | Deliverable | Done when |
|---|---|---|
| 0 | PRD and guidelines | Both docs reviewed and merged |
| 1 | `SKILL.md`, surface map reference, decision tables | An agent can follow the skill by hand on a real repo |
| 2 | TypeScript template, then Go and Python | Each template builds and passes the checker |
| 3 | Conformance checker and eval fixtures | Checker catches seeded violations; 3 fixtures pass |
| 4 | Hardening and v1.0 | 5 canonical tasks pass on every fixture |

### 9.3 Out of scope for v1

- GraphQL-specific guidance beyond a client note
- OAuth browser callback flows on a server without a browser
- Windows-native installers
- Skill marketplaces and distribution automation
- Multi-product monorepo command namespacing

## 10. Risks

| Risk | Impact | Mitigation |
|---|---|---|
| The product API cannot reach a UI capability | Surface stays partial | Mark the gap in `CLI.md`, use a documented path, report it to the product team |
| Over-generation from OpenAPI | Endpoint-shaped commands nobody can guess | Phase 1 and 2 force a surface map and a design pass |
| Stack mismatch | Users need a new runtime | Match the repo language; ship a binary when the language allows |
| API drift | CLI breaks silently | Contract tests and the conformance checker in CI |
| Token leakage | Security incident | Central redaction, no tokens in debug output, env and keychain storage |
| Destructive misuse by an agent | Data loss | `--dry-run`, `--yes`, target echo, no bulk delete without confirmation |
| Skill rot | Agents follow stale rules | Version the guidelines, keep the checker executable, review on API changes |

## 11. Open questions

1. Should the skill ship a `clia` meta-CLI that scaffolds and checks, or keep everything as scripts inside the skill folder?
2. Does v1 need OAuth device flow, or is API token auth enough for the first fixtures?
3. How should the skill handle products with several APIs (core, billing, admin) in one repo: one binary with command groups, or several binaries?
4. Should the conformance checker be language-agnostic (run the built CLI) or inspect source too?
5. Do we standardize JSON on `snake_case` or inherit the product API convention? Current draft inherits, with one convention per tool.
6. Is `--fields` worth requiring in v1, or is it an optimization for later?
7. How do we version the guidelines: independent semver, or tied to skill releases?
8. Should the skill generate an MCP server from the same command tree as a follow-on, or stay CLI-only?

## 12. Appendix

### 12.1 Definitions

- **Lean:** smallest surface that covers the product, few dependencies, fast startup.
- **Efficient:** one request per command where possible, pagination that stops, output sized for the task.
- **Effective:** the command does what its name says, fails loudly, and leaves state consistent.
- **Surface map:** table of product capabilities, API calls, risk classes, and the commands that cover them.
- **Conformance checker:** script that runs the built CLI and checks the MUST rules in `CLI-GUIDELINES.md`.

### 12.2 Related documents

- [`CLI-GUIDELINES.md`](CLI-GUIDELINES.md): normative CLI rules.
- [`README.md`](README.md): repository entry point.

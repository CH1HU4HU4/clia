<img src="assets/clia-logo-icon.png" width="64" height="64" alt="">

# CLIA

**CLI Anything**: an agent skill for building a lean, efficient, effective CLI
for a SaaS product.

A CLI is the interface an agent already knows how to use. CLIA gives a coding
agent the decisions, templates, and verification loop to build one that covers
the product surface, runs without interaction, prints stable JSON, and teaches
itself through `--help`.

## What is in the box

| Path | Purpose |
|---|---|
| `SKILL.md` | Trigger, six-phase workflow, stop conditions, reading order |
| `CLI-GUIDELINES.md` | Normative manual; section 17 is the release checklist |
| `references/surface-map.md` | How to inventory the product and fill `CLI.md` |
| `references/stacks/` | TypeScript, Go, and Python setup guides |
| `references/checker.md` | Checker usage, config, evidence model, limits |
| `templates/` | Runnable `acme` skeletons; all three pass every P0 check |
| `scripts/conformance` | Runs a built CLI and reports every rule by ID |
| `scripts/mock_api.py` | Mock SaaS API: pagination, idempotency, device flow, errors |
| `evals/` | Positive and defective fixtures; `evals/run-evals` |

## Install as a skill

Copy or symlink this folder into your harness's skills directory under the name
`clia`:

```sh
# OpenCode
ln -s "$PWD" ~/.config/opencode/skills/clia

# Claude Code (project-local)
mkdir -p .claude/skills && ln -s "$PWD" .claude/skills/clia

# Codex: add the folder to the skills directory configured for the session
```

Restart the session. The skill triggers on "build a CLI", "command line tool",
"terminal interface", or "agent access" for a repo with an HTTP API.

## Use it on a repo

1. Ask the agent to build or extend the CLI. It reads `SKILL.md`, fills `CLI.md`,
   then scaffolds from the matching template.
2. When a first vertical slice exists, run the gate:

```sh
scripts/conformance --bin ./cli/bin/acme --repo ./cli --report report.json
```

3. Fix every applicable P0 failure. N/A is allowed only for unsupported
   idempotency, jobs, or files, cited in `CLI.md`.
4. Run the five canonical tasks with stdin closed, then hand off the README,
   agent snippet, CI, and release artifact.

## Verify the skill itself

```sh
python3 evals/run-evals
```

Expected:

```text
python-template      PASS
typescript-template  PASS
go-template          PASS
defective            PASS   caught prompt, missing --json, truncation, wrong exit, token leak
oauth-device         PASS   non-TTY device login and refresh work
```

The defective fixture ships five seeded bugs; the eval fails if the checker
misses any of them. Add every new reviewer finding to that fixture.

Requirements for the full suite: Python 3.9+, Node 22.6+, Go 1.22+.

## Design rules

- The template matches the repo language. A CLI in a new language gets abandoned.
- The surface map comes before command code. One command per user job.
- `--json`, exit codes, redaction, and non-TTY behavior are not optional.
- The checker is the gate. Prose alone does not enforce a contract.

## Read more

- [PRD.md](PRD.md): product definition, users, workflow, metrics.
- [CLI-GUIDELINES.md](CLI-GUIDELINES.md): the normative manual.
- [SKILL.md](SKILL.md): the workflow the agent follows.

## License

MIT. See [LICENSE](LICENSE).

Created in [T3 Code](https://t3.codes).

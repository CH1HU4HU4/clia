# Conformance checker

`scripts/conformance` runs a built CLI against the `[check]` items in section 17
of `CLI-GUIDELINES.md`. It is the merge gate, not a style linter.

## Run

```sh
scripts/conformance --bin ./cli/bin/acme --repo ./cli
scripts/conformance --bin ./cli/bin/acme --repo ./cli --json --report report.json
scripts/conformance --bin ./cli/bin/acme --repo ./cli --strict   # P1 also gates
scripts/conformance --bin ./cli/bin/acme --repo ./cli --update-goldens
```

| Flag | Meaning |
|---|---|
| `--bin` | Binary, or a launcher command such as `node bin/acme.ts` |
| `--repo` | CLI repo (default: current directory) |
| `--config` | `conformance.json` (default: `<repo>/conformance.json`) |
| `--cli-doc` | `CLI.md` path (default: `<repo>/CLI.md`) |
| `--mock` | `mock_api.py` path (default: bundled) |
| `--base-url` | Use a running API instead of starting the mock |
| `--report` | Write the JSON report here |
| `--json` | Print the report as JSON instead of text |
| `--strict` | P1 failures fail the gate |
| `--skip` | Comma-separated rule IDs (fire drills only; not for a merge) |
| `--update-goldens` | Write help and canonical snapshots |
| `--timeout` | Per-command timeout in seconds (default 25) |
| `--keep` | Keep the temporary home directory for debugging |

Exit: `0` gate pass, `1` gate fail, `2` setup or discovery failure.

## Evidence model

No `[check]` item reads application source. The checker uses:

- **the binary**: exit codes, stdout, stderr, help, schema, completions, timing
- **the repo**: `CLI.md`, `README.md`, tests, CI workflow, golden files
- **the config file**: mode, profiles, machine-output setting
- **the mock API**: request log, idempotency headers, refresh calls, seeded errors
- **a pseudo-terminal**: destructive confirmation on a TTY

The checker starts `scripts/mock_api.py` on a loopback port and points the CLI at
it. It sets a temp `HOME` and `XDG_CONFIG_HOME`, a test token, and a clean env.

## conformance.json

```json
{
  "name": "acme",
  "tool": "acme",
  "bin": "./bin/acme",
  "token_env": "ACME_TOKEN",
  "token": "test-token",
  "resource": "project",
  "sample_id": "prj_001",
  "ambiguous": "dupe",
  "startup_budget_ms": 150,
  "test_command": "npm test",
  "golden_dir": "tests/golden",
  "setup": [["config", "set", "base-url", "{base_url}"]],
  "login": ["auth", "login", "--token", "{token}"],
  "env": {"ACME_BASE_URL": "{base_url}"},
  "mock_args": ["--device-only"],
  "use_env_token": true,
  "key_case": "snake",
  "capabilities": {
    "jobs": false, "bulk": false, "files": false,
    "doctor": false, "schema": true, "completions": true,
    "update_check": false, "refresh": true, "idempotency": true
  }
}
```

Placeholders: `{base_url}`, `{token}`, `{xdg}`, `{tool}`, `{repo}`.

- `setup` runs once before discovery. Failures abort with exit 2.
- `login` runs after setup. Use `["auth","login","--device"]` for device-flow products.
- `capabilities` false marks dependent rules N/A with the inventory reason.
- `env` adds extra environment values for fixtures that do not use config.

## Verdicts

| Status | Meaning |
|---|---|
| `PASS` | Rule verified |
| `FAIL` | Rule violated; P0 blocks the gate |
| `N/A` | API capability unsupported and cited in `CLI.md` |
| `DEFERRED` | P1 feature not shipped yet |
| `REVIEW` | Human review item; reported, not auto-judged |
| `SKIP` | Explicitly skipped with `--skip` |

N/A is allowed only for M23 (idempotency), M26 (async jobs), and M44 (files),
and only when the API inventory says the capability is unsupported. Everything
else must pass or fail honestly. Do not build a fake capability to pass.

Review items (M02, M04, M05, M06, M29, M36, M47) are reported for a human. The
checker still gathers evidence for them where it can, such as README content and
the target line in root help.

## Goldens

`--update-goldens` writes:

- `tests/golden/help.json`: `--help` for every discovered command
- `tests/golden/canonical.json`: root help, `auth status`, list, get, create
  dry-run, and a refused delete

Snapshots normalize the base URL, token, request IDs, UUIDs, and timestamps.
Commit them. Review every change deliberately. A golden update is a contract
change; a drifted field is a bug.

## In CI

```yaml
- name: Conformance
  run: |
    npm test
    npm pack
    ../clia/scripts/conformance --bin ./bin/acme --repo . --report report.json
```

Keep the skill checkout pinned by ref. Run the checker on every PR that touches
commands, JSON shapes, or exit codes. Run `--strict` on the release branch.

## Limits

- Help fallback parsing expects the section format from section 10.2. Prefer
  shipping `schema --json`; the checker uses it when present.
- The checker cannot prove every secret path. It covers `--debug`, errors,
  `config list`, and dry runs; add fixture-specific assertions when the product
  handles more credential types.
- It drives one token and one org. Multi-tenant ambiguity is tested with the
  bundled duplicate names; extend `mock_api.py` for more.
- It does not replace the five canonical tasks. Run them in a sandbox too.

## Extending

1. Add or change the rule in section 17 first; IDs are stable.
2. Add the metadata to `scripts/conform/rules.py`.
3. Implement the evidence in the matching `checks_*.py`.
4. Add a seeded defect to `evals/fixtures/defective` so the check is proven.
5. Run `python3 evals/run-evals`.

A check that cannot fail on a bad fixture is decoration.

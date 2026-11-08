# CLIA evals

Two kinds of evidence:

- **Automated**: `python3 evals/run-evals` runs the conformance checker against
  the three templates and the defective fixture. It fails if a template stops
  passing P0, or if the checker misses a seeded defect.
- **Agent-run**: the existing-CLI and gaps cases need an agent and a reviewer.
  Their pass conditions are in each fixture's README.

## Automated cases

| Case | Setup | Pass condition |
|---|---|---|
| `python-template` | Python template, mock API | Every applicable P0 check passes |
| `typescript-template` | TypeScript template on Node 22.6+, mock API | Every applicable P0 check passes |
| `go-template` | Go 1.22+, built binary, mock API | Every applicable P0 check passes |
| `defective` | CLI with seeded defects | Checker fails M13, M15, M19, M30, M45 and names the prompt and token leak |
| `oauth-device` | Python template, mock in `--device-only` mode | Non-TTY device login passes M28; refresh passes M34 |

Run one case:

```sh
python3 evals/run-evals --only defective
```

## Seeded defects in `fixtures/defective`

| Defect | Caught by |
|---|---|
| Prompts for input with stdin closed | M45 (and M21 where a delete fixture exists) |
| `--json` accepted but ignored on list | M13 |
| Lists silently truncate at 3 items | M15 |
| 404 maps to exit 1 and "request failed" | M19 |
| `--debug` prints the API token | M30 |

When a reviewer or council finds a new defect, add it to this fixture and assert
the checker catches it. The eval grows with the skill.

## Agent-run cases

Run records live in `runs/`; the latest is `runs/2026-11-08.md` (both PASS).
Re-run these after any change to `SKILL.md`, `CLI-GUIDELINES.md`, or the checker.

### Existing CLI

`fixtures/existing-cli/` ships a human-only CLI with interactive login and table
output. The agent must extend it, not rebuild it. See its README.

### Gaps

`fixtures/gaps/` describes a UI capability with only a private endpoint. The
agent must record the gap and leave the capability out. See its README.

### Greenfield

Use `fixtures/defective/` as the API surface, or point a template at any fake
SaaS API. Score with section 20 of `CLI-GUIDELINES.md`.

## Adding a fixture

1. Add `conformance.json` with `bin`, `token`, `resource`, and capability flags.
2. Start the bundled mock with `scripts/mock_api.py` unless the fixture needs a
   different API.
3. Add the case to `run-evals` with an explicit expected outcome.

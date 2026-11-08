# Existing CLI fixture

A partial, human-only CLI that an agent is asked to extend. This is the
"Existing CLI" eval from the PRD.

## Setup

```sh
cd evals/fixtures/existing-cli
export ACME_TOKEN=test-token
python3 scripts/mock_api.py --port 8787 --quiet &   # from the skill root
python3 old_cli.py --base-url http://127.0.0.1:8787 project list
```

## What exists

`old_cli.py` has:

- interactive login that prompts for a token on every run
- table-only `project list`
- no `--json`, no pagination, no exit-code map, no tests

## Task for the agent

Extend, do not rebuild. Keep `project list` working while adding `--json`,
pagination, `auth login/status/logout`, `whoami`, and the exit-code map. Record
the "extend" decision and the preserved command names in `CLI.md`. Run the
conformance checker and fix every P0 failure.

## Pass condition

Existing commands keep their names and still work; the conformance checker
passes all applicable P0 checks; the agent did not rename or remove a working
command without a deprecation note.

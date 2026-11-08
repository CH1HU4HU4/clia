# acme

Command line for the Acme project API. Built from the CLIA Python template.

## Install

```sh
python3 -m pip install .
# or: pipx install .
acme --version
```

Published builds: download the wheel from a release, verify `checksums.txt`,
then `pipx install acme_cli-1.0.0-py3-none-any.whl`.

## Authenticate

```sh
export ACME_TOKEN="acme_live_..."   # CI and agents
acme auth login --token "$ACME_TOKEN"
acme auth login --device            # OAuth device flow, no browser callback
acme auth status --json
```

Precedence: `--token`, then `ACME_TOKEN` / `ACME_API_KEY`, then the user config,
then the keychain. `--help` and `--version` never need auth or the network.

## Five things to try

```sh
acme project list --limit 5
acme project get prj_001
acme project create --name web --dry-run --json
acme project create --name web --json
acme project update prj_001 --set status=paused --json
```

Point at staging with `--profile staging`, `--base-url`, or `ACME_BASE_URL`.
Machine output is a setting: `acme config set output json`.

## Documentation

- `CLI.md` — surface map, command tree, exit codes, gaps.
- `acme --help` and `acme <command> --help` — tested examples for every command.
- `acme schema --json` — the whole command tree in one document.
- Exit codes: 0 success, 2 usage, 3 auth, 4 forbidden, 5 not found, 6 conflict,
  7 rate limit/server, 8 network, 9 partial success, 10 confirmation, 11 ambiguous.

## Agent usage

Paste this into `AGENTS.md` or `CLAUDE.md`:

```md
Use the `acme` CLI for Acme operations instead of raw HTTP. Prefer `--json` and
read stdout only; errors are JSON on stderr with `code`, `hint`, and `retryable`.
Run `acme <command> --help` or `acme schema --json` before guessing flags.
Never pass `--yes` to a destructive command without confirming the target.
Preview writes with `--dry-run --json`.
```

## Development

```sh
python3 -m unittest discover -s tests -v
python3 -m acme --help
```

Startup budget: p95 under 300 ms. No runtime dependencies outside the Python
standard library. One file per command; numbers and formatting live in
`src/acme/output.py`, HTTP in `src/acme/api.py`, errors in `src/acme/errors.py`.

# acme

Command line for the Acme project API. Built from the CLIA TypeScript template.

Runs on Node 22.6+ with native TypeScript type stripping. No runtime dependencies.

## Install

```sh
npm install -g .
# or: npx acme-cli
acme --version
```

Published builds: download the package tarball from a release, verify
`checksums.txt`, then `npm install -g acme-cli-1.0.0.tgz`.

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
npm test
node bin/acme.ts --help
```

Startup budget: p95 under 150 ms. Keep `--help`, `--version`, and `completion`
free of network calls and heavy imports. Commands return data; `src/output.ts`
writes it, `src/api.ts` talks HTTP, `src/errors.ts` maps exits. One file per
command, registered once in `src/commands/index.ts`.

# Templates

Three runnable skeletons, one contract. Each one ships:

- `auth login` (token and device flow), `auth logout`, `auth status`, `whoami`
- `config get|set|list|unset`, profiles, `--base-url`, `--api-version`
- one resource (`project`) with list/get/create/update/delete
- `--json`, `--quiet`, `--fields`, pagination, summaries, `--full`
- one exit-code map, redacted errors, `--dry-run`
- TTY confirmation and `--yes` off a TTY
- idempotency keys and token refresh
- `schema --json`, completions, generated help, `CLI.md`, tests, CI
- `conformance.json` and `tests/golden/`

All three pass every applicable P0 check from `CLI-GUIDELINES.md` section 17.

| Stack | Directory | Runtime | Startup budget |
|---|---|---|---|
| TypeScript | `typescript/` | Node 22.6+ (native TS) | 150 ms |
| Go | `go/` | Go 1.22+ | 50 ms |
| Python | `python/` | Python 3.9+ | 300 ms |

## Instantiate

```sh
cp -R templates/<stack> cli
cd cli
grep -ril acme . | xargs sed -i '' 's/acme/yourproduct/g'   # macOS
# or: grep -ril acme . | xargs sed -i 's/acme/yourproduct/g'
```

Then:

1. Edit `src/…/constants.*` (or `internal/cli/constants.go`) for tool name,
   version, base URL, and docs URL.
2. Edit `CLI.md` with the real surface map; keep the sample shape until the map
   is filled.
3. Replace the `project` resource with the product's first resource.
4. Update `conformance.json` (`bin`, `resource`, `sample_id`, capabilities).
5. Run the checker:

```sh
../clia/scripts/conformance --bin ./bin/acme --repo . --update-goldens
../clia/scripts/conformance --bin ./bin/acme --repo . --strict
```

## What not to change

- The layering: parse -> command -> client -> format.
- The one exit-code map.
- The redaction module.
- The list envelope: `data`, `has_more`, `next_cursor`, `truncated`.
- The rule that `--json` writes one document to stdout.

## What to change

- Resource names, verbs, and command files.
- Output fields and summary selection.
- Auth flow if the product requires something other than token or device flow.
- Pagination adapter if the API is offset-based rather than cursor-based.
- The mock's fake data is only for evals; real contract tests use a sandbox.

## Verify a template

From the skill root:

```sh
python3 evals/run-evals --only python-template
```

The eval builds the binary when needed, starts the mock API, and asserts the
gate passes.

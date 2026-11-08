# Go stack guide

Use when the product repo is Go, or when a single static binary is the right
ship artifact. The template uses only the standard library.

## Start

```sh
cp -R templates/go cli
cd cli
```

Rename the sample:

```sh
grep -ril acme . | xargs sed -i '' 's/acme/yourproduct/g'   # macOS
# or: grep -ril acme . | xargs sed -i 's/acme/yourproduct/g'
```

Then update `go.mod` module path, `internal/cli/constants.go`, and `CLI.md`.
Keep the binary name and `Tool` identical.

## Layout

```
cmd/acme/main.go        # entry point
internal/cli/args.go     # flags, command matching, suggestions
internal/cli/config.go   # TOML subset, profiles, 0600
internal/cli/context.go  # one resolved target
internal/cli/api.go      # net/http, retries, refresh, error mapping
internal/cli/output.go   # JSON, table, quiet, dry-run writers
internal/cli/errors.go   # one exit-code map
internal/cli/redact.go   # masks tokens
internal/cli/help.go     # generated help
internal/cli/commands.go # one registry
internal/cli/*_cmd.go    # resource commands
internal/cli/tty_*.go    # build-tagged isatty
```

A command returns `(int, error)`. The wrapper prints errors and exits. No
command calls `os.Exit`.

## Build and test

```sh
go vet ./...
go test ./...
go build -trimpath -ldflags "-s -w" -o bin/acme ./cmd/acme
```

Cross-compile for releases:

```sh
GOOS=linux GOARCH=amd64 go build -trimpath -ldflags "-s -w" -o dist/acme-linux-amd64 ./cmd/acme
GOOS=darwin GOARCH=arm64 go build -trimpath -ldflags "-s -w" -o dist/acme-darwin-arm64 ./cmd/acme
```

## HTTP

`net/http` with a cloned default transport and `ProxyFromEnvironment`:

- Retry reads and idempotent writes twice on 429/5xx/network.
- Honor `Retry-After`; cap backoff at 2 seconds.
- Use one `http.Client` per process; reuse connections.
- Never add `--insecure`. Private CAs use `--cacert` with a custom pool.
- Map status to exit codes in `errors.go` only.

JSON decoding lands numbers in `float64`. IDs from real APIs must be strings; if
the product returns numeric IDs, decode with `json.Decoder.UseNumber()` and emit
strings, or the contract breaks.

## TTY detection

`os.ModeCharDevice` is true for `/dev/null`, so it is the wrong test for a
prompt. Use the build-tagged `isTerminal` ioctl in `tty_darwin.go` /
`tty_linux.go`. Add a build-tagged file for another OS rather than a runtime
dependency.

## Startup

Budget: p95 under 50 ms for the static binary. Measure:

```sh
hyperfine --warmup 3 './bin/acme --version'
```

No init-time network work, no heavy global registration, no command tree built
from files at startup.

## Tests

`go test ./...` covers parsing, redaction, error mapping, config round-trip, and
an `httptest` server for list/get/404 and delete refusal. Add contract tests per
resource as you build it. Keep one script a human can run in two minutes.

## Packaging

- Static binary per OS/arch in CI with `-trimpath -ldflags "-s -w"`.
- `sha256sum` checksums and an install line in the README.
- Do not commit the binary. Build it in CI and in `run-evals`.
- Pin the Go version in CI.

## Checklist

- [ ] `--help` and `--version` offline, with no token.
- [ ] One JSON document on stdout; structured errors on stderr.
- [ ] Exit-code table in `errors.go`; no arbitrary exits.
- [ ] Config `0600`; token never printed, including `--debug` and dry runs.
- [ ] Non-TTY delete exits 10 with a `--yes` hint.
- [ ] Proxy honored; no `--insecure`.
- [ ] Startup p95 under 50 ms.
- [ ] `scripts/conformance --bin ./bin/acme --repo .` passes every P0 check.

## Pitfalls

- `map[string]any` marshals keys alphabetically. That is stable, and `--fields`
  still preserves the documented key set; do not rely on insertion order.
- Forgetting `defer response.Body.Close()` leaks connections under retries.
- Installing a prompt before checking `isTerminal` hangs agents.
- Using `http.DefaultClient` without a timeout.
- Handling SIGINT by default gives exit 130 but no error envelope; the template
  traps it and prints `cancelled`.

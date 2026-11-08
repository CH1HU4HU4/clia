# TypeScript stack guide

Use when the product repo is TypeScript or Node, or when there is no existing
client and the team accepts Node. The template runs on Node 22.6+ with native
TypeScript type stripping, so it has **no runtime dependencies**.

## Start

```sh
cp -R templates/typescript cli
cd cli
```

Rename the sample binary and product strings:

```sh
grep -ril acme . | xargs sed -i '' 's/acme/yourproduct/g'   # macOS
# or: grep -ril acme . | xargs sed -i 's/acme/yourproduct/g'
```

Then update `package.json` `name`, `bin`, `src/constants.ts` (tool, version,
base URL, docs URL), and `CLI.md`. Keep `TOOL` and the binary name identical.

The sample has one resource (`project`) with list/get/create/update/delete, plus
`auth`, `config`, `whoami`, `schema`, `completion`, `version`, and `help`. Copy
the shape for the next resource; do not redesign the modules.

## Layout

```
bin/acme            # shell wrapper: sets NODE_USE_ENV_PROXY, execs node
bin/acme.ts         # entry point
src/cli.ts          # parse, dispatch, one error mapper
src/args.ts         # flags, command matching, suggestions
src/config.ts       # TOML subset, profiles, 0600
src/context.ts      # one resolved target
src/api.ts          # fetch, retries, refresh, error mapping
src/output.ts       # JSON, table, quiet, dry-run writers
src/errors.ts       # one exit-code map
src/redact.ts       # masks tokens everywhere
src/help.ts         # generated help
src/commands/       # one file per command, registered in index.ts
test/               # node:test unit + integration tests
```

Four layers: **parse -> command -> client -> format**. A command orchestrates.
It does not format strings or build URLs.

## Run and test

```sh
./bin/acme --help
npm test
npm run typecheck   # after npm install (typescript + @types/node)
```

Node 22.6+ strips types natively. Keep syntax **erasable**:

- no `enum`, no `namespace`, no constructor parameter properties
- import local files with their `.ts` extension
- no decorators or `const enum`
- type-only imports use `import type`

If the repo already compiles TypeScript, point the template at the repo build
instead of running source directly, and keep the same module boundaries.

## HTTP

`src/api.ts` uses global `fetch` with `AbortController` for timeouts.

- Set `NODE_USE_ENV_PROXY=1` before the process starts to honor `HTTP_PROXY` and
  `HTTPS_PROXY`. The template's `bin/acme` wrapper does this. Setting it at
  runtime is too late.
- Retry reads and idempotent writes twice on 429/5xx/network; honor
  `Retry-After`; never retry a write without an idempotency key.
- Map status to exit codes in `errors.ts` only. Commands never call
  `process.exit` with a number.
- Never forward the token to a redirect host. The template follows redirects
  only because the default API does not redirect; tighten this if yours does.

## Startup

Budget: p95 under 150 ms. Measure:

```sh
hyperfine --warmup 3 './bin/acme --version'
```

Keep `--help`, `--version`, and `completion` offline and free of heavy imports.
Do not check for updates on every run.

## Packaging

- npm package with a `bin` entry; the template's shell wrapper sets proxy env.
- `npm pack` in CI, `sha256sum *.tgz > checksums.txt`, upload the artifact.
- Node is required; do not claim a zero-runtime binary unless you add a
  Bun-compiled build and test it.
- Pin versions in CI examples. Do not use `tool@latest` there.

## Tests

`npm test` runs `node --test`. Cover:

- flag parsing, defaults, `--flag=value`, repeated flags, `--`
- table and JSON shaping, `--fields`, `--quiet`
- redaction of tokens and headers
- HTTP-to-exit mapping for 401/403/404/409/422/429/500/timeout
- non-TTY delete exit 10, `--dry-run`, idempotency
- help examples executed and JSON snapshots

## Checklist

- [ ] `--help` and `--version` work offline, with no config and no token.
- [ ] `--json` emits exactly one document on stdout; errors are JSON on stderr.
- [ ] No ANSI when piped, with `--json`, or with `NO_COLOR`.
- [ ] Config is `0600`; project config never holds a token.
- [ ] Destructive commands prompt on a TTY and exit 10 without `--yes` elsewhere.
- [ ] Proxy env is honored; no `--insecure` flag.
- [ ] Startup p95 under 150 ms with `hyperfine`.
- [ ] `scripts/conformance --bin ./bin/acme --repo .` passes every P0 check.

## Pitfalls

- Writing `process.exit()` inside a command skips buffered output. Set an exit
  code or return it to the wrapper.
- Reading stdin implicitly. Only `--file -` reads stdin.
- Using `fs.readSync` for a prompt: a PTY can be non-blocking. Use `readline`.
- Sorting JSON keys by hand; let `JSON.stringify` keep insertion order and keep
  the shape documented.
- Checking for updates synchronously; cache the check and make it opt-out.

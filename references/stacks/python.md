# Python stack guide

Use when the product repo is Python, or when the team ships Python tooling. The
template targets Python 3.9+ with the standard library only.

## Start

```sh
cp -R templates/python cli
cd cli
```

Rename the sample:

```sh
grep -ril acme . | xargs sed -i '' 's/acme/yourproduct/g'   # macOS
# or: grep -ril acme . | xargs sed -i 's/acme/yourproduct/g'
```

Then update `pyproject.toml`, `src/acme/constants.py`, and `CLI.md`.

## Layout

```
src/acme/cli.py          # parse, dispatch, one error mapper
src/acme/args.py         # flags, command matching, suggestions
src/acme/config.py       # TOML subset, profiles, 0600
src/acme/context.py      # one resolved target
src/acme/api.py          # urllib, retries, refresh, error mapping
src/acme/output.py       # JSON, table, quiet, dry-run writers
src/acme/errors.py       # one exit-code map
src/acme/redact.py       # masks tokens
src/acme/help.py         # generated help
src/acme/commands/       # one file per command
tests/                   # unittest discovery
```

## Run and test

```sh
PYTHONPATH=src python3 -m acme --help
# or after install:
python3 -m pip install .
acme --help

python3 -m unittest discover -s tests -v
```

The `bin/acme` launcher is for development. Installed users get the console
script declared in `pyproject.toml`.

## Parsing

The template hand-rolls a small parser so help, `schema --json`, suggestions,
and `--flag=value` behave the same on every command. Use argparse or Typer when
the repo already does, but keep the help sections (`Arguments`, `Flags`,
`Examples`) and the exit map.

## Config

The user config is `$XDG_CONFIG_HOME/acme/config.toml`, defaulting to
`~/.config/acme/config.toml`, mode `0600`. The template parses the TOML subset it
writes: top-level keys and `[profiles.<name>]` string keys.

- On Python 3.11+, swap the parser for `tomllib`; keep the writer.
- Refuse to read a world-readable file that contains a token.
- Project config (`./.acme/config.toml`) holds context only, never credentials.

## HTTP

`urllib.request` honors `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY` by default.
The template:

- retries reads and idempotent writes twice on 429/5xx/network
- honors `Retry-After`
- refreshes tokens within 60 seconds of expiry
- maps status to exit codes in `errors.py`

If the repo uses `httpx` or `requests`, keep the same error mapper and retry
policy. Do not add a dependency only for the CLI.

## Startup

Budget: p95 under 300 ms. Measure:

```sh
hyperfine --warmup 3 './bin/acme --version'
```

Keep imports small. Import command modules lazily if the tree grows. `--help`
and `--version` must not read the network.

## Packaging

- `pyproject.toml` with a `[project.scripts]` entry point.
- Build a wheel in CI: `python -m pip wheel . --no-deps -w dist`,
  `shasum -a 256`, upload.
- Install with `pipx install <wheel>` or `uv tool install`.
- Pin Python versions in CI examples.

## Tests

`unittest` discovery covers parsing, formatting, redaction, error mapping, config
mode, and an in-process HTTP server for list/get/404/delete refusal. Add
contract tests with recorded fixtures per resource.

## Checklist

- [ ] `--help` and `--version` offline, with no token.
- [ ] One JSON document on stdout; structured errors on stderr.
- [ ] No prompts off a TTY; `--json` implies `--no-input`.
- [ ] Config `0600`; token never printed.
- [ ] `--dry-run` on every destructive command.
- [ ] Exit codes match section 6.2 of the guidelines.
- [ ] Startup p95 under 300 ms.
- [ ] `scripts/conformance --bin ./bin/acme --repo .` passes every P0 check.

## Pitfalls

- `input()` in a non-TTY raises `EOFError` or hangs. Check `sys.stdin.isatty()`.
- Printing tables when `--json` is set. Route every write through `output.py`.
- `sys.exit()` inside a command skips the error mapper. Raise `CliError`.
- Using `getpass` off a TTY; require `--token` or the device flow instead.
- Letting a traceback escape. Catch once in `main`; show it only with `--debug`.

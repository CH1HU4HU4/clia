# Greenfield REST fixture

The positive case: an empty product repo with a fake SaaS API and token auth.
An agent starts from the matching template, fills `CLI.md`, and reaches a
working CLI.

## Setup

```sh
# From the skill root
python3 scripts/mock_api.py --port 8787 --quiet &
cp -R templates/python /tmp/acme-cli
# ... follow SKILL.md phases 0-6 against the mock ...
```

The mock exposes `/v1/projects` with cursor pagination, idempotency keys,
partial updates, duplicate names, expiring device tokens, and injectable
401/403/404/409/422/429/500/timeout responses.

## Pass condition

- Every applicable P0 check passes:
  `scripts/conformance --bin ./bin/acme --repo . --strict`
- The five canonical tasks pass with stdin closed.
- `CLI.md` has a cited surface map and a filled API inventory.
- The README has an install line and the `AGENTS.md` snippet.

`evals/run-evals` covers this case as `python-template`, `typescript-template`,
and `go-template`: each template is instantiated as-is against the mock and must
pass the full P0 gate.

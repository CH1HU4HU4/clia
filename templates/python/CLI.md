# CLI design record — acme

This is the design artifact review uses. It is filled before command code and
kept current. The conformance checker reads it for M01.

## Decisions

| Question | Answer |
|---|---|
| Tool and binary name | `acme` (checked: npm and PATH free) |
| Repo language and build | Python 3.9+, stdlib only, `python3 -m pip install .` |
| API style and base URLs | REST, `https://api.acme.com`, staging via profile |
| API version | `X-API-Version: 2026-01-01`, pinned in config |
| Auth | API token; OAuth device flow available; no browser callback |
| Existing CLI path | Rebuild (sample fixture; no existing CLI) |
| First vertical slice | `auth status` plus `project list` against the sandbox |

## Surface map

| Capability | Source | User job | API call | Class | Command | Notes |
|---|---|---|---|---|---|---|
| Browse projects | `web/projects/page.tsx` | Find a project | `GET /v1/projects` | read | `acme project list` | cursor pagination |
| Filter by status | `web/projects/page.tsx` | Work on active projects | `GET /v1/projects?status=` | read | `acme project list --status` | server-side |
| Search projects | `web/projects/page.tsx` | Find by text | `GET /v1/projects?search=` | read | `acme project list --search` | server-side |
| Read one project | `web/projects/[id]/page.tsx` | Inspect settings | `GET /v1/projects/{id}` | read | `acme project get` | full object |
| Resolve a project name | `web/projects/page.tsx` | Avoid copying IDs | `GET /v1/projects?name=` | read | `acme project get <name>` | ambiguity exits 11 |
| Create a project | `web/projects/new.tsx` | Start a project | `POST /v1/projects` | write | `acme project create` | idempotency key |
| Create from a file | `web/projects/new.tsx` | Nested settings | `POST /v1/projects` | write | `acme project create --file` | `-` reads stdin |
| Edit fields | `web/projects/[id]/settings.tsx` | Fix metadata | `PATCH /v1/projects/{id}` | write | `acme project update --set` | partial patch |
| Pause a project | `web/projects/[id]/settings.tsx` | Stop usage | `PATCH /v1/projects/{id}` | write | `acme project update --set status=paused` | domain state |
| Archive a project | `web/projects/[id]/settings.tsx` | Retire a project | `PATCH /v1/projects/{id}` | write | `acme project update --set status=archived` | reversible |
| Delete a project | `web/projects/[id]/settings.tsx` | Remove a project | `DELETE /v1/projects/{id}` | destructive | `acme project delete` | `--yes`, `--dry-run` |
| Show current identity | `web/account/page.tsx` | Check the target | `GET /v1/me` | read | `acme whoami` | user, org, env |
| Check credentials | `web/account/tokens.tsx` | Debug auth | `GET /v1/me` | read | `acme auth status` | `--json` |
| Log in | `web/login/page.tsx` | Set up a machine | `POST /v1/auth/token` | write | `acme auth login` | `--token`, `--device` |
| Log out | `web/account/tokens.tsx` | Remove a credential | local | destructive | `acme auth logout` | local only |
| Read config | `web/account/settings.tsx` | Inspect context | local | read | `acme config get/list` | sources shown |
| Write config | `web/account/settings.tsx` | Set staging | local | write | `acme config set` | 0600 |
| Load the command tree | n/a | Agent onboarding | local | read | `acme schema` | no network |
| Shell completions | n/a | Human ergonomics | local | read | `acme completion` | no network |

Coverage: 19 rows, 19 commands. 100%.

## Gaps

| Capability | Why it has no command |
|---|---|
| Bulk delete | No documented API; UI loops client-side. Not built. |
| Project activity log | UI reads a private websocket, no documented endpoint. |
| Organization billing | Separate internal service, not in this API. |
| OAuth browser callback | Deliberately unsupported; device flow covers humans. |
| Keychain storage | Config file at 0600 ships first; keychain is a follow-up. |
| `doctor` | P1, deferred to 1.0. Recorded in the roadmap. |
| Update check | P1, deferred to 1.0. |

## API capability inventory

| Capability | Finding | Consequence |
|---|---|---|
| Pagination | Cursor (`cursor`, `limit`, max 200) | one adapter, `--all` capped at 10,000 |
| Idempotency | `Idempotency-Key`, 24h TTL | create always sends a key |
| Async jobs | none | M26 is N/A (cite this row) |
| Retries | `Retry-After` on 429 | retry reads twice; writes only with a key |
| Versioning | `X-API-Version` header | pinned, `--api-version` overrides |
| Tenancy | org from token; `org` query optional | `--org` override, never guessed |
| Rate limits | per token, 429 with `Retry-After` | backoff, bulk cap |
| Files | none | M44 is N/A (cite this row) |

## Command tree

```
acme auth login|logout|status
acme config get|set|list|unset
acme project list|get|create|update|delete
acme whoami
acme version
acme completion bash|zsh|fish
acme schema
acme help
```

## Output convention

- Keys: `snake_case`, inherited from the API.
- Timestamps: RFC 3339 UTC with `Z`.
- IDs: opaque strings, `prj_` prefix is not parsed.
- Money: not part of this surface.
- Lists: `{"data", "has_more", "next_cursor", "truncated"}`.
- Errors: JSON on stderr with `code`, `message`, `hint`, `status`, `request_id`,
  `retryable`, and `target`.

## Exit codes

0 success, 1 unexpected, 2 usage, 3 auth, 4 forbidden, 5 not found, 6 conflict
or validation, 7 rate limit/server, 8 network/timeout, 9 partial success,
10 confirmation, 11 ambiguous target, 12 diagnostic, 130 interrupted.

## Safety classes

| Command | Class | Guard |
|---|---|---|
| `project list/get` | read | none, `--yes` ignored |
| `project create/update` | write | `--dry-run`, idempotency key |
| `project delete` | destructive | TTY prompt, `--yes` off TTY, `--dry-run` |
| `config set/unset` | write | local file, 0600 |
| `auth logout` | destructive | local credential only |

## Auth precedence

`--token` → `ACME_TOKEN` / `ACME_API_KEY` → user config → keychain (follow-up).
Project config holds context only and never credentials.

## Open gaps and exceptions

- Keychain is not implemented; user config at 0600 is the credential store.
  Written exception for M29.
- `doctor` and update checks are P1 and not shipped in this template.
- No `--insecure`; private CAs use `--cacert` when the client adds it.

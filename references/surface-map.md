# Surface map: inventory the product before writing commands

The surface map is the design record and the coverage contract. It goes in
`CLI.md` at the repo root before command code exists.

## 1. Read in this order

1. **UI navigation and screens.** Every screen and menu action is a capability.
   Look for buttons, row menus, bulk actions, filters, and empty states.
2. **Route definitions or OpenAPI/GraphQL schema.** Map each UI action to the
   call it makes. Match `operationId` when OpenAPI exists.
3. **The official SDK or the internal API client in the repo.** It already
   knows auth, pagination, and error shapes. Reuse that knowledge; match its
   language.
4. **Docs, changelog, and support macros.** They name jobs the UI hides.

Do not start from endpoints. Endpoint-shaped commands are unguessable.

## 2. One row per user job

Two jobs may share an endpoint and still need two commands. "List projects" and
"find a project by name" are different jobs even when both hit `GET /projects`.

```md
| Capability | Source | User job | API call | Class | Command | Notes |
|---|---|---|---|---|---|---|
| List projects | `web/projects/page.tsx` | Find a project | `GET /v1/projects` | read | `acme project list` | cursor |
| Search projects | `web/projects/page.tsx` | Find by text | `GET /v1/projects?search=` | read | `acme project list --search` | server-side |
| Create project | `web/projects/new.tsx` | Start a project | `POST /v1/projects` | write | `acme project create` | idempotency key |
| Delete project | `web/projects/[id]/settings.tsx` | Remove a project | `DELETE /v1/projects/{id}` | destructive | `acme project delete` | needs `--yes` |
| Read logs | `web/deploys/[id]/logs.tsx` | Debug a deploy | `GET /v1/deploys/{id}/logs` | read | `acme deploy logs` | stream |
```

Rules:

- **Every row cites a source.** A UI file, a route, or an OpenAPI `operationId`.
  A row without a source is a guess.
- **Class every row.** `read`, `write`, or `destructive`. Destructive means data
  can be lost: delete, revoke, cancel, rotate, bulk update.
- **Every row names one command.** If a job has no command, it is a gap, not a
  blank cell.
- **One command per job, not per endpoint.**

## 3. Coverage

```
coverage = rows with a command / total rows
```

- Target: at least 90% before implementation starts.
- A small product usually has 15 or more rows. A typical SaaS has 25 or more.
- If the map has fewer, write one line explaining why the product is small.
- Never invent rows to hit a number.
- Gaps count in the denominator but not the numerator until a documented
  alternative covers them.

Mark each row `done` only when its command passes the per-command checks.

## 4. Gaps

A gap is a UI capability with no documented, token-accessible API. Options:

1. Use a documented endpoint that covers the job.
2. Leave the capability out with a note.
3. Ask the product team to expose it.

Never scrape the UI, reuse a session cookie, or call a private endpoint. Record
the gap in `CLI.md` and in the report to the product team.

```md
| Capability | Source | Why no command |
|---|---|---|
| Export report | `web/reports/page.tsx` | Private `/api/reports/export`; no documented alternative. |
```

## 5. API capability inventory

Record what the API supports before designing flags. Do not assume a mechanism
because a competitor has one.

| Capability | Question | If unsupported |
|---|---|---|
| Pagination | Cursor or offset? Max page size? | Build the adapter, cap `--all` |
| Idempotency | Key header? TTL? Scope? | No automatic retry of writes; warn in help |
| Async jobs | Job resource? Status enum? Poll endpoint? | Sync commands only, no `--wait` |
| Retries | `Retry-After`? Safe methods? | Retry reads only, back off |
| Versioning | Header, date, or path? | Pin one version, record it |
| Tenancy | Org or project in path, header, or token? | Resolve context, require explicit scope |
| Rate limits | Per key, org, or endpoint? Burst? | Conservative concurrency, bulk cap |
| Files | Upload and download endpoints? | Omit the capability or stream to disk |

These answers drive flags, retries, exit codes, and what counts as N/A.
Unsupported capabilities are what make M23, M26, and M44 N/A; nothing else.

## 6. Existing CLI

Choose one path in `CLI.md` before writing code:

| Path | Use when |
|---|---|
| Adopt | Existing CLI covers the surface and passes most MUST rules |
| Extend | It works for some commands and the shape can be copied |
| Rebuild | It is unmaintainable, or its contract cannot be fixed without breaking users |

Default: **extend**. Keep working command names and flags. Bring them to
conformance command by command. Rename only through a one-minor deprecation
window. A rebuild throws away user muscle memory and must be justified in
writing.

## 7. Definition of ready

Fill every line in `CLI.md` before writing command code. A missing answer is a
blocked condition, not an invitation to guess.

- [ ] Tool name and binary name, checked against the package registry and `PATH`.
- [ ] Repo language, package manager, and build command.
- [ ] API style (REST, GraphQL), base URLs, API version header.
- [ ] Auth method and a non-TTY path to a token.
- [ ] Surface map at 90% coverage, gaps listed, every row cited.
- [ ] Existing CLI path: adopt, extend, or rebuild.
- [ ] API capability inventory filled.
- [ ] Command tree that fits on one screen.
- [ ] Output convention: key case, timestamp format, ID type, money units.
- [ ] Safety class for every write.
- [ ] The first vertical slice, named explicitly.

Suggested `CLI.md` skeleton:

```md
# CLI design record — acme

## Decisions
| Question | Answer |
|---|---|
| Tool / binary | |
| Language / build | |
| API style / base URLs | |
| API version | |
| Auth | |
| Existing CLI path | |
| First vertical slice | |

## Surface map
...

## Gaps
...

## API capability inventory
...

## Command tree
...

## Output convention
...

## Exit codes
...

## Safety classes
...

## Open gaps and exceptions
...
```

## 8. Output conventions

Decide once and write it down:

- Key case: one convention per tool, inherited from the API (`snake_case` is
  common). Never mix.
- Timestamps: RFC 3339 in UTC with `Z`.
- IDs: opaque strings, even when numeric.
- Money: integer minor units, and the key names the unit (`amount_cents`).
- Arrays: always arrays; empty is `[]`, never `null`.
- Missing values: key present, value `null`.

## 9. Blocked conditions

Stop and report when:

- A primary job needs a capability with no documented API and no alternative.
- Auth cannot complete without a browser and there is no token or device flow.
- The API does not document what a destructive call removes or cascades to.
- A name can match several resources, the API allows duplicates, and no ID path exists.
- Rate limits make a bulk command unsafe without a product decision.

The report names the missing input, the safe commands to build now, and the
smallest decision needed.

## 10. Common mistakes

- Mapping endpoints instead of jobs.
- Counting a private endpoint as covered.
- Leaving gaps out of the denominator.
- Starting implementation with two rows still unanswered.
- Choosing a language the repo does not use.
- Forgetting to record the output convention, then mixing cases across commands.

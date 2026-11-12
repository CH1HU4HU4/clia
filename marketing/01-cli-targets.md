# CLIA target list: open-source SaaS without a CLI

Status: research complete, 2026-11-12
Goal: find products with a documented HTTP API, a real user base, and no
official CLI. Build the CLI, hand over the source, ask for one credit line.

---

## 1. The offer

We build and ship a complete CLI for the product: command tree, auth, `--json`,
exit codes, tests, CI, docs, release artifact. We give them the source.

They give us one line in the CLI documentation:

```
Built by CLIA — https://cliaskill.vercel.app
```

No fee, no telemetry, no lock-in, no shared IP. They can fork, rename, or
relicense it. We keep the right to list the project in our portfolio.

**Why they say yes.** Their users are already building the CLI for them. In the
last year the strongest open-source SaaS products shipped official CLIs. The
ones that have not are leaving the interface to single-maintainer community
projects and MCP servers. This is free engineering for a gap they already know
about.

**Why we do it.** Distribution. Every install, README, and docs page is a CLIA
proof artifact. The CLI is the demo.

---

## 2. Why now: the 2026 CLI wave

Verified on npm, GitHub, and project docs, 2026-11-12:

| Product | CLI | Latest | Date |
|---|---|---|---|
| Chatwoot | `chatwoot/cli` (Go, MIT) | v0.7.0 | 2026-09-25 |
| Twenty | `twenty` | v2.57.0 | 2026-11-09 |
| DocuSeal | `docuseal` | v1.0.6 | 2026-10-01 |
| Postiz | `postiz` | v2.0.27 | 2026-10-30 |
| Metabase | `@metabase/cli` | v0.5.16 | 2026-11-11 |
| Teable | `@teable/cli` | v0.6.52 | 2026-11-12 |
| Meilisearch | `@meilisearch/cli` | v0.4.0 | 2026-11-07 |
| Langfuse | `langfuse-cli` | v1.3.1 | 2026-11-03 |
| Immich | `packages/cli` | in-repo | active |
| Actual Budget | `packages/cli` | in-repo | active |

Chatwoot is the clearest signal. It started its CLI in January 2026, shipped an
agent skill with it, and now documents `chatwoot conv 123 reply "thanks"` as a
first-class workflow. That is the CLIA playbook, already in production.

The window is not closed. It is closing per product.

---

## 3. How a target qualified

Four checks. A product only qualified if all four were negative, or the only
CLI was stale or community-owned.

1. **Repo scan.** No `cli/`, `apps/cli`, `packages/cli`, or client commands in
   `cmd/`. Installer and server binaries do not count.
2. **Registry scan.** No official package with a `bin` entry on npm or PyPI.
   `npm view <scope>/cli`, `pip index versions <name>-cli`.
3. **Org scan.** No `<product>-cli` repository under the vendor's org.
4. **Docs scan.** No CLI page in the product documentation.

Demand was measured separately: community CLI stars, MCP packages, and
"agent-ready" forks. Those are evidence users want the interface, not evidence
the vendor ships it.

---

## 4. Scoreboard

Score is out of 100. Weights:

| Dimension | Max | What it measures |
|---|---|---|
| API surface | 25 | Documented endpoints and whether they cover real jobs |
| CLI gap | 20 | No official CLI (20), community only (18-19), stale official (10) |
| Distribution | 20 | Hosted tier, community size, agent relevance |
| Maintainer fit | 15 | Contribution path, responsiveness, team size |
| CLI leverage | 20 | How much a CLI improves the core job |

| # | Product | Repo | Stars | Hosted | Auth | Existing CLI | Score |
|---|---|---|---|---|---|---|---|
| 1 | NocoDB | `nocodb/nocodb` | 65.5k | Yes | `xc-token` | community 12★ | **93** |
| 2 | Baserow | `baserow/baserow` | 6.3k | Yes | JWT / DB token | community PyPI | **90** |
| 3 | Plane | `makeplane/plane` | 62.3k | Yes | `X-API-Key` | community 32★ + ops CLI | **88** |
| 4 | Listmonk | `knadh/listmonk` | 24.3k | No | Basic / token | none | **85** |
| 5 | Invoice Ninja | `invoiceninja/invoiceninja` | 10.6k | Yes | `X-API-TOKEN` | community 1★ | **83** |
| 6 | Paperless-ngx | `paperless-ngx/paperless-ngx` | 48.0k | No | Token | 3 community CLIs | **80** |
| 7 | Outline | `outline/outline` | 41.2k | Yes | Bearer / OAuth | community | **79** |
| 8 | Shlink | `shlinkio/shlink` | 5.4k | No | `X-Api-Key` | server CLI + TODO repo | **78** |
| 9 | Typesense | `typesense/typesense` | 27.1k | Yes | API key | community 17★ (2023) | **77** |
| 10 | Dub | `dubinc/dub.link` | 25.2k | Yes | Bearer | community 0.0.13 | **76** |
| 11 | Formbricks | `formbricks/formbricks` | 13.2k | Yes | API key | none | **72** |
| 12 | Plausible | `plausible/analytics` | 29.8k | Yes | Bearer | community 1★ | **72** |
| 13 | Docmost | `docmost/docmost` | 22.3k | Yes | unclear | community 14★ | **71** |
| 14 | Umami | `umami-software/umami` | 40.1k | Yes | API key | official, abandoned 2022 | **67** |
| 15 | Ghostfolio | `ghostfolio/ghostfolio` | 9.7k | No | Token | none | **66** |

Component scores:

| Product | API | Gap | Dist | Maint | Leverage |
|---|---|---|---|---|---|
| NocoDB | 24 | 19 | 20 | 11 | 19 |
| Baserow | 25 | 19 | 14 | 13 | 19 |
| Plane | 20 | 18 | 19 | 13 | 18 |
| Listmonk | 21 | 19 | 12 | 13 | 20 |
| Invoice Ninja | 22 | 19 | 14 | 11 | 17 |
| Paperless-ngx | 20 | 16 | 13 | 12 | 19 |
| Outline | 19 | 18 | 16 | 10 | 16 |
| Shlink | 18 | 20 | 11 | 12 | 17 |
| Typesense | 19 | 17 | 16 | 10 | 15 |
| Dub | 16 | 17 | 17 | 11 | 15 |
| Formbricks | 14 | 19 | 13 | 12 | 14 |
| Plausible | 12 | 19 | 17 | 12 | 12 |
| Docmost | 13 | 17 | 13 | 11 | 17 |
| Umami | 15 | 10 | 17 | 12 | 13 |
| Ghostfolio | 15 | 19 | 9 | 10 | 13 |

---

## 5. First wave: build these three

### 5.1 Baserow — the showcase

**What.** Open-source Airtable alternative. Django + Vue, MIT core, cloud and
self-hosted. Their README claims 150,000 users.

**API.** REST with JWT user auth and scoped database tokens. Their live schema
at `https://api.baserow.io/api/schema.json` exposes **350 paths**. That is the
largest documented surface on this list and the best possible CLIA demo.

**Gap.** No official CLI. One community Python package, `baserow-cli` v0.1.1,
by a single developer, two releases. `baserow-mcp` exists inside the Baserow
org with 3 stars.

**Jobs the CLI wins.**
- `baserow rows import <table> --csv data.csv --batch 500`
- `baserow table export <table> --format csv --json`
- `baserow schema diff <table> --from schema.json`
- `baserow fields list <table> --json`
- `baserow files upload <file> --json`

**Angle.** "350 endpoints, no CLI. We mapped every one, built the 20 jobs that
cover 90% of usage, and ran it against a conformance gate. It is yours."

**Risk.** Smaller GitHub audience than NocoDB. The 350-path surface means the
surface map is real work, which is exactly the point.

### 5.2 Listmonk — the quick win

**What.** High-performance self-hosted newsletter and mailing-list manager.
Go, single binary, PostgreSQL. 24k stars, one lead maintainer.

**API.** REST with BasicAuth or `Authorization: token`. Subscribers, lists,
campaigns, templates, media, transactional mail, bounces.

**Gap.** The `listmonk` binary installs and upgrades the server; it does not
manage content from a remote machine. Community CLI has 3 stars. An MCP server
exists, which confirms agent demand.

**Jobs the CLI wins.**
- `listmonk subscribers import --list 3 --csv subs.csv`
- `listmonk campaign create --list 3 --template 2 --subject "..." --dry-run`
- `listmonk campaign send <id> --yes`
- `listmonk subscribers export --list 3 --json`
- `listmonk tx send --to ... --template 2`

**Angle.** "Your binary installs the server. Your users still cannot import
40,000 subscribers or send a campaign from CI. Here is the client."

**Risk.** Single maintainer with strong opinions. No hosted tier, so the win is
credibility, not reach. The ask should be a separate MIT repo plus a docs link,
not a merge into core.

### 5.3 Plane — the big swing

**What.** Open-source Jira/Linear alternative. 62k stars, AGPL, cloud.

**API.** REST with `X-API-Key`. Projects, work items, cycles, modules, pages,
comments, states, labels.

**Gap.** Plane ships **Prime CLI** for deploying self-hosted instances, and an
official **MCP server** with 360 stars. Neither is a client CLI. A community
`plane-cli` has 32 stars and is actively maintained.

**Jobs the CLI wins.**
- `plane issues list --project ENG --state "In Progress" --json`
- `plane issues import --project ENG --csv backlog.csv`
- `plane issues bulk-update --query "label:stale" --state Backlog --dry-run`
- `plane cycles list --project ENG --json`
- `plane export --project ENG --format md`

**Angle.** "You shipped an MCP server so agents can read Plane. Teams still
cannot script Plane in CI. The CLI is the other half: deterministic, pipeable,
versioned."

**Risk.** Large team may have a CLI on the roadmap. AGPL means any upstreamed
code inherits it. Lead with the standalone repo and offer to transfer.

---

## 6. Second wave: warm, not first

### NocoDB — biggest logo, most friction

65.5k stars, cloud + self-host, `xc-token` auth, official MCP docs. No client
CLI; the org's `nc-cli` is a one-commit app scaffolder. Community
`stagware/nocodb-cli` has 12 stars.

Jobs: `base export`, `records import --csv`, `schema diff`, `views list`,
`webhooks`, `files upload`. Angle: schema-as-code and CSV pipelines.

Friction: source-available license, large org, and they already invested in
MCP. Pitch the CLI as the CI layer under the MCP, not a replacement.

### Invoice Ninja — finance ops

10.6k stars, hosted, Elastic License 2.0, `X-API-TOKEN`. Huge v5 API: clients,
invoices, quotes, payments, expenses, projects, tasks, recurring, reports, bulk
actions. Community CLI has 1 star.

Jobs: `clients import`, `invoice create --from-json`, `recurring run`,
`payments reconcile`, `reports ar`. Angle: month-end close in one command.

Friction: ELv2; maintainers may see a CLI as support burden.

### Paperless-ngx — demand is proven

48k stars, GPL-3, self-hosted. Token auth. Three community CLIs at 57, 38, and
23 stars, plus an "AI agent ready" fork. No official CLI.

Jobs: `documents import --watch`, `tag apply --query`, `export`, `tasks wait`.
Angle: "Three CLIs exist. None is yours. Here is the one that passes a gate."

Friction: no hosted tier; maintainers may prefer the community projects.

### Outline — docs as code

41.2k stars, hosted, BSL 1.1, Bearer + OAuth, OpenAPI-complete. Community npm
and PyPI clients, no official CLI.

Jobs: `docs export --format md`, `docs import`, `search`, `collections list`.
Angle: backups and docs-as-code for teams that live in the terminal.

Friction: no CONTRIBUTING.md; BSL; they may not accept external feature PRs.

### Shlink — the TODO story

5.4k stars, MIT, self-hosted, `X-Api-Key`. The server binary can manage short
URLs on the host. The org's `shlink-cli` repo has said
`[TO DO] A standalone CLI tool to interact with Shlink's API` since 2022.

Jobs: `short-url create`, `visits`, `tags`, `domains`, `import`.
Angle: "You wrote the TODO in 2022. We shipped it."

Friction: the server CLI already covers the jobs locally; the gap is remote and
agent use. Be precise about that or the pitch looks uninformed.

### Typesense — maintenance play

27.1k stars, GPL-3, hosted cloud, API key. Community CLI from 2023 has 17 stars
and no recent release.

Jobs: `collections`, `documents import`, `aliases`, `keys`, `cluster health`.
Angle: "The community CLI stopped in 2023. Here is a maintained one."

Friction: official clients are good; CLI value is mostly bulk import and ops.

---

## 7. Watchlist: verify before pitching

| Product | Why it is not first | What to check |
|---|---|---|
| Formbricks | API v2 is beta; management surface unclear | Confirm documented endpoints beyond survey display |
| Plausible | Stats + site provisioning only; narrow | Confirm write surface for goals/sites |
| Docmost | API docs 404 at the obvious URLs | Find documented API; otherwise CLIA stop condition |
| Umami | Official CLI exists but abandoned since 2022 | Ask if they want it revived or replaced |
| Dub | Community CLI exists; smaller API surface | Confirm link/analytics surface and hosted demand |
| Ghostfolio | Self-hosted, small audience | Confirm API token path and bulk jobs |

---

## 8. Do not pitch: they already shipped a CLI

Pitching these wastes the one shot. Dates verified 2026-11-12.

| Product | CLI | Evidence |
|---|---|---|
| Chatwoot | `chatwoot/cli` | Go, MIT, v0.7.0, agent skill |
| Twenty | `twenty` | v2.57.0, official |
| DocuSeal | `docuseal` | v1.0.6, official |
| Postiz | `postiz` | v2.0.27, official |
| Metabase | `@metabase/cli` | v0.5.16 |
| Teable | `@teable/cli` | v0.6.52 |
| Meilisearch | `@meilisearch/cli` | v0.4.0 |
| Langfuse | `langfuse-cli` | v1.3.1 |
| Immich | `packages/cli` | in-repo |
| Actual Budget | `packages/cli` | in-repo |
| Hoppscotch | `@hoppscotch/cli` | v0.31.4 |
| Cal.com, Novu, Directus, Strapi, Ghost, Supabase, Appwrite | official CLIs | registry and docs |

Note the pattern: the products that shipped one are the ones with agent-heavy
audiences. That is the same audience CLIA sells to.

---

## 9. Outreach playbook

**Step 1: proposal issue, not a PR.**
Open one issue with the command tree, three copy-paste examples, and one
question: "Do you want this upstream, or as a separate repo you link to?"
Do not attach a 5,000-line diff.

**Step 2: build in public.**
Repo `<product>-cli` under our org, MIT, with the credit line in the README.
Ship `--help`, one live read command, and `--json` before asking for a review.

**Step 3: the 60-second demo.**
`--help` with real examples, `auth status --json`, `list --limit 5 --json`,
one write with `--dry-run`, one destructive command returning exit 10 with
stdin closed. That is the whole pitch.

**Step 4: hand over.**
Offer repo transfer or a PR. Include the conformance report and CI. Keep no
private dependency.

**Step 5: ask for the line.**
One sentence in the CLI docs page or README, plus a changelog mention. No logo,
no command output attribution, no `--help` spam. Users punish that.

**Credit line, exact:**

```
Built by CLIA — https://cliaskill.vercel.app
```

**If upstreamed:**

```
Originally built by CLIA — https://cliaskill.vercel.app
```

### Objections

| Objection | Response |
|---|---|
| "We are building our own" | "Compare surface maps first. Ours is done. Take it or take the checklist." |
| "We do not want a binary" | "We match your repo language: Go, Python, or TypeScript." |
| "Who maintains it?" | "We do, for 12 months. Then we transfer it." |
| "Why free?" | "The credit line is the payment. You keep the code." |
| "Legal will not approve" | "Start as a separate MIT repo. No CLA, no merge." |

### Pre-outreach checklist

- [ ] No `cli/`, `packages/cli`, or client commands in the repo.
- [ ] No official npm/PyPI package with a `bin` entry.
- [ ] No `<product>-cli` repo in the vendor org.
- [ ] No CLI page in the docs.
- [ ] Token auth works headless; no browser-only flow.
- [ ] Every command maps to a documented endpoint.
- [ ] CONTRIBUTING, CLA, and issue templates read.
- [ ] Sandbox: cloud trial or self-host container.
- [ ] License checked for client distribution and contribution.

---

## 10. Next 7 days

| Day | Action |
|---|---|
| 1 | Re-verify the top three with the checklist. Open sandbox accounts. |
| 2 | Write the Baserow `CLI.md` surface map from the 350-path schema. |
| 3 | Ship the Baserow vertical slice: `auth status`, `rows list`, `--json`. |
| 4 | Open the Baserow proposal issue with the slice and five examples. |
| 5 | Start Listmonk: one-command subscriber import and campaign dry-run. |
| 6 | Start Plane: `issues list` and `issues import` against a sandbox. |
| 7 | Review responses. Pick the first yes. Publish the build log. |

**Success metric for 90 days:** three accepted CLIs, one maintainer post or
changelog mention, 10,000 installs, five inbound "build us one" requests.

---

## 11. Assumptions to test

1. Vendors will accept a CLI built outside their repo. Chatwoot built in-house,
   so the outside-contributor model is unproven.
2. A credit line in docs is enough distribution. If not, ask for a changelog
   entry and a social post instead.
3. Community CLI demand predicts vendor appetite. The counter-case is Paperless:
   three community CLIs may mean the maintainers deliberately left it alone.
4. The CLI is still the right interface now that MCP exists. The honest pitch is
   complement, not replacement: MCP for interactive agents, CLI for CI and
   deterministic automation.

Test assumption 1 with Baserow first. It has the smallest org, the clearest gap,
and the most impressive surface to show.

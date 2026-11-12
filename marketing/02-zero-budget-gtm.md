# Zero-budget alternatives to "build their CLI"

Status: options, 2026-11-12
Constraint: no ad spend, no sponsorships, no bounties, no paid directories.
The real budget is hours per vendor. Every model below is judged on that.

---

## The constraint, stated honestly

The build-their-CLI model costs 3-5 days per vendor and ends in a binary
yes/no. It is bespoke labor sold for a credit line. At zero budget that is the
worst shape of work: high cost per shot, no compounding, and permission from a
gatekeeper before anything ships.

Any alternative worth doing must do at least one of these:

1. Make one unit of work serve many vendors.
2. Remove the vendor's permission from the loop.
3. Shrink the ask from "take our codebase" to "read this."

The six models below are ordered by how well they do that.

---

## Model A: The CLI Gap Index

**Thesis.** Turn the target research into a public, living directory. Every
product with no CLI is a lead. Every vendor wants to move from "none" to
"official."

**What we ship.** A single page: product, category, stars, API, auth, CLI
status (official / community / stale / none), and a link to the docs. Filter by
"no CLI." Update monthly.

Start with the 36 products already checked. Add a "suggest a product" form.

**The ask.** Nothing. Vendors find themselves listed and email us.

**Why $0.** The research exists. The page is static HTML on the existing Vercel
project. No outreach required.

**First signal.** A vendor asks to be moved from "none" to "in progress," or a
user submits a correction.

**Risk.** Maintenance. A stale index loses trust. Date every row and publish a
corrections policy.

**Effort.** 1 day to publish, 2 hours a month to maintain.

**Why it compounds.** It owns the query `<product> CLI` for every product on
the list. That is the exact search a product manager runs when they start
thinking about a CLI.

---

## Model B: The conformance scorecard

**Thesis.** Do not build the CLI. Grade the ones that exist. The checker is the
moat; the scorecard is the proof.

**What we ship.** Run `scripts/conformance` against 10 CLIs:

- Baselines: `gh`, `stripe`, `vercel`, `flyctl`, `supabase`.
- 2026 wave: Chatwoot, Metabase, Teable, Postiz, DocuSeal, Langfuse, Meilisearch.

Publish one page per CLI: pass/fail by P0 rule, the exact command that failed,
and what it breaks for an agent. Headline: "We audited 11 SaaS CLIs. Seven
would strand an agent."

**The ask.** "Want a free re-audit after fixes?" That is a reply, not a
contract. The badge is optional and always links to the method.

**Why $0.** The checker and the mock API already exist. No vendor code, no
permission, no sandbox.

**First signal.** A vendor replies publicly or fixes one rule. That is a warm
conversation with a technical buyer, opened by evidence instead of a pitch.

**Risk.** Tone. Audit products that just shipped a CLI, lead with what passes,
give a right of reply, and offer the fix as a PR. Never publish a score without
the reproduction command.

**Effort.** 2 days for the first 6, then 2 hours per CLI.

**Why it compounds.** Every audit is also a teardown post, a sales artifact,
and a benchmark for the guidelines. One run, three outputs.

---

## Model C: Starter templates and a CI action

**Thesis.** Give away the first hour. Let developers generate a CLI that already
passes the gate, then let the template do the marketing.

**What we ship.**

- `create-clia-cli` for TypeScript, `pipx run clia-starter` for Python, and a
  `go run` starter. All three pass every P0 check out of the box.
- A GitHub Action: `uses: CH1HU4HU4/clia@v1` runs the checker on every push.
- Generated README carries one line: `Built with CLIA`.

**The ask.** None. Install is the ask.

**Why $0.** The three templates already pass the eval suite. Packaging is the
only work.

**First signal.** A stranger opens an issue on the template, or a repo shows the
action in `.github/workflows`.

**Risk.** Templates are a crowded shelf. The differentiator is the gate: most
starters give you structure, this one gives you a pass/fail contract.

**Effort.** 2 days to package, 1 hour a month.

**Why it compounds.** Every generated CLI is a CLIA artifact in someone else's
repo. The attribution line travels without us.

---

## Model D: Teardown content

**Thesis.** Own the phrase "agent-ready CLI" by showing the failures, not
claiming the standard.

**What we ship.** One teardown a week, 900-1,200 words: the CLI, its score, three
concrete diffs, and the agent failure each one causes. Cross-post to the repo,
dev.to, Hacker News, r/selfhosted, and the vendor's Discord.

Target queries: `<product> CLI`, `CLI for AI agents`, `SaaS CLI design`,
`why my CLI hangs in CI`.

**The ask.** Try the checker. Subscribe. Reply with a CLI to audit.

**Why $0.** Writing. The audits from Model B are the raw material.

**First signal.** Organic search traffic to a long-tail product query, or a
maintainer sharing the post.

**Risk.** Slow. Content compounds after 8-12 pieces, not 2. Do not start unless
we can hold the weekly cadence for a quarter.

**Effort.** 4 hours per piece once the audit exists.

**Why it compounds.** It builds the only durable asset in dev tools: a
reputation for a specific, useful judgment.

---

## Model E: The slice PR

**Thesis.** Keep the original model but shrink the unit of work from a full CLI
to a 200-line proof.

**What we ship.** One vertical slice: `auth status` plus one `list --json`
command, wired to the real API, with the surface-map issue attached. No full
command tree, no release, no CI.

Open one issue: "Here is the first command and the map for the rest. Want the
other 19?"

**The ask.** A yes/no on the remaining work, not adoption of a codebase.

**Why $0.** Hours instead of days. Five shots a week instead of one.

**First signal.** A maintainer says "yes, open the PR" or "no, we are doing it
ourselves." Both are useful and fast.

**Risk.** Still permission-dependent, and a slice can look like a stunt if it
does not hit the real API. It must run against a sandbox or a live instance.

**Effort.** 3-4 hours per target.

**Why it compounds.** It produces a portfolio of live proofs and a list of
vendors who said no and why. That list is worth more than another cold email.

---

## Model F: The unofficial CLI

**Thesis.** Build for the users, not the vendor. If adoption is loud enough,
the vendor adopts it or links it.

**What we ship.** One CLI for a product with proven demand and no official
client: Paperless-ngx (three community CLIs), Typesense (stale community CLI),
or NocoDB (one 12-star community CLI). MIT, our org, clear "unofficial"
disclaimer, no logo.

**The ask.** Nothing at first. Later: "link it, or take it over."

**Why $0.** No permission, no CLA, no vendor schedule.

**First signal.** Users install it and open issues. A maintainer mentions it in
a thread.

**Risk.** Trademark and support. Use the product name only descriptively, never
the logo, and put "unofficial" in the first line of the README. Budget support
time or the goodwill turns.

**Effort.** 5-7 days for the first one, then maintenance.

**Why it compounds.** It is the only model that creates real users before
asking anyone for anything. Chatwoot's official CLI is the counter-example:
vendors can and will build their own. Speed matters.

---

## Comparison

| Model | Work per shot | Needs vendor permission | Compounding | Time to first signal | Main risk |
|---|---|---|---|---|---|
| A. Gap Index | 1 day, then 2h/mo | No | High | 2-6 weeks | Staleness |
| B. Scorecard | 2 days for 6 | No | High | 1-3 weeks | Tone |
| C. Templates | 2 days | No | Medium | 2-8 weeks | Crowded shelf |
| D. Teardowns | 4h each | No | High, slow | 8-12 weeks | Cadence |
| E. Slice PR | 3-4h per target | Yes | Low | 3-10 days | Looks like a stunt |
| F. Unofficial CLI | 5-7 days | No | Medium | 2-6 weeks | Support, trademark |

The original model, for comparison: 3-5 days per vendor, permission required,
no compounding, and a single yes/no at the end.

---

## Recommended portfolio

Do not run six. Run two, plus one always-on.

**Primary: A + B as one property.**
The Gap Index is the directory. The Scorecard is the proof. Together they are
"the state of SaaS CLIs," updated monthly. This is the inbound engine: vendors
find themselves listed, read a score, and ask how to fix it.

**Secondary: E, at five targets a week.**
The slice PR is the outbound arm. It uses the same surface map and produces a
live proof in hours. It feeds the index with "in progress" rows.

**Always-on: C.**
Templates and the CI action are table stakes. Ship once, forget, let installs
accumulate.

**Experiment: F, one product only.**
Pick the one with the loudest demand (Paperless). If it gets 500 installs in 60
days, the model works. If not, stop.

**Hold: D.**
Start teardowns only if A and B produce enough audits to write from. Otherwise
it becomes a second job with no distribution.

---

## 30-day plan

| Week | Ship | Output |
|---|---|---|
| 1 | CLI Gap Index v1 with the 36 checked products | A public page, a correction form, and 15 "no CLI" rows |
| 2 | Conformance scorecard on 6 CLIs | 6 public reports, 3 vendor replies |
| 3 | `create-clia-cli` + GitHub Action | 3 starters, 1 marketplace listing |
| 4 | 10 slice PRs from the index | 10 live proofs, 2 yes, 8 documented noes |

Metrics to watch: index pageviews, vendor replies, audit requests, starter
installs, slice-PR acceptance rate. Revenue is not a 30-day metric. Inbound
conversations are.

---

## What not to do at zero budget

- **Paid ads.** A $200 test buys noise in a category with no search volume yet.
- **Conference sponsorships and swag.** Cash for attention, the opposite of the
  constraint.
- **Cold email at volume.** Deliverability costs money and the pitch is weaker
  than a public audit.
- **Building full CLIs for ten vendors.** Five days each, ten yes/no bets, no
  reusable asset.
- **A badge without a published method.** Authority is borrowed, not declared.
  Publish the rules and the reproductions first.

---

## The strategic bet

The original model sells labor. These alternatives sell judgment.

Labor does not scale at zero budget and depends on a gatekeeper. Judgment
scales: one audit serves the vendor, the content, the benchmark, and the next
sales call. The checker is the only asset here that gets more valuable every
time someone runs it.

If only one thing ships this month, ship the scorecard. It turns the 2026 CLI
wave from a threat into a stage.

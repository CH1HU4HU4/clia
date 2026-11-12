# Outreach system (zero budget)

Status: playbook, 2026-11-12
Rule: mass-market the audit. Hand-sell the build.

---

## Audience: four roles, two funnels

The deal and the product have different buyers. Do not mix the channels.

| Funnel | Buyer | Consideration | Channels |
|---|---|---|---|
| A. Vendor deal: we build, they adopt, they credit | Founder or product lead | High, 1:1 | Direct email, X, HN, warm intro |
| B. Product adoption: developers use the skill | Engineer or technical founder | Low, self-serve | Reddit, HN, skill directories, GitHub |

Inside funnel A there are three roles:

| Role | Cares about | Message |
|---|---|---|
| Founder / CEO | Distribution, competitive parity, agent readiness | "Agents cannot use your product. We will build the CLI free." |
| Product / DevRel | DX, docs, adoption | "Surface map, command tree, conformance report." |
| Engineer | Stack match, tests, CI | "Here is the slice; it passes the gate." |

Reddit is funnel B. It validates the CLI and creates user demand. It does not
close the vendor deal. The vendor list is about 50 companies; email them
directly.

---

## The split

| Offer | Consideration | Channel | Volume |
|---|---|---|---|
| Free audit / index row | Low | Email, Reddit, HN | 25/day, 1 broadcast |
| "Let us build your CLI" | High | Reply thread, call | 3-5/week, hand-written |

Trying to mass the second one converts worse than targeted sends and burns the
domain. The audit is the lead magnet. The build is the close.

---

## Channel limits at $0

| Channel | Safe volume | Real reply rate | What kills you |
|---|---|---|---|
| Cold email | 25/day, warmed inbox | 8-12% with a data hook | New domain, links in email 1, 500/day |
| GitHub issues | 5-10/day, human-written | High | Templated issues = spam report |
| Reddit | 1 post per sub, per week | Broadcast | Self-promo rules, cross-posting |
| X DMs | ~10/day | Low | DMs closed, bulk = ban |
| LinkedIn | ~20 requests/week | Medium | Automation = restriction |
| Discord/Slack | 1 post per community, ask mods | High | Cross-posting = ban |
| HN | 1 post | Thousands of views | One bad post burns the account |

---

## Email: the 25/day system

**List.** From the index. One row per target: repo, maintainer handle, public
contact, missing-CLI evidence, one command their users need.

**Send.** 25/day, 5 days/week. Plain text. No images, no tracking pixel, no link
in the first sentence. Gmail from a warmed account. 125/week, 500/month.

**Three touches, 12 days.** Every touch is a gift, not a pitch.

### Touch 1 — day 0

Subject: `[Product] on the CLI gap index`

> Hi [name] — I run CLIA, a conformance checker for agent-ready CLIs. I put
> [product] on the CLI Gap Index: [link]. It has a solid API and no client CLI,
> so [specific job] still takes a script per team. If it's useful, I'll send the
> audit for [product] — six rules, no ask.

### Touch 2 — day 4

Subject: `Audit: [product]`

> Here's the audit: [link]. Two rules would strand an agent in CI: [M07, no
> `--json`] and [M13, prompts on a TTY]. Both are one-line fixes. Want the diff?

### Touch 3 — day 10

Subject: `Close the loop on [product]`

> Last note from me. Do you want the slice PR (`auth status` +
> `[resource] list --json`), or should I mark [product] as "building in-house"
> on the index? Either is fine — I'll stop either way.

The easy no is the point. It gets replies and keeps the list clean.

**Compliance footer on every send:**

> You're receiving this because [email] is published in [repo]'s commit history.
> Reply "stop" and I will not contact you again. [Name], [postal address].

No purchased lists. No scraped emails. No automation tools. Human review of
every send.

---

## Reddit

Reddit is a validation and demand channel, not the vendor-deal channel. It
reaches the engineers who will implement the CLI and the users who will ask for
it. The founder is reachable on X, HN, and email.

One good post per subreddit beats fifty DMs, and DMs get you banned. Keep Reddit
to one post a week and one hour of comments a day.

### Where

| Subreddit | Angle | Fit |
|---|---|---|
| r/selfhosted | The CLI gap in self-hosted tools | Best. Listmonk, Paperless, Shlink, Ghostfolio, NocoDB |
| r/commandline | CLI design teardown, exit codes, `--json` | Highest intent, smaller |
| r/devops | Non-TTY behavior, CI, exit-code maps | Medium |
| r/opensource | Contributing a CLI upstream, the credit model | Medium |
| r/SaaS | The build-for-credit experiment itself | Founders, not users |
| r/LocalLLaMA, r/AI_Agents | "Your MCP server is not a CLI" | High engagement, spicy |
| r/homelab | Adjacent to selfhosted | Medium |
| r/programming | Too strict, no promo | Skip |

### The post that works

Original research, with the data in the post. Not a product announcement.

**Title bank:**

- "I checked 36 open-source SaaS products for a CLI. 15 still don't have one."
- "I ran an agent-readiness check on 12 CLIs. 9 fail."
- "Your MCP server is not a CLI"
- "The CLI gap in self-hosted software"
- "I audited Chatwoot's new CLI. Here's what it gets right."

**Body shape:** method, the table, two surprises, one ask for corrections. Link
at the bottom, not the top. If the value is behind the link, the post dies. If
the post is the artifact, it lives.

### Rules that matter

- Read the sidebar and the self-promo thread before posting.
- Disclose authorship in the first line.
- Text post, not a link post.
- One subreddit per day. Never cross-post identical text.
- Reply to every comment for the first two hours.
- No vote manipulation, no alt accounts, no "DM me."
- Account needs history. Comment for a week before posting anything.

### The evergreen play

Search Reddit for the exact pain: "NocoDB CLI", "Paperless CLI", "Baserow
command line", "Listmonk import". Reply to threads from the last 12 months with
a real answer, no link. Those threads rank in Google for years. This is the
highest-intent, lowest-risk Reddit work, and it never stops.

### Honest expectations

- r/selfhosted hit: 30-80k views, 100-300 upvotes, 30-80 comments, 500-2,000
  site visits, 1-3 maintainer conversations.
- r/commandline: 5-15k views, 100-400 visits, the best technical feedback.
- r/SaaS: founder critique, zero users.
- Direct installs are low. Social proof and discovery are high.

Reddit's real output is not signups. It is a list of which products people
actually want CLIs for, and a warm "saw your post" opener with maintainers.

---

## Founder channels

The vendor list is about 50 companies. That is small enough to hand-sell.

1. **Direct email.** The primary channel. Find the founder or product lead in
   the repo, the company site, or the commit history. One specific paragraph,
   one demo link.
2. **X build-in-public.** OSS founders live on X. Post the slice, the surface
   map, and the before/after. Tag the product, not the person's personal handle,
   unless they engage first.
3. **Show HN.** One post, framed as a build, not a product launch.
4. **Warm intro.** Investors, accelerators, and maintainers of adjacent projects.
   A one-line intro beats a cold email every time.
5. **Founder communities.** r/SaaS, Indie Hackers, and founder Slacks are for
   feedback on the offer, not for reaching the founders of 60k-star projects.
   Use them to sharpen the pitch, not to find leads.

The message for a founder is not the message for an engineer:

> Agents do not use dashboards. Your competitors shipped a CLI in 2026. Yours
> is missing. We will build it free, you keep the code, one line of credit.

---

## Broadcast

One Show HN post: "I audited 12 SaaS CLIs for agent-friendliness. Nine would
strand an agent." It reaches more maintainers in a day than 500 emails, costs
$0, and does not touch deliverability. The index page is the landing.

Same content, rewritten per community:

- HN: the audit and the method.
- Reddit: the gap in self-hosted tools.
- X: one chart, one claim, one link.
- LinkedIn: the vendor angle, "your API has no CLI."

---

## Metrics

| Week | Measure |
|---|---|
| 1 | 15 Reddit comments, 125 emails sent, 0 posts |
| 2 | Index live, 1 r/selfhosted post, 10 replies |
| 3 | 1 r/commandline post, 2 vendor calls |
| 4 | 1 Show HN, 10 slice PRs, 2 yes |

Track: replies, positive replies, audits delivered, slice PRs accepted. Not
opens. Opens are vanity without a pixel.

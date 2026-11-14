# Reddit promo subs: where "I built this" is the point

Status: research, 2026-11-12
Premise: these subs buy reach, not demand. Use them as a launch amplifier after
the topic-sub plays in `04-reddit-targets.md`. They will not replace them.

---

## 1. Worth posting

| # | Sub | Size | What it is for | CLIA fit | Rule to respect |
|---|---|---|---|---|---|
| 1 | **r/SideProject** | ~848K | The default place to share a side project and get feedback | Reach. Broad audience, mostly builders and lurkers | Self-promo is tolerated, but pure links are ignored. Tell the story and ask a real question. |
| 2 | **r/coolgithubprojects** | ~50K | GitHub projects, browsed by developers | Best-qualified audience on this list | Use the **Self Promotion** flair; keep it reasonable. A repo link and a short why. |
| 3 | **r/IMadeThis** | ~45-60K | Explicitly for showing things you made | Best acceptance rate. Story-driven | Self-promotion is welcome. Lead with why you made it, not the feature list. |
| 4 | **r/alphaandbetausers** | ~47-72K | Founders looking for early users and feedback | Good for "run the checker, tell me what breaks" | Self-promo welcome; **post flair required** before posting. |
| 5 | **r/LaunchMyStartup** | ~10K | Launch announcements and early feedback | Small, but the post is on-topic by definition | Launch framing; expect feedback, not traffic. |
| 6 | **r/github** | Very large | GitHub ecosystem discussion | One comment in the weekly self-promotion megathread | Self-promo is **only** allowed in the megathread. A standalone post is removed. |
| 7 | **r/buildinpublic** | ~30K+ | Build logs and transparent numbers | Good for the "what the checker caught" story | Self-promo is conditional. It has to be a log, not an announcement. |

### Low-intent, use once
- **r/startups_promotion** (~42K): a pure promo feed. Easy post, almost no qualified traffic.
- **r/PlugYourProduct**: same. A link dump.
- **r/MVPLaunch**: small launch sub. Fine as a checkbox; not a channel.
- **r/roastmystartup** (~36K): feedback, not promotion. Useful if you want honest criticism of the positioning, not users.
- **r/ProductHunters**: only relevant if you actually launch on Product Hunt.

---

## 2. Avoid

| Sub | Why |
|---|---|
| **r/opensource** | Banned AI-made and AI-focused projects in October 2026. New rules also require a project to be at least a year old with 3+ contributors. CLIA trips all three. Posting there is a removal and a reputation hit. |
| **r/selfpromotion** | It is an adult-content creator sub. Wrong room entirely. |
| **r/shamelessplug** | Restricted or dead depending on the week. No reliable audience. |
| **r/SaaS** | One mention per 60 days, and that includes comments and links. Do not spend it on a launch post. |
| **r/commandline** | A focus group for CLI design, not a promotion channel. |

---

## 3. A launch sequence that does not look like spam

| Day | Sub | Post |
|---|---|---|
| 0 | r/coolgithubprojects | Repo + one-paragraph why + the Self Promotion flair. "I built a conformance checker for CLIs that coding agents generate." |
| 0 | r/IMadeThis | Same artifact, different story: why you made it and what broke first. No identical title. |
| 1 | r/SideProject | "I checked the CLI my agent built. It failed five ways." Story + what the gate catches. |
| 2 | r/alphaandbetausers | "Free checker for your SaaS CLI. Run it, paste the failures, I'll tell you what they break." Flair on. |
| 3 | r/github | One comment in the weekly self-promotion megathread. |
| 7 | r/buildinpublic | Numbers: repo visits, checker runs, installs, what the posts produced. |
| 14 | — | Kill anything that produced no repo visit. Do not repeat it. |

Space the posts. Do not put the same link in five subs on the same day; that is
the pattern moderators remove and accounts get flagged for.

---

## 4. Post shape

**Title:** the outcome, not the product.

- Good: "I checked 11 SaaS CLIs for agent use. Seven would strand an agent."
- Good: "The CLI my coding agent built passed the demo and failed the first agent."
- Bad: "Introducing CLIA — build a CLI for your SaaS with AI."

**Body:**
1. What you built and why, in two sentences.
2. One concrete failure it catches, with the exact command and the agent consequence.
3. One command the reader can run.
4. Ask for a specific reaction: "Run it on your CLI and tell me which rule is wrong."
5. Repo link at the end. Disclose: "I built this."

**In promo subs, the artifact is the post. The product is the footnote.**

---

## 5. What to expect

| Sub | What you get | What you do not get |
|---|---|---|
| r/SideProject | Reach, a few hundred visitors, occasional feedback | Qualified SaaS founders |
| r/coolgithubprojects | The best-qualified clicks on this list | Volume |
| r/IMadeThis | Sympathy upvotes and some developers | Buyers |
| r/alphaandbetausers | Testers and reciprocal feedback | Retention |
| r/github megathread | A backlink and slow search traffic | A spike |

Measure repo visits and `conformance` runs, not upvotes. A post with 40 upvotes
and 12 checker runs beats one with 400 upvotes and none.

---

## 6. The honest note

These subs are where you announce. They are not where the problem is felt.

The conversion still comes from r/ClaudeCode ("my CLI doesn't work in CI"),
r/microsaas ("do I need a CLI?"), r/AI_Agents ("CLI or MCP?"), and r/LLMDevs
("how should agents connect to my app?"). If you only have five posts in you this
month, spend three there and two here.

# Product Hunt launch copy

Status: drafts, 2026-11-12
Product: CLIA
Product URL: https://cliaskill.vercel.app
Repo: https://github.com/CH1HU4HU4/clia
Pricing: Free, MIT, open source

Before submitting: the Product Hunt MCP server is not connected in this session.
Log in through the Product Hunt connection, then re-read the composer limits,
topic picks, and launch-day availability. Character counts below use the
standard limits (name 40, tagline 60, description 500). Confirm them before
pasting.

---

## Name

CLIA

Alternates, only if the plain name is taken:

- CLIA by Omer
- CLIA Skill
- CLI Anything

The product is named CLIA everywhere else. Keep it.

## Tagline (60 max)

Recommended:

> Give your SaaS a CLI that AI agents can run

Other options:

> An agent skill that builds your SaaS CLI
> Your product has an API. Agents need a command.
> Build the CLI your AI agent keeps asking for
> Turn your SaaS into commands an agent can run

Pick the recommended one. It names the buyer, the artifact, and the user.

## Description (500 max)

Primary:

> CLIA is a skill for Claude Code, Codex, and OpenCode. Point it at your SaaS repo and it builds a real CLI: the commands that cover your product, stable `--json`, exit codes, zero prompts, and dry runs before deletes. It maps the surface first, then proves the build with a conformance checker. TypeScript, Go, and Python templates. Free and MIT.

Short version, for directories with a tighter cap:

> An agent skill that builds a real CLI for your SaaS: full command coverage, stable `--json`, exit codes, no prompts, dry runs before deletes. Maps the surface first, then proves it with a conformance checker. Free and MIT.

## First comment (maker comment)

This is the copy that decides the launch. Post it as the first comment, not in
the description box.

> Hi Product Hunt. I'm Omer.
>
> I kept watching the same failure. An agent builds a SaaS in a weekend. The product ships with a clean dashboard and a working API. Then you ask the agent to use that product and it has nothing to hold. It opens a browser, guesses at endpoints, or gives up.
>
> Agents run commands. That is the interface they know. The fix is a command line.
>
> Building one an agent can trust is the hard part. Most SaaS CLIs wrap the easy endpoints and leave the rest to curl. Login opens a browser. Output is a table. A delete asks for confirmation on a terminal that does not exist.
>
> CLIA is a skill for Claude Code, Codex, and OpenCode. Point it at your repo. It reads the product surface, maps every user job to a command, and scaffolds from a template that matches your language: TypeScript, Go, or Python.
>
> The rules are the part I care about most. Every data command supports `--json` with one stable shape. Every failure gets an exit code that names the cause. Nothing prompts when stdin is closed. Writes take `--dry-run`. Destructive commands need `--yes` off a TTY. Help text carries real examples, defaults, and env fallbacks, so an agent can finish a job without reading your source.
>
> A conformance checker runs the built CLI and grades every rule by ID. All three templates pass every P0 check. One eval fixture ships five seeded bugs, and the checker has to catch every one before the suite passes.
>
> CLIA is free, MIT, and open source. No signup.
>
> If you built a product with AI and want an agent to use it, install the skill and run it on your repo. Tell me what breaks. I learn more from the gaps than from the wins.

## Topics and categories

Primary picks:

- Developer Tools
- Artificial Intelligence
- Open Source

Backups if a slot is taken or the picker disagrees:

- SaaS
- Productivity
- Command Line

Open source goes first if the form asks for one label. It is the least
contested claim and the most credible.

## Product facts for the form

- Pricing: Free
- Product state: New
- Open source: yes
- Solo maker: yes
- Website: https://cliaskill.vercel.app
- GitHub: https://github.com/CH1HU4HU4/clia
- X handle: leave blank unless there is one that posts

## Gallery captions

Six slides, 1270x760. Each caption stays under 140 characters.

1. Your product has an API. Agents need a command.
2. CLIA maps every user job to a command before it writes code.
3. Stable `--json`, real exit codes, zero prompts.
4. Every write supports `--dry-run`. Every delete needs `--yes`.
5. A checker grades every rule by ID and fails the build.
6. One install prompt, then `/clia build a CLI for this repo`.

Slide notes for the designer:

- Slide 1: the tagline over the terminal, logo small in the corner.
- Slide 2: a two-column surface map with three rows filled.
- Slide 3: one command, one JSON response, one exit code.
- Slide 4: a delete command with `--dry-run` output and the target echoed.
- Slide 5: checker output with rule IDs and pass marks.
- Slide 6: the install prompt from the landing page, copy button visible.

## Promo

Skip it. The product is free. A promo code on a free product reads as noise.

## X launch post

> Your SaaS has a dashboard and an API. Agents can use neither.
>
> CLIA is a skill for Claude Code, Codex, and OpenCode that builds the CLI in between.
>
> Free, MIT, live on Product Hunt today: [link]

Thread, if the post gets traction:

> 2/ The skill maps the product surface first. Every user job gets a command, a risk class, and an API call. Gaps get written down instead of guessed at.
>
> 3/ Then it holds the build to a contract: `--json` on every data command, exit codes that name the failure, no prompts when stdin is closed, `--dry-run` on writes.
>
> 4/ A conformance checker runs the finished CLI and grades every rule by ID. The templates pass. The eval fixture with five seeded bugs has to fail.
>
> 5/ Install the skill, point your agent at your repo, run `/clia build a CLI for this repo`. Tell me what breaks: [link]

## LinkedIn post

> Agents can build a SaaS in a weekend. Using that product is still manual work.
>
> A dashboard needs eyes. An API needs a client. Neither gives an agent something it can run, retry, and check.
>
> CLIA is a skill for Claude Code, Codex, and OpenCode. Point it at your repo and it builds a product CLI: the commands that cover the real jobs, stable JSON, real exit codes, no prompts, and a dry run before anything gets deleted.
>
> Free and open source. Launching on Product Hunt today.
>
> If you ship with AI, install it on one repo and tell me where it fails. [link]

## Direct messages and email to supporters

Send this to people who use the product or asked about it. Do not ask
for upvotes. Ask for a test and a comment.

> CLIA is live on Product Hunt today: [link]
>
> If you have five minutes, install it on a repo and tell me what breaks. A comment with one real failure helps more than an upvote.

Follow-up for people who ask what to do:

> Install prompt is on the site. It adds the skill to your agent's skills folder. Then run `/clia build a CLI for this repo` and paste the first error you hit.

## Reply templates for launch-day comments

**"How is this different from an MCP server?"**

> MCP exposes tools to a model. CLIA builds a command line the agent can run, pipe, retry, and check in CI. Most teams need the command first, and the command works with any model. The skill is CLI-only for now.

**"Does it work with my stack?"**

> Templates ship for TypeScript, Go, and Python, and the skill matches the language in your repo. For anything else, the guidelines still hold and the agent writes the CLI by hand.

**"Why not use curl?"**

> curl works when a person writes each call. An agent needs command names, stable JSON, exit codes, and help text it can read. That turns a one-off request into a tool it can reuse.

**"My API is not documented."**

> The skill stops and records the gap instead of inventing endpoints. You get a list of what agents cannot reach yet, which is useful before you promise agent access.

**"What stops an agent from deleting my data?"**

> Destructive commands require `--yes` off a TTY, take `--dry-run`, and echo the target before they act. Bulk deletes need explicit confirmation.

**"Is it free?"**

> Free, MIT, no signup. Repo: https://github.com/CH1HU4HU4/clia

**"Does it work with Cursor?"**

> It targets harnesses with folder-based skills: OpenCode, Claude Code, and Codex. Cursor support depends on how you load skills there.

**"How long does a CLI take?"**

> The first working command lands in under 30 minutes on a fixture repo. A full surface depends on your API. The skill builds one command at a time and keeps the tree working.

## Shoutouts

Only send these for products you use. Ratings are public.

- Claude Code, 5: "The harness I built the first CLIA templates against."
- OpenCode, 5: "Where the skill runs today. Folder skills and shell access in one place."
- T3 Code, 5: "Where CLIA was written."

Remove any shoutout you cannot stand behind in public.

## Launch-day checklist

- 12:01 AM Pacific: launch is live. Post the first comment within five minutes.
- 12:10 AM: X post, then the thread.
- 12:30 AM: LinkedIn post.
- Morning: send the direct messages in small batches, not one blast.
- Reply to every comment within 30 minutes for the first six hours.
- After 6 PM Pacific: post one build note with the best question from the day.
- Next morning: send the same note to everyone who commented.

## What to measure

- Comments with a real product or a real failure. This is the only signal that matters.
- Installs from the site, measured by GitHub referral traffic.
- Replies that turn into a repo to test.

Upvotes are a scoreboard. Comments are the product research.

# Reddit targets: solo founders building with AI

Status: research, 2026-11-12
Scope: funnel B (skill adoption), not the vendor deal. Per `03-outreach-system.md`,
Reddit validates the CLI and creates user demand; it does not close a vendor.

---

## 1. The wedge, stated correctly

CLIA is not "a CLI builder" on Reddit. It is the answer to two questions people
are already asking:

1. **"Should my SaaS have a CLI or an MCP?"** — demand.
2. **"Why does the CLI my coding agent built fail in CI?"** — product.

Most founder subs have question 1. Most agent subs have question 2. Market in the
founder subs with the proof from the agent subs.

Do not lead with "I built CLIA." Lead with the decision table or the failure
teardown. The repo is the second comment, after the post has earned a reply.

---

## 2. Ranked list

Rank is fit × evidence × posting tolerance. "Evidence" links are real threads,
not category guesses.

| # | Sub | Who is there | Evidence the problem is live | Promo reality | First play |
|---|---|---|---|---|---|
| 1 | **r/microsaas** (~218K) | Solo and tiny-team SaaS founders, many non-technical | ["Is a CLI useful for running micro SaaS?"](https://reddit.com/r/microsaas/comments/1wbibfk/is_a_cli_useful_for_running_micro_saas/) — 24 upvotes, 21 comments; "I added an MCP server to my analytics micro SaaS"; "Your MCP server's README is a landing page" | Moderate. No low-effort self-promo; backstory, stack, and a lesson are the price of entry. Mods are actively enforcing in 2026. | Answer the CLI question with a decision table: when a micro-SaaS needs a CLI, an MCP, or neither. Then a standalone post with the same table. |
| 2 | **r/indiehackers** (~194K) | Indie founders, build-in-public crowd | ["Vibe coding a social media SaaS? We built an MCP server and a CLI so Claude can check your work"](https://www.reddit.com/r/indiehackers/comments/1udibld/vibe_coding_a_social_media_saas_we_built_an_mcp/); ["Day 101 building Vigil — CLI and agent skills"](https://www.reddit.com/r/indiehackers/comments/1wuw70z/day_101_building_vigil_in_public/) | Strict. Naked promo dies; a build log with numbers survives. | "My CLI passed my demo and failed my first agent." Walk the five failure modes: prompt, no `--json`, truncation, wrong exit, token leak. |
| 3 | **r/AI_Agents** | Agent builders, technical founders, some hobbyists | ["Skill + CLI or MCP"](https://www.reddit.com/r/AI_Agents/comments/1wh0ckp/skill_cli_or_mcp/) — 27 comments; ["The Truth About MCP vs CLI"](https://www.reddit.com/r/AI_Agents/comments/1rjtp3q/the_truth_about_mcp_vs_cli/); ["For those having exposed both MCP and CLI..."](https://www.reddit.com/r/AI_Agents/comments/1t8a4t6/for_those_having_exposed_both_mcp_and_cli_should/) | Assume strict. This sub rewards a real comparison, not a launch. | Comment in the live decision threads first. Then one data post: same product exposed as API, MCP, and CLI; token, latency, CI reliability. |
| 4 | **r/LLMDevs** | Technical builders shipping agent products | ["MCP vs API vs CLI: How Should AI Agents Connect to Your App"](https://www.reddit.com/r/LLMDevs/comments/1xp9b3j/mcp_vs_api_vs_cli_how_should_ai_agents_connect_to/); ["CLI vs MCP is a false choice"](https://www.reddit.com/r/LLMDevs/comments/1s69pdx/cli_vs_mcp_is_a_false_choice_why_cant_we_have_both/) | Unknown but technical; link-drops are ignored. | The missing third option: "You have neither. Here is the order to build them in." Attach the surface map, not the skill. |
| 5 | **r/ClaudeCode** | Claude Code users shipping tools, skills, and CLIs | ["I made a Linear CLI tool for AI Agents"](https://www.reddit.com/r/ClaudeCode/comments/1qu103k/i_made_a_linear_cli_tool_for_ai_agents/); ["Plugin+Skills to use ANY CLI agent"](https://www.reddit.com/r/ClaudeCode/comments/1swj1bb/pluginskills_to_use_any_cli_agent_in_claude_code/); "Built a SQL Server CLI with query whitelisting" | Crowded with "I built a skill" posts. Differentiation is the gate, not the skill. | Show a generated CLI failing the checker, then the exact diff that fixes it. CLIA is the skill behind the diff. |
| 6 | **r/vibecoding** (~370K) | Solo founders and non-engineers building with AI | ["Solo founder pushed to prod — CLI roadmap 17 tickets deep"](https://www.reddit.com/r/vibecoding/comments/1snhdaa/solo_founder_pushed_to_prod_today_heres_what_i/); "MCP vs API vs CLI: I built all 3 for agents" | Low-effort link drops are removed. Quality and learning first; self-promo second. | Founder story: "I shipped the app, forgot the interface my users' agents needed." No link in the post. |
| 7 | **r/SaaS** | Largest founder pool, broad skill level | ["More and more SaaS is headed towards API keys & MCP connectors"](https://www.reddit.com/r/SaaS/comments/1xqx7gx/how_would_you_charge_peruse_for_a_web_app_that/); MCP as a launch checkbox in recent launches | Restricted. Promotion belongs in designated threads, roughly one mention per 60 days. | Comments and weekly threads only. Never a launch post. The reach is real; the tolerance is not. |
| 8 | **r/SideProject** | Solo builders launching constantly | ["A random signup on my SaaS... I'd also consider building a CLI. Agents..."](https://www.reddit.com/r/SideProject/comments/1xrex8x/a_random_signup_on_my_saas_just_gave_me_an_idea_i/); ["3 years trying to build SaaS — MCP, CLI, Tunnels... to justify the..."](https://www.reddit.com/r/SideProject/comments/1t92g0i/3_years_trying_to_build_saas_what_worked_what/) | Launch-friendly, high noise, low average sophistication. | Build log with numbers: installs, time saved, what the gate caught. |
| 9 | **r/mcp** | MCP-native builders and tool authors | ["CLI > MCP?"](https://www.reddit.com/r/mcp/comments/1o8w5wq/cli_mcp/); ["MCP Is up to 32× More Expensive Than CLI"](https://www.reddit.com/r/mcp/comments/1rr31ee/mcp_is_up_to_32_more_expensive_than_cli/); "I built a tool that converts MCP servers into CLI + Skill files" | The audience is MCP-first. A "CLI is better" post reads as a fight. | Comment with data only. Disclose. Frame CLI as the layer under MCP, not the replacement. |
| 10 | **r/StartupSoloFounder** | Small, exact solo-founder audience | ["SaaS isn't dead in the 18 industries AI agents still can't reach"](https://www.reddit.com/r/StartupSoloFounder/comments/1xqgzrm/saas_isnt_dead_in_the_18_industries_ai_agents/) — the agent-access gap in vertical SaaS | Low volume, low promo tolerance. | The vertical-SaaS angle: "Your buyer's agent cannot reach your product. That is the moat and the gap." |
| 11 | **r/ClaudeAI** | Huge, broad Claude audience | ["MCP vs API vs CLI — How Should AI Agents Connect to Your App?"](https://www.reddit.com/r/ClaudeAI/comments/1xnkv6c/mcp_vs_api_vs_cli_how_should_ai_agents_connect_to/); ["I'm not building apps anymore, I'm building CLIs"](https://www.reddit.com/r/ClaudeAI/comments/1xchv9v/im_not_building_apps_anymore_im_building_clis/); "How do you decide between MCP and CLI for your agents?" | Very noisy. Only a strong teardown gets through. | Use only after the r/ClaudeCode post works. Cross-post the teardown, not the announcement. |
| 12 | **r/selfhosted** | Self-hosters, CLI-gap demand | ["Is there no comprehensive forgejo/gitea CLI?"](https://www.reddit.com/r/selfhosted/comments/1t1ze40/is_there_no_comprehensive_forgejogitea_cli/) | New-project megathreads; promo confined there. | Not a CLIA target. Use it for the CLI Gap Index and the unofficial-CLI model. Different buyer. |

---

## 3. Skip or test later

| Sub | Why not first |
|---|---|
| **r/commandline** | CLI enthusiasts and critics, not founders with a product gap. They will review the tool; they will not adopt the skill. |
| **r/cursor** | People consuming CLI agents. The product-side pain is thin. A CLI-orchestrator angle is the only test worth running. |
| **r/ChatGPTCoding** | Same: agent users, not SaaS builders. Has a weekly self-promo thread, so the reach is cheap but the intent is low. |
| **r/startups** (~2.1M) | Large but non-technical, promo-strict, and the problem is not native there. Wrong room. |

---

## 4. First 14 days

| Day | Action | Sub |
|---|---|---|
| 1 | Comment in the live "Is a CLI useful for running micro SaaS?" thread. Decision table, no link. | r/microsaas |
| 2 | Comment in "Skill + CLI or MCP" and "For those having exposed both..." with the same table, adapted. | r/AI_Agents |
| 3 | Standalone post: "When a micro-SaaS actually needs a CLI (and when it doesn't)." Link in the comments. | r/microsaas |
| 5 | Build story: "My CLI passed my demo and failed my first agent." Five failure modes from `evals/`. | r/indiehackers |
| 7 | Decision matrix: "You have an API and no CLI. Build in this order." | r/LLMDevs |
| 9 | Teardown: generated CLI, failing checker output, fixed diff. | r/ClaudeCode |
| 11 | Founder story: "I shipped the app, forgot the interface." | r/vibecoding |
| 13 | Answer the API-keys-and-MCP thread. No link. | r/SaaS |
| 14 | Review: which post produced a repo visit, a skill install, or a substantive reply. Kill the rest. | — |

One post per sub, per week. Do not cross-post the same title. Do not put the
same link in more than one sub in a day.

---

## 5. The only three formats that fit

1. **Decision table** — CLI vs MCP vs API-only, by product shape. Works in
   r/microsaas, r/SideProject, r/SaaS, r/AI_Agents, r/LLMDevs.
2. **Failure teardown** — generated CLI, the exact command that fails, the agent
   consequence, the diff. Works in r/ClaudeCode, r/vibecoding, r/indiehackers.
3. **Build log** — numbers, what broke, what the gate caught. Works in
   r/indiehackers, r/SideProject, r/vibecoding.

Anything else is an ad. The skill is the CTA, never the headline.

---

## 6. Rules to respect

- **Sitewide:** 90/10 participation. One product mention per thread, at most.
- **r/SaaS:** promotion is confined; treat it as comments and designated threads.
  The 2M reach is not worth a ban.
- **r/microsaas:** the value test is explicit. Backstory, stack, revenue, or a
  specific lesson. A link alone is removed.
- **r/indiehackers:** strict. The story has to stand without the product.
- **r/vibecoding:** low-effort promo removed. Put the learning in the post.
- **r/mcp:** disclose the position. CLI-vs-MCP is a religious argument there;
  bring numbers, not a verdict.
- **Everywhere:** read the current sticky before posting. Rules changed in 2026
  in at least r/vibecoding and r/microsaas.

---

## 7. What not to do

- Do not post "I built CLIA" in r/SaaS. It is the fastest way to lose the account.
- Do not argue "CLI > MCP" in r/mcp. You will win the thread and lose the room.
- Do not use the vendor offer ("we will build your CLI free") on Reddit. That is
  the email funnel, and it reads as an ad in every founder sub.
- Do not target r/commandline as a market. It is a focus group, not a channel.
- Do not cross-post the same link to six subs on day one. That is the pattern
  moderators ban for.

---

## 8. Assumptions to test

1. r/microsaas CLI curiosity converts to installs, not just upvotes.
2. r/AI_Agents readers are building products, not only comparing tools.
3. r/ClaudeCode still tolerates skill posts when the artifact is a teardown
   rather than an announcement.
4. A decision table outperforms a build story in founder subs; the reverse is
   true in agent subs.

If 1 and 4 hold, double down on r/microsaas and turn the table into the CLIA
landing-page lead magnet. If 2 holds, r/AI_Agents becomes the demand-proof
channel for the vendor email list.

# Grantmother concept and sponsor matrix

Excerpt from the hackathon ideation notes, 2026-10-19. This is a proposal, not evidence of completed integrations. Story figures are illustrative. The comparison matrix is preserved for context.

## 4. Concept C — Grantmother (grant co-op for tiny nonprofits)

### The company
Grantmother is a grant office that small nonprofits share. It interviews the founder, finds funders whose giving matches, drafts the letter of inquiry and budget, checks every sentence against what the founder actually said, and stops at a human signature. It charges per matched funder and a success tier, with a sliding scale for the smallest orgs.

### Agent jobs (6)
1. **Interviewer** — the avatar conducts a voice intake interview; produces the fact sheet the whole company is bound to.
2. **Funder Scout** — finds foundations and program officers with matching giving history; capped, cost-visible lookups.
3. **Fit Checker** — eligibility (geography, budget size, 501(c)(3) status, deadlines); ranks the shortlist; flags where a human must decide.
4. **Writer** — drafts LOI/proposal sections from the fact sheet and funder profile.
5. **Auditor** — on a different model from the Writer; marks every claim as "said in intake," "from documents," or "unsupported," and blocks unsupported claims.
6. **Treasurer/Ops** — budget table from the org's spreadsheet, deadline calendar, reminders, metering and billing.

Human in the loop: the founder approves the fact sheet, picks funders, approves wiki learnings, and signs. Nothing is sent to a funder by the system.

### End-to-end user journey
A founder of a small school-mental-health nonprofit opens a room. The avatar interviews them for five minutes; the fact sheet appears and the founder corrects two lines. Funder Scout returns eight foundations with program officers and recent grants in the area; Fit Checker cuts three for budget-size rules and flags two "human decides" items. Writer drafts an LOI for the top funder. Auditor flags one sentence ("serves 2,000 students") as unsupported; the founder changes it to the number they actually said. Treasurer builds the budget table from the uploaded sheet and sets the deadline reminders. The founder approves one learning ("funder X prefers outcomes framed as counselor hours") into the shared wiki. Billing meters two funder matches.

**Inputs:** voice interview, org documents/budget sheet, funder data, deadlines. **Outputs:** fact sheet, ranked funder shortlist with human-decision flags, audited LOI draft, budget table, deadline calendar, wiki learnings, metered invoice.

### 90-second storyboard
- 0–15 s: Founder speaks to the avatar: "We put counselors in three schools; we need $40k for a fourth." Fact sheet fills in live.
- 15–30 s: Funder Scout posts eight funders in the room with "12 lookups, [actual metered cost]" and program officer names; Fit Checker strikes three with reasons.
- 30–50 s: Writer's draft appears paragraph by paragraph. Auditor (different model) highlights one sentence red: "unsupported: 2,000 students; intake said 600." Founder edits.
- 50–65 s: Treasurer's budget table and the deadline calendar; the reminder email lands.
- 65–80 s: The learning box proposes one durable fact; the founder clicks approve; the wiki updates and the next funder's draft adapts.
- 80–90 s: Flexprice ledger: "2 funder matches metered; success tier pending." Tagline: "A grant office that refuses to lie."

### Minimum demo and expansion
**Smallest slice:** text intake (voice stretch), a seeded funder list (labeled), Writer + Auditor on two different models, one approved learning.

Ordered steps:
1. PromptQL project: one room, connected to a seeded "funders" sheet and the org's budget sheet; bots for Writer, Auditor, Treasurer. Ask Jacob or Laura for project credits with this problem statement.
2. Writer and Auditor on different providers via Flatkey (single key, swap base URL); the independence is a feature to say out loud.
3. Auditor rule: every claim tagged with its source; unsupported claims block the draft. This is the demo's spine.
4. Glasser: Apollo-style people/company search for program officers and foundation details; inspect endpoints and empty-result billing; cap at a few dollars; show the cost.
5. Masky: avatar Interviewer with voice; if latency is bad on stage, a pre-recorded interview plus a live text correction.
6. n8n: deadline reminders and a pipeline sheet sync; emails to self.
7. Flexprice: "funder match" meter, success-tier plan; Stripe test.
8. Ask the W: run the scoping pass at the start and show its "agent does / human decides" map as the company's governance page.
9. Build-time: Snyk (scan + Agent Scan on any skill files), Prelint reviewing PRs against a "no fabricated facts" spec, Tenki/Celesto for hosting the long-running Scout.
10. Stretch: BAND room for handoffs if PromptQL bots cannot address each other; LinqCode client portal; AdaL campaign content from the nonprofit's website; Finch listing of a "grant-readiness audit" skill.

**Seeded/mock (labeled):** the funder list if Glasser credits are not live; the nonprofit itself (do not use the real petition organizer's details without permission); Stripe test mode.
**Dependencies:** PromptQL project + credits; Flatkey key; Glasser balance; Masky credits.
**Top failure points and fallbacks:** Avatar voice fails → text intake. PromptQL bot-to-bot calls unclear → have the human tag each bot into the thread (which is what the talk demoed). Glasser returns thin funder data → seeded list, stated.

### Monetization and value
Per-match credits, a success tier on awards, and a sliding scale. Value: a $40k ask that would never have been written gets written, with unsupported claims flagged for human review; the checker can still miss errors.

### Prizes/credits touched
PromptQL prize + credits (amounts uncaptured); Glasser $100 credits Best Use; Masky $800 Best Use if the Interviewer is real; Flatkey discounted routing; Snyk score; Prelint free for hackathon teams; Tenki $300 / Celesto $5 for hosting.
**Cost drivers:** Glasser per-call cents (bounded), LLM tokens for Writer/Auditor pairs, Masky voice/video credits, nothing for Stripe test.

---

## 5. Sponsor-by-project matrix (18 rows)

Legend: **Core** = in the runtime path of the demo. **Build** = tooling used to build/ship the demo. **Stretch** = optional, after the minimum slice. **Omit** = deliberately not used, with reason. A row counts as a meaningful use only if it is Core or Build and actually wired; Stretch is not implementation or prize eligibility.

| # | Sponsor | A. Foster | B. One Night Only | C. Grantmother |
|---|---|---|---|---|
| 1 | Masky.ai | **Stretch** — avatar reads weekly package status/release notes. | **Core** — Maître d' avatar: voice booking + allergen Q&A; "log in with Masky" invite images on guests' own credits. | **Core** — avatar Interviewer; optional pitch clip; founder's own credits via login. |
| 2 | PromptQL | **Core (data)** — queries over dependents/CVE export; approved-learning wiki of project conventions. Not messaging. | **Core (data)** — guest list, costs, supplier sheet; "learnings" wiki across pop-ups. | **Core (backbone)** — rooms, bots over funder/budget sheets, learning box with human approval. |
| 3 | RocketRide | **Stretch/alternative** — triage→fix→scan pipeline as `.pipe` if BAND path fails. | **Core (backbone)** — the pop-up pipeline on the canvas; built-in Masky/n8n nodes; Cloud deploy if credits allow. | **Omit** — PromptQL is the backbone; a second orchestrator would duplicate it. |
| 4 | CelestoAI | **Core** — hosts the long-running Scout; Celesto CI on the seed repo (drop-in YAML claim unverified). | **Stretch** — host Stage Manager off laptop. | **Build** — sandbox for developing and testing the Funder Scout; runtime hosting is optional. |
| 5 | Finch | **Stretch** — publish "adopt-a-package triage" skill; integration path not established. | **Stretch** — "run a pop-up" skill listing. | **Stretch** — "grant-readiness audit" skill listing. |
| 6 | Tenki | **Core** — disposable sandbox for Fixer; PR reviewer on the fix PR. | **Build** — sandbox/CI for the app build. | **Build** — sandbox/CI. |
| 7 | LinqCode/LingCode | **Stretch** — public adopt-a-package portal (payments overlap with Flexprice). | **Core** — bookings web app with payments; no App Store path. | **Stretch** — client portal for pipeline/approvals. |
| 8 | Glasser | **Stretch** — find the ex-maintainer's current contact and dependent companies; capped; outreach human-approved. | **Core** — venues/suppliers/promoters; cost shown per lookup; cap ~$2. | **Core** — foundations/program officers; cost shown; cap a few dollars. |
| 9 | AdaL | **Build/Stretch** — second coding agent for Fixer; adoption announcement video from codebase. | **Core** — promo video/images from the event page; drafts only, no posting. | **Stretch** — campaign content from the nonprofit's website. |
| 10 | Snyk | **Core** — Warden: before/after scan, Agent Scan on skill/MCP files; App Security Score. | **Build** — scan the payments app pre-demo; score for judges. | **Build** — scan + Agent Scan; score for judges. |
| 11 | Flexprice | **Core** — priority-fix and attestation meters; sponsor ledger; Stripe test. | **Core** — per-seat meter, deposit credits, no-show credits; Stripe test. | **Core** — funder-match meter, success tier; Stripe test. |
| 12 | BAND | **Core (backbone)** — room per package; identity per agent; human steward approvals. | **Stretch** — human approval room for supplier orders. | **Stretch** — handoff/governance room if PromptQL bots can't address each other. |
| 13 | Kylon | **Omit** — would duplicate n8n for triggers and BAND for flow. | **Stretch** — host draws the close-out routine; becomes the Close-out agent. | **Stretch** — grant writer draws the intake→draft→sign process. |
| 14 | n8n | **Core** — scan/webhook trigger → room thread; release-notes email. | **Core** — reminders, supplier confirm, booking webhook. | **Core** — deadline calendar, reminders, sheet sync. |
| 15 | Paritok | **Build/Stretch** — proxy in front of Fixer for long codebase sessions; savings are claims. | **Omit** — short sessions, no measurable benefit to show. | **Stretch** — proxy for long document sessions; claims only. |
| 16 | Flatkey | **Core** — cheap model for Triage, strong for Fixer, failover. | **Build** — model per node. | **Core** — Writer and Auditor on different providers through one key; independence is the feature. |
| 17 | Prelint | **Core** — PR vs charter/ADRs; the Reviewer agent's engine. | **Build** — PRs vs pitch spec (allergen rule, no-show policy). | **Build** — PRs vs "no fabricated facts" spec. |
| 18 | Ask the W | **Build** — scope which orphans are worth adopting; where the human decides. | **Build** — the four decision points in the concept sheet. | **Core** — "agent does / human decides" map shown as the governance page. |

**Proposed sponsor coverage (Core + Build roles, not completed integrations):**

Parent review corrected the totals against the matrix. Foster counts AdaL and Paritok only for their proposed build-time roles; their stretch features are excluded.

| | Core | Build | Stretch | Omit | Meaningful (Core+Build) |
|---|---|---|---|---|---|
| A. Foster | 9 | 3 | 5 | 1 | **12** |
| B. One Night Only | 8 | 5 | 4 | 1 | **13** |
| C. Grantmother | 7 | 4 | 6 | 1 | **11** |

Realistic in one afternoon: 5–7 of each project's Core rows wired for real, the rest shown as seeded or stated as stretch. Claim only what runs.

---

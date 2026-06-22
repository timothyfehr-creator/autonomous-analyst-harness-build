# START HERE — what to do next

This is the **planning/design package** for the Analyst Harness (a private, single-user
research harness). No code exists yet, by design. Here is the exact sequence.

## Right now, before any code: Tier 0 already works

The everyday mode — **Tier 0, conversational** ([docs/CONVERSATION.md](docs/CONVERSATION.md))
— is a discipline, not software. You can use it today: ask your questions, get honestly
labeled, still-interesting answers (fact / inference / assumption / guess + a confidence word
+ one self-refute line). Most of your daily value lives here. Everything below is the
machinery for *committing* a claim when one earns it — not a prerequisite for getting answers.

## The build sequence (do these in order)

**Step 1 — Cold review (required; can't skip).**
Open a fresh **GPT 5.5 Pro** (or any *different* model / a human) session. Paste
[docs/REVIEW_PROMPT.md](docs/REVIEW_PROMPT.md) and attach the eight core docs it names. Aim
it especially at the new tier seams flagged in
[docs/REVIEW_V3_SELFPASS.md](docs/REVIEW_V3_SELFPASS.md) — F1/F2: do the objective escalation
triggers in CONVERSATION.md actually bind, or just relocate the rationalization?
*(Why required: this is a merged design and my own self-pass doesn't count — merging two
plans inherits neither one's review.)*

**Step 2 — Adjudicate.**
Log every P0/P1 the review finds into [docs/REVIEW_ADJUDICATION.md](docs/REVIEW_ADJUDICATION.md)
with a disposition. Fix the fatal ones in the docs. When **no finding is BLOCKING**, set the
header to `external_review_complete: true`, `open_p0_p1: 0`, `governance_status: READY`.

**Step 3 — Kick off the build.**
Paste [docs/START_PROMPT.md](docs/START_PROMPT.md) into **Claude Code** (or run it as an
**Ultraplan** if you've pushed this repo to GitHub). It will read everything, confirm
governance is READY, plan **Phase 0 only**, then implement **WP0.0** and stop. It will
*refuse* to build while governance is BLOCKED — that's intentional.

**Step 4 — Build one work package at a time.**
Approve each WP plan; let it implement → test → self-review → commit → stop; repeat. Follow
[AGENTS.md](AGENTS.md). **At Milestone B, pause** and ask honestly: am I actually using Tiers
1–2, or living happily in Tier 0? If the latter, that's real signal to stop before Phases
5–7 rather than build machinery you won't use (self-pass finding F5).

## File map

- `START_HERE.md` — this runbook.
- `docs/CONSTITUTION.md` — the contract; the three tiers (§1); accepted limits (§15).
- `IMPLEMENTATION_PLAN.md` — the 41-WP backlog, milestones, tier framing.
- `docs/CONVERSATION.md` — the Tier-0 default contract (use this today).
- `docs/DATA_MODEL.md` — record shapes. `docs/EXAMPLE_WORKFLOW.md` — a full Tier-2 walkthrough.
- `docs/KNOWLEDGE.md` / `docs/TOOLING.md` — baseline-fact and tooling policy.
- `AGENTS.md` / `CLAUDE.md` — build discipline and project guidance.
- `MERGE_NOTES.md` — why the design is what it is (what came from which plan).
- `docs/REVIEW_PROMPT.md` — the cold-review prompt (Step 1).
- `docs/REVIEW_V3_SELFPASS.md` — my non-independent dry review (the seams to attack).
- `docs/REVIEW_ADJUDICATION.md` — the governance gate (Step 2).
- `docs/START_PROMPT.md` — the Claude Code kickoff (Step 3).
- `docs/RED_TEAM_BRIEF.md` — adversarial brief for reviewing the constitution.
- `factbase/` — seed registries (mostly empty by design; sources.yaml seeded).
- `skills/` — fact-repository and visuals skills (phase-gated).

## The one thing to remember

A green run means the bookkeeping is coherent — never that the analysis is true. And Tier 0
exists so that staying honest never has to make your answers boring.

# MERGE_NOTES — v3 = best of two designs

v3 merges two independently-produced v2 plans for this harness: one by Claude (Opus), one
by GPT 5.5 Pro. This records the objective comparison and exactly what was taken from where,
so no decision is unattributed.

## Headline

**GPT's architecture won; Claude's operating model won.** v3 adopts GPT's data model and
constitution structure almost wholesale, and adds the one thing GPT's design structurally
lacked — a lightweight default tier — as the framing that makes all that rigor opt-in.

## What v3 took from GPT 5.5 Pro (the rigorous core)

- **Multi-axis status** (Constitution §5): Support / Dispute / Freshness / Lifecycle /
  Stability as separate fields, instead of one overloaded confidence enum. The single best
  idea in either plan; it dissolves the taxonomy-ambiguity problem.
- **The evidence chain as separate records** (§2–§3): source entity → evidence artifact →
  **claim-evidence assessment** → claim → structured observation. The assessment being its
  own record (so one artifact can support one claim and refute another, unmutated) is a
  genuine improvement over Claude's flatter evidence record.
- **Two-axis source judgment done right** (§3): scoped, dated, append-only source
  reliability (A–F) separate from relationship-specific information credibility (1–6) — the
  STANAG model Claude had deferred.
- **Structured observations** (§6.3, §12): typed values bound to claims; renderers consume
  observation IDs only, never prose. Cleanly solves "don't scrape a chart from a sentence."
- **APPEND_ONLY_HISTORY stability class** (§5): the event-ledger model (Tim's
  event-vs-state distinction), built as a first-class status.
- **Reviewer-independence as a recorded class** (§10): SAME_MODEL_FRESH_CONTEXT /
  DIFFERENT_MODEL / HUMAN / MIXED, with baseline claims requiring real independence.
- **Candidate lifecycle** (§4): a fact can be jotted as CANDIDATE without the full chain.
- **Prediction hash-chain + external anchor**, all ex-ante fields frozen (§11).
- **Utility-first milestone ordering** with clean stop points; **migration framework**;
  **closed schemas + root-envelope versioning**; the **DATA_MODEL**, **EXAMPLE_WORKFLOW**,
  **KNOWLEDGE**, **TOOLING** docs, the two **skills**, and the neutral-type **sources.yaml**
  are carried into v3 from GPT's bundle largely as-is.

GPT's self-validation was honest, not theater (it correctly left itself BLOCKED pending
external review and reported "0 scripts; design package").

## What v3 took from Claude (the operating model)

- **The three-tier rigor model** (Constitution §1) — the decisive addition. GPT treats "an
  answer" as the unit that always carries a manifest + refuter + hashes; its own example
  shows answering a trivial question takes twelve steps and a dozen records. v3 makes
  **Tier 0 — Conversational** (honest labels in prose, speculation encouraged and badged, a
  one-line self-refute, *no records/manifest/refuter*) the **default**, with GPT's heavy
  chain as opt-in escalation (Tier 1 recorded, Tier 2 committed). This is the direct fix for
  the stated goal: do not make being interesting expensive.
- **WP0.3 — the Tier-0 contract** (`docs/CONVERSATION.md`) and **Milestone 0**: the
  lightweight default is specified and delivers value on day zero, before any code.
- **§6.6 right-sizing for solo use**: information credibility and full semantic-review
  hashing are required only at Tier 2 / baseline promotion, optional at Tier 1 — so routine
  recording stays cheap enough to actually do.
- **Proportionality framing** throughout: the merge's explicit refusal of the "rigorous and
  useless" trade.

## Where each was better (objective)

| Dimension | Stronger | Why |
|---|---|---|
| Data model / evidence chain | **GPT** | Assessment-as-record; observations; multi-axis status |
| Two-axis reliability/credibility | **GPT** | Built it; Claude deferred it |
| Visuals discipline | **GPT** | Observation-bound, CRS, post-render inspection |
| Migration / governance depth | **GPT** | Full migration WP, quarantine-not-invent |
| Keeping answers useful / not strangled | **Claude** | The tier model; GPT had no lightweight path |
| Right-sizing rigor to solo use | **Claude** | GPT's default is Tier 2 for every answer |
| Concrete exploit-finding (review) | **GPT** | Built the working seed-registry exploit |

## Shared blind spots both plans had (and v3's response)

- **Abandonment risk.** Both designs are heavy enough that the real failure mode for a
  solo user is *not using the tool* and falling back to plain chat. Neither named it. v3's
  answer: Tier 0 *is* the everyday tool, so the harness stays used even when you don't want
  ceremony; the heavy tiers are there for when a claim earns them.
- **Semantic-review rubber-stamping.** Both rely on a human/different-model marking support
  `CHECKED`; that flag can be rubber-stamped, re-creating coverage-theater one level down.
  v3 keeps it (no better structural option) but lists it in accepted limitations (§15.3/.4)
  and requires real reviewer independence for baseline claims.

## Honest correction on the Claude-side prediction

Before seeing GPT's plan, Claude predicted it would be one-directionally biased toward more
rigor and blind to over-engineering. That was **partly wrong**: GPT's plan ordered work by
user value, included a candidate lifecycle, and explicitly declined to burden a private user
with publication-grade disclaimers. The prediction held only narrowly — GPT lacked a
lightweight *answer* tier — which is exactly the seam v3 adds.

## Governance state

v3 is a **new merge** and has **not** been externally reviewed. Per Constitution §14 and
`REVIEW_ADJUDICATION.md`, governance is **BLOCKED** until v3 gets its own cold review (the
two designs being merged does not transfer either's review to the merged artifact).

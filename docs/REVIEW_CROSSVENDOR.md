# Cross-vendor independent review — request & prompt (P0 surface)

**You are the independent review this project still owes itself.** The harness has been reviewed
only by the same model family that built it (a fresh-context in-harness pass — see
`docs/REVIEW_MILESTONE_A.md`). That is explicitly **not** independent. You are a *different vendor's*
model (GPT-5.5-Pro / Gemini / Claude-from-a-different-lineage) or a human reviewer. Your job is to
find where the highest-stakes controls **fail** — especially in ways a same-lineage reviewer would
share the blind spot for.

Paste this whole file as your instructions. The code is at
`https://github.com/timothyfehr-creator/autonomous-analyst-harness-build` and in the attached zip
(`analyst-harness-v3-review-*.zip`). It runs offline: `python3 -m venv .venv && .venv/bin/pip
install -r requirements-dev.txt && .venv/bin/python -m pytest` (expect 431 green) and the three
machine gates `.venv/bin/python scripts/gate_phase{1,2,3}_exit.py` (each exits 0).

## What the system is (one paragraph)

A private, single-user Russia/Ukraine research harness that makes the chain from source → evidence
→ claim → committed answer inspectable and hard to game. **Three tiers of rigor, default
lightweight:** Tier 0 conversational (honest prose labels, no records — most use), Tier 1 recorded,
Tier 2 a *committed answer* bound to exact record hashes and checked by a refuter. A passing gate
means "the recorded relationships are coherent," never "this is true." Read `docs/CONSTITUTION.md`
(the contract) and `docs/DATA_MODEL.md` (the closed schemas) first; `docs/EXAMPLE_WORKFLOW.md` is a
worked Tier-2 walkthrough.

## Scope: the P0 surface + the Phase-3 answer loop

Assume Phases 0–2 schema/records plumbing holds (it has its own gates). **Focus your attack on the
three P0 controls and their composition through `verify.py --mode answer`:**

1. **Corroboration** (`scripts/validate_support.py`): can you make a claim show `CORROBORATED`
   without ≥2 genuinely independent origins?
2. **Gate-computed `high_impact`** (`scripts/validate_high_impact.py` + `config/high_impact_triggers.yaml`):
   can you launder a casualties/attribution/territorial-control claim as low-impact to switch off
   the strong controls?
3. **The refuter** (`scripts/validate_refuter.py`, `docs/REFUTER.md`) + the answer composition
   (`scripts/verify.py` `answer_check`, `scripts/validate_output.py`,
   `scripts/validate_manifest_structural.py`, `scripts/validate_context_pack.py`): can you ship a
   committed answer whose refuter is inadequate (under-covers, not independent, doesn't contest a
   high-impact claim) yet passes? Look hardest at **composition seams** between the three controls.

## What we ALREADY found and fixed — so hunt for NEW seams, don't re-report these

**Round 1 of THIS cross-vendor review (REJECT) already found and FIXED these P0/P1 paths — verify
they hold, then find NEW ones:** (P0-1) a refuter that REJECT/REVISE/DOWNGRADEs a claim now BLOCKS
the committed answer (`validate_refuter` answer_mode); (P0-2) `high_impact` now computes from the
claim TEXT too, not just author topics (a `topics:[transport]` casualties claim is caught); (P0-3) a
CHECKED review must bind the CURRENT claim-content hash (a stale review no longer earns support);
(P0-4) a high-impact assertion in the answer prose must be covered by a marked claim that is
high-impact IN that CATEGORY (a casualties marker cannot launder a co-located territorial-control
assertion); (P1-1) `--mode answer` requires `lifecycle: ANSWER`. Each has a fixture + a gate witness.

The in-harness review (`docs/REVIEW_MILESTONE_A.md`) + earlier follow-ups already found and **fixed**
(with regression tests): the empty-`claim_markers` degenerate answer; an unenforced
`required_refuter_class`; the observation feeding-leg; the A7 heading/blockquote skip-list; and the
two surfaced findings — **corroboration independence** (now counted by connected components over
shared `origin_chain` source OR `independence_group`, not `origin_chain[0]` alone) and **`high_impact`
topic synonyms** (trigger set widened). Verify those fixes actually hold in fresh context (try to
re-open them), but your highest value is a seam **none** of these found.

## Accepted residuals — do NOT report these as novel

- **A2** — a self-consistent *fabricated* record (coherent locator/hashes/credibility, semantically
  false). The gates are a coherence lower bound, not a truth certificate (Constitution §15.1).
- **A9** — a load-bearing claim simply never committed (held at Tier 0). A usage pattern; the
  recurrence-ledger fix is a deferred future WP.
- The A7 unmarked-assertion scanner is heuristic; markdown **table cells** are a disclosed blind
  spot (table data should come from observations; the manifest-coverage requirement is the backstop).

If you believe a residual is actually structurally closable, that IS a finding — show the gate.

## Mandatory adversarial exercises

Run the A1–A9 exercises in `docs/REVIEW_PROMPT.md` §"Mandatory adversarial exercises" against the
*built* code (not the old design). For each, produce a concrete passing-but-bad artifact (YAML /
analysis / refuter) and state whether the gate catches it. A1 (corroboration), A5 (observation/unit),
A7 (answer/refuter) are claimed killed — try hardest to revive them. Then add at least one exercise
of your own that the existing nine do not cover.

## Finding format (per issue)

```
[ID] severity: P0|P1|P2   control: corroboration|high_impact|refuter|composition|other
confidence: Certain|Probable|Speculative
Evidence: <file:line or the exact gate function>
Failure scenario: <concrete sequence — the passing-but-bad artifact>
Why current controls miss it: <the specific gap, vs the fixes above>
Recommended change: <specific edit>
Verification: <exact fixture/test that would lock the fix>
```

End with a one-paragraph honest assessment: **can an inadequately-supported or inadequately-refuted
committed answer ship today, and do the three P0 controls compose without a seam?** Do not inflate
the score if any P0 finding stands; a single real P0 means the committed-answer loop is not yet
trustworthy. This review does not gate anything automatically — it is defence-in-depth the owner
weighs.

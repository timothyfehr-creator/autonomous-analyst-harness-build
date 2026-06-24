# REFUTER — the Tier-2 refutation contract (WP3.3)

A committed (Tier-2) answer does not pass `verify.py --mode answer` until a **refuter artifact** is
bound to it and survives this contract. The refuter is the adversarial check that makes a recorded
answer trustworthy; it is enforced by `scripts/validate_refuter.py`. None of it proves the answer is
*true* — it proves the answer was *contested* by an appropriately independent reviewer who covered
exactly the claims and assessments the answer leans on.

## What a refuter artifact is

A `ref-` record (schema in `scripts/schema_defs.py`) that binds one analysis manifest and records:

- `manifest_hash` + `output_hash` — the exact manifest and answer text it reviewed;
- `reviewer_class` — `SAME_MODEL_FRESH_CONTEXT` · `DIFFERENT_MODEL` · `HUMAN` · `MIXED`;
- `reviewed_claim_ids` + `reviewed_assessment_ids` — the sets it actually reviewed;
- `verdicts[]` — per claim: a `verdict` (SURVIVES / REVISE / DOWNGRADE / REJECT) and the
  displacement / independence / freshness / observation / reasoning checks (PASS / FAIL /
  NOT_APPLICABLE), plus an optional `high_impact` contest flag;
- `alternative_hypotheses`, `disconfirming_searches`, `unresolved_gaps` — the honest residue.

## The contract the gate enforces

1. **Exact binding.** `manifest_hash` and `output_hash` must equal the analysis manifest's — the
   refuter reviewed *this* answer, not an earlier draft.
2. **Set-equality coverage (§10).** `reviewed_claim_ids` must equal the manifest's marker claim set,
   and `reviewed_assessment_ids` the manifest's cea-ref set — **exactly**, no missing and no extra.
   A boolean "I reviewed everything" attestation is never a substitute. The required set is anchored
   in the manifest (which the output gate forbids shrinking), so an answer cannot quietly drop a
   load-bearing claim to make the review look complete (the A7 exploit).
3. **Independence floor.** Every claim a committed answer cites *feeds the manifest*, so it requires
   an independent reviewer. `SAME_MODEL_FRESH_CONTEXT` is procedural only and **never qualifies** for
   a committed answer; use `DIFFERENT_MODEL`, `HUMAN`, or `MIXED`.
4. **`high_impact` contest (V-P0-1).** When the gate computes a claim `high_impact: true` by trigger
   (its topics intersect {casualties, attribution, territorial-control}, or it is a falsifiable
   projection feeding a prediction) but the claim is stored not-true, the verdict **must** set
   `high_impact: true` and run the independence check. This closes the circularity where the
   strongest control could be switched off by the very field that triggers it.
5. **Check applicability.** An INFERENCE claim's `reasoning_check`, a claim-with-observation's
   `observation_check`, and a STALE/REVIEW_DUE claim's `freshness_check` may not be `NOT_APPLICABLE`.
6. **Exemption review.** `exemptions_reviewed` must equal the analysis's `narrative_exemptions` — the
   refuter must have reviewed every sentence the author declared non-load-bearing (the cost that
   keeps the §A7 unmarked-assertion escape honest).

`unresolved_gaps` being non-empty is **not** a failure — recording what was not resolved is the
honest behavior, not a defect. Exit codes: `0` clean · `1` a finding in valid input · `2` cannot run.

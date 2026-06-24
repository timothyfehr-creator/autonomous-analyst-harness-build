# Milestone-A independent review — the P0 surface

**What this is.** A fresh-context, multi-agent adversarial review of the three P0 controls at
Milestone A — corroboration (WP2.5), gate-computed `high_impact` (WP2.2 / V-P0-1), and the refuter
(WP3.3) — plus their end-to-end composition through `verify.py --mode answer`. Three independent
reviewers each read the relevant code COLD (no build context) and attacked one control end to end,
building staged factbase trees and running the real gates.

**Honest label (the standing open limit).** This is a **same-platform** review (fresh-context
agents on the same model that built the harness). It is **NOT** a true cross-vendor pass. A
genuinely independent GPT-5.5-Pro / Gemini / human review of this P0 surface remains recommended
defence-in-depth and is **not** closed by this artifact (see README + PROGRESS). The owner chose
the in-harness review for this run; the cross-vendor pass can be run separately.

**Outcome.** The review found real, composing structural seams that the per-WP reviews missed — the
value of a holistic cold look. The clear Phase-3 answer-loop seams were **fixed-forward and locked
with regression tests** (below). Two findings touch the Phase-2 corroboration oracle or the trigger
config and are **surfaced for owner decision**, not changed autonomously.

## Fixed-forward (Phase-3 answer loop; regression-tested)

1. **Master seam — empty-markers committed answer (was exit 0).** A committed answer with empty
   `claim_markers` plus a `SAME_MODEL_FRESH_CONTEXT` refuter reviewing nothing shipped clean: the
   refuter's set-equality was vacuously satisfied and the independence floor (gated on
   `manifest_claims` being non-empty) switched off, while the answer still leaned on a claim via the
   context pack. **Fix:** `answer_check` now rejects an answer that cites no claim (empty
   `claim_markers`). `tests/test_answer_mode.py::test_answer_empty_markers_rejected`.
2. **`required_refuter_class` was decorative.** The manifest declared `HUMAN_OR_DIFFERENT_MODEL` but
   no gate enforced it. **Fix:** `validate_refuter` now rejects a `reviewer_class` that does not
   satisfy the manifest's declared bar. `tests/test_validate_refuter.py::test_required_refuter_class_enforced`.
3. **Feeding-leg seam — a claim backing a cited observation was reviewed by no one.** The §10
   "feeds a manifest" high-impact leg is uncomputed at records scope, and the refuter contest only
   ranged over prose-marker claims — so a benign-topic claim feeding the answer via an observation
   escaped the contest + independence floor. **Fix:** `validate_manifest_structural` now requires
   every cited observation's underlying claim to be a marked claim, forcing it into the refuter's
   covered/contested set. `tests/test_draft_mode.py::test_manifest_observation_backing_must_be_marked`.
4. **A7 heading/blockquote skip-list.** A load-bearing assertion smuggled into a markdown heading or
   blockquote was skipped by the unmarked-assertion scanner. **Fix:** headings and blockquotes are
   now stripped + scanned (like list bullets). `tests/test_validate_output.py::test_heading_and_blockquote_assertions_are_scanned`.

## Confirmed solid (attacked, held)

- The credibility floor (1..3, fail-closed on bool/null/string/UNASSESSED), stance/status/
  supersession filtering, and the **labeled** first-party exclusion (the A1 kill) in corroboration.
- `high_impact` null/false/type bypass (`is not True` + schema null-block); the cross-commit R-HI
  tamper gate (true→false flips + trigger-input changes on existing claims; the `Reviewed-separately:`
  trailer does NOT clear R-HI); the topic + falsifiable-projection legs compose with the refuter
  contest as defence-in-depth (the records gate is a whole-factbase floor that runs first).
- Refuter binding, set-equality coverage, the per-claim verdict requirement, SURVIVES-cannot-carry-
  FAIL, and the independence floor + V-P0-1 contest **when markers are non-empty**.
- Input-lifecycle reject across all three reference paths (markers ∪ context-pack `claim_refs` ∪
  visual `input_claim_refs`), including STALE/REVIEW_DUE.

## Surfaced for owner decision (NOT changed autonomously)

1. **Corroboration independence is collapsed on `origin_chain[0]` only (Phase-2 / WP2.5).** Two
   outlets that echo one upstream wire — sharing a deeper `origin_chain[*].source_id` and even a
   truthfully-declared shared `independence_group` — can reach `CORROBORATED`, because the gate
   never consults the deeper chain or the `independence_group` field (which no gate currently
   reads). The same `origin_chain[0]`-only collapse is reused by the conflict gate. This is the §3
   "two outlets repeating one ministry statement are one chain" hazard. Closing it is an oracle-level
   change to `validate_support.py` + `validate_conflict.py` (collapse on the shared/deepest origin or
   honor `independence_group`) and is governance-sensitive (it changes how corroboration is computed
   and could move the skeleton). Recommended as its own hardening WP, with the caveat that
   `independence_group` is itself author-declared (a determined author can still split groups — the
   deeper-chain signal is the more objective lever).
2. **`high_impact` topic matching is exact-token over a free-text `topics` list.** Common synonyms
   (`losses`, `deaths`, `fatalities`, `KIA`) are not in the 4-token trigger set, so a casualties
   claim tagged with a synonym escapes the topic leg. This is disclosed + owner-editable
   (`config/high_impact_triggers.yaml`). Recommended: widen the trigger set and/or constrain `topics`
   to a controlled vocabulary.

## Accepted residuals (no structural gate can close)

- **A2** — a self-consistent fabricated assessment (coherent locator/hashes/credibility, semantically
  false). The gates are a coherence lower bound, not a truth certificate (§15.1).
- **A9** — a load-bearing claim simply never committed (held at Tier 0). A usage pattern, not a
  fixture; the recurrence-ledger fix is the deferred WP4.7 (its own review).
- The A7 unmarked-assertion scanner remains a heuristic; markdown **table cells** are a disclosed
  blind spot (table data should come from observations; the manifest-coverage requirement is the
  real backstop). The deterministic A7 half (manifest ↔ marker ↔ refuter set-equality) is airtight.

#!/usr/bin/env python3
"""WP3.3 — refuter integrity + support audit (the answer-mode refuter control). See docs/REFUTER.md.

A Tier-2 answer does not pass until a refuter artifact is bound to the exact manifest/output and
covers the required claim/assessment sets by SET EQUALITY (Constitution §10). This gate enforces:

  1. exact binding: refuter.manifest_hash/output_hash == analysis.manifest_hash/output_hash;
  2. set-equality coverage: reviewed_claim_ids == the manifest's marker claim set AND
     reviewed_assessment_ids == the manifest's cea-ref set (missing OR extra → fail; a boolean
     attestation is not a substitute). This anchors the "required set" in the manifest, which
     validate_output/manifest_structural prevent from being shrunk (the A7 deterministic half);
  3. independence floor: every claim a committed answer cites FEEDS the manifest and so requires an
     independent reviewer — reviewer_class SAME_MODEL_FRESH_CONTEXT never qualifies (§10);
  4. high_impact CONTEST (V-P0-1 / R2-P0-3): for EVERY high-impact claim — gate-computed (topics,
     text, reviewer impact_category, or a falsifiable projection) OR a correctly-stored
     high_impact: true — the refuter's verdict MUST set high_impact: true AND actually run the
     independence check (not NOT_APPLICABLE). Setting the flag correctly no longer lets a claim skip
     the rigor (R2-P0-3). In answer mode a committed high-impact claim must ALSO carry a non-NONE
     impact_category (FR-2) and the refuter must show a non-empty disconfirming_searches;
  5. per-verdict check applicability: an INFERENCE claim's reasoning_check, a claim-with-observation's
     observation_check, and a STALE/REVIEW_DUE claim's freshness_check may not be NOT_APPLICABLE;
  6. the A7 escape cost: exemptions_reviewed == analysis.narrative_exemptions (the refuter must echo
     every sentence the author declared non-load-bearing, so an exemption costs a review).

Returns (exit_code, findings): 0 clean · 1 finding in valid input. `unresolved_gaps` being non-empty
is NOT a failure (honest disclosure). Schema runs first in the caller; live records resolve clean.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import answer_layer as al  # noqa: E402
import validate_high_impact as v_hi  # noqa: E402

INDEPENDENT = {"HUMAN", "DIFFERENT_MODEL", "MIXED"}


def _wellformed_search(s) -> bool:
    """A disconfirming search is real iff it is a non-empty string OR a mapping with non-empty
    query AND result — so a vacuous [""], [None], [{}] does not satisfy the high-impact requirement."""
    if isinstance(s, str):
        return bool(s.strip())
    if isinstance(s, dict):
        return bool(str(s.get("query") or "").strip()) and bool(str(s.get("result") or "").strip())
    return False


def validate_refuter(refuter: dict, analysis: dict, live: al.Live, triggers=None, answer_mode=False,
                     required_ceas=None):
    """answer_mode=False: validate the refuter record's STRUCTURE (a negative verdict is a valid
    stored record). answer_mode=True (a committed answer): the refuter must also CERTIFY the answer —
    every required claim's verdict must be SURVIVES, so a refuter that REVISE/DOWNGRADE/REJECTs a
    claim blocks the committed answer (cross-vendor review P0-1: the refuter's "no" must mean no).
    required_ceas (R2-P0-1): when the caller passes a GATE-COMPUTED required assessment set (manifest
    ∪ context pack ∪ the marked claims' active CHECKED support — computed by answer_check from the
    real factbase), coverage is by SUPERSET (reviewed ⊇ required) instead of the manifest set-equality
    the author could shrink. None ⇒ records/standalone mode uses manifest set-equality."""
    if triggers is None:
        triggers = v_hi.trigger_set()
    f = []

    # 1. exact binding to the analysis manifest + output
    if refuter.get("manifest_hash") != analysis.get("manifest_hash"):
        f.append("refuter manifest_hash does not bind the analysis manifest_hash")
    if refuter.get("output_hash") != analysis.get("output_hash"):
        f.append("refuter output_hash does not bind the analysis output_hash")

    # the required sets are anchored in the MANIFEST (author cannot shrink them — A7)
    markers = analysis.get("claim_markers") if isinstance(analysis.get("claim_markers"), dict) else {}
    manifest_claims = {mv.get("claim_id") for mv in markers.values() if isinstance(mv, dict)}
    manifest_ceas = {r.get("id") for r in (analysis.get("claim_evidence_assessment_refs") or [])
                     if isinstance(r, dict)}
    reviewed_claims = set(refuter.get("reviewed_claim_ids") or [])
    reviewed_ceas = set(refuter.get("reviewed_assessment_ids") or [])

    # 2. coverage. Claims are always set-equal to the markers (they DEFINE the answer's claims).
    if reviewed_claims != manifest_claims:
        f.append(f"reviewed_claim_ids != manifest claim set "
                 f"(missing {sorted(manifest_claims - reviewed_claims)}, "
                 f"extra {sorted(reviewed_claims - manifest_claims)})")
    # Assessments: a gate-computed required set (answer mode) is covered by SUPERSET — the author
    # cannot shrink it by emptying the manifest list (R2-P0-1). Records mode uses manifest equality.
    if required_ceas is not None:
        missing = set(required_ceas) - reviewed_ceas
        if missing:
            f.append(f"reviewed_assessment_ids does not cover the gate-computed required set "
                     f"(missing {sorted(missing)}) — a committed answer's refuter scope is computed "
                     f"from the marked claims' active CHECKED support + the context pack, not the "
                     f"author's manifest list [R2-P0-1]")
    elif reviewed_ceas != manifest_ceas:
        f.append(f"reviewed_assessment_ids != manifest assessment set "
                 f"(missing {sorted(manifest_ceas - reviewed_ceas)}, "
                 f"extra {sorted(reviewed_ceas - manifest_ceas)})")

    # 3. independence floor — every cited claim feeds the manifest ⇒ needs an independent reviewer
    if manifest_claims and refuter.get("reviewer_class") == "SAME_MODEL_FRESH_CONTEXT":
        f.append("reviewer_class SAME_MODEL_FRESH_CONTEXT is not independent (§10): a committed "
                 "answer's claims feed the manifest and require HUMAN / DIFFERENT_MODEL / MIXED")
    # ...and the manifest's OWN declared bar must actually be met (it was decorative before — the
    # Milestone-A P0 review found required_refuter_class was never enforced).
    if analysis.get("required_refuter_class") == "HUMAN_OR_DIFFERENT_MODEL" \
            and refuter.get("reviewer_class") not in INDEPENDENT:
        f.append(f"reviewer_class {refuter.get('reviewer_class')!r} does not satisfy the manifest's "
                 f"required_refuter_class HUMAN_OR_DIFFERENT_MODEL (needs HUMAN/DIFFERENT_MODEL/MIXED)")

    verdicts = {vd.get("claim_id"): vd for vd in (refuter.get("verdicts") or []) if isinstance(vd, dict)}
    # claims that carry an observation cited in the manifest (so observation_check is applicable)
    manifest_obs = [r.get("id") for r in (analysis.get("observation_refs") or []) if isinstance(r, dict)]
    claims_with_obs = {live.observations[o].get("claim_id") for o in manifest_obs if o in live.observations}

    # 4 + 5. per-claim: every required claim must be ADJUDICATED (have a verdict — set membership is
    # not coverage), then contest + check applicability + verdict-disposition consistency.
    CHECKS = ("displacement_check", "independence_check", "freshness_check",
              "observation_check", "reasoning_check")
    any_high_impact = False
    for cid in sorted(manifest_claims):
        claim = live.claims.get(cid)
        if claim is None:
            continue  # resolution is manifest_structural's job (run first in answer mode)
        vd = verdicts.get(cid)
        if vd is None:
            f.append(f"claim {cid!r}: in the manifest's required set but has no verdict entry "
                     f"(a covered claim must be adjudicated, not merely listed)")
            continue
        # 4. high_impact contest — fire for EVERY high-impact claim, by ANY route: gate-computed
        # (topics/text/category/projection) OR a correctly-stored high_impact: true. R2-P0-3 closed
        # the loophole where setting the flag right let the claim skip the rigor (the old gate only
        # fired on an author DOWNGRADE). compute_high_impact already folds in the FR-2 category leg.
        computed, reasons = v_hi.compute_high_impact(claim, triggers)
        is_hi = computed or claim.get("high_impact") is True
        if is_hi:
            any_high_impact = True
            detail = "; ".join(reasons) or "stored high_impact: true"
            if vd.get("high_impact") is not True or vd.get("independence_check") == "NOT_APPLICABLE":
                f.append(f"claim {cid!r}: is high_impact ({detail}); the refuter MUST contest it "
                         f"(verdict high_impact: true + independence_check run, not NOT_APPLICABLE) "
                         f"[V-P0-1/R2-P0-3]")
            # FR-2 answer-path closure: a committed answer's high-impact claim must carry the
            # AUTHORITATIVE reviewer-assigned category, not a word-list guess.
            if answer_mode:
                cat = claim.get("impact_category")
                if not (isinstance(cat, str) and cat not in ("", "NONE")):
                    f.append(f"claim {cid!r}: high_impact but impact_category is {cat!r} — a committed "
                             f"answer's high-impact claim must carry a non-NONE impact_category "
                             f"(FR-2/R2-P0-2)")
        if claim.get("epistemic_type") == "INFERENCE" and vd.get("reasoning_check") == "NOT_APPLICABLE":
            f.append(f"claim {cid!r}: INFERENCE verdict requires reasoning_check != NOT_APPLICABLE")
        if cid in claims_with_obs and vd.get("observation_check") == "NOT_APPLICABLE":
            f.append(f"claim {cid!r}: has a cited observation — observation_check may not be NOT_APPLICABLE")
        if claim.get("freshness_status") in {"STALE", "REVIEW_DUE"} and vd.get("freshness_check") == "NOT_APPLICABLE":
            f.append(f"claim {cid!r}: freshness_status {claim.get('freshness_status')!r} requires "
                     f"freshness_check != NOT_APPLICABLE")
        # disposition consistency: a SURVIVES verdict cannot carry a FAILed check (the check failed,
        # so the claim did NOT survive). An honest negative records FAIL + REVISE/DOWNGRADE/REJECT.
        if vd.get("verdict") == "SURVIVES":
            failed = [c for c in CHECKS if vd.get(c) == "FAIL"]
            if failed:
                f.append(f"claim {cid!r}: verdict SURVIVES but {failed} FAILed — a failed check cannot "
                         f"yield SURVIVES (use REVISE/DOWNGRADE/REJECT)")
        # answer-mode certification: a committed answer requires every required claim to SURVIVE.
        # A REVISE/DOWNGRADE/REJECT verdict is an honest "no" that blocks the committed answer (it is
        # still a valid stored refuter record — answer_mode=False does not flag it).
        elif answer_mode and vd.get("verdict") in {"REVISE", "DOWNGRADE", "REJECT"}:
            f.append(f"claim {cid!r}: refuter verdict {vd.get('verdict')!r} — a committed answer "
                     f"requires every claim to SURVIVE the refuter; this answer cannot be committed")

    # R2-P0-3: a committed answer that commits a high-impact claim must show an ACTUAL disconfirming
    # search — an empty disconfirming_searches is not a contest. Answer-mode only (a stored refuter
    # record may legitimately carry none).
    if answer_mode and any_high_impact and not any(
            _wellformed_search(s) for s in (refuter.get("disconfirming_searches") or [])):
        f.append("a committed answer includes a high-impact claim but disconfirming_searches is "
                 "empty or vacuous — a high-impact contest requires an actual disconfirming search "
                 "(a non-empty query+result), R2-P0-3")

    # 6. the A7 escape cost: the refuter must echo the analysis's narrative_exemptions by set equality
    if set(refuter.get("exemptions_reviewed") or []) != set(analysis.get("narrative_exemptions") or []):
        f.append("exemptions_reviewed != analysis narrative_exemptions (the A7 escape requires the "
                 "refuter to review every exempted sentence; clearing one costs a review)")

    return (1 if f else 0), sorted(f)

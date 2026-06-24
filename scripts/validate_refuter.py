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
  4. high_impact CONTEST (V-P0-1 refuter half): for a claim the gate computes high_impact TRUE by
     trigger (topics ∩ {casualties, attribution, territorial-control}, or a falsifiable projection)
     while it is stored not-true, the refuter's verdict MUST set high_impact: true AND actually run
     the independence check — closing the circularity where the strongest control is switched off
     by the very field that triggers it;
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


def validate_refuter(refuter: dict, analysis: dict, live: al.Live, triggers=None):
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

    # 2. set-equality coverage (both directions)
    if reviewed_claims != manifest_claims:
        f.append(f"reviewed_claim_ids != manifest claim set "
                 f"(missing {sorted(manifest_claims - reviewed_claims)}, "
                 f"extra {sorted(reviewed_claims - manifest_claims)})")
    if reviewed_ceas != manifest_ceas:
        f.append(f"reviewed_assessment_ids != manifest assessment set "
                 f"(missing {sorted(manifest_ceas - reviewed_ceas)}, "
                 f"extra {sorted(reviewed_ceas - manifest_ceas)})")

    # 3. independence floor — every cited claim feeds the manifest ⇒ needs an independent reviewer
    if manifest_claims and refuter.get("reviewer_class") == "SAME_MODEL_FRESH_CONTEXT":
        f.append("reviewer_class SAME_MODEL_FRESH_CONTEXT is not independent (§10): a committed "
                 "answer's claims feed the manifest and require HUMAN / DIFFERENT_MODEL / MIXED")

    verdicts = {vd.get("claim_id"): vd for vd in (refuter.get("verdicts") or []) if isinstance(vd, dict)}
    # claims that carry an observation cited in the manifest (so observation_check is applicable)
    manifest_obs = [r.get("id") for r in (analysis.get("observation_refs") or []) if isinstance(r, dict)]
    claims_with_obs = {live.observations[o].get("claim_id") for o in manifest_obs if o in live.observations}

    # 4 + 5. per-claim: every required claim must be ADJUDICATED (have a verdict — set membership is
    # not coverage), then contest + check applicability + verdict-disposition consistency.
    CHECKS = ("displacement_check", "independence_check", "freshness_check",
              "observation_check", "reasoning_check")
    for cid in sorted(manifest_claims):
        claim = live.claims.get(cid)
        if claim is None:
            continue  # resolution is manifest_structural's job (run first in answer mode)
        vd = verdicts.get(cid)
        if vd is None:
            f.append(f"claim {cid!r}: in the manifest's required set but has no verdict entry "
                     f"(a covered claim must be adjudicated, not merely listed)")
            continue
        computed, reasons = v_hi.compute_high_impact(claim, triggers)
        if computed and claim.get("high_impact") is not True:
            if vd.get("high_impact") is not True or vd.get("independence_check") == "NOT_APPLICABLE":
                f.append(f"claim {cid!r}: gate computes high_impact true ({'; '.join(reasons)}) but it "
                         f"is stored {claim.get('high_impact')!r}; the refuter MUST contest it "
                         f"(verdict high_impact: true + independence_check run) [V-P0-1]")
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

    # 6. the A7 escape cost: the refuter must echo the analysis's narrative_exemptions by set equality
    if set(refuter.get("exemptions_reviewed") or []) != set(analysis.get("narrative_exemptions") or []):
        f.append("exemptions_reviewed != analysis narrative_exemptions (the A7 escape requires the "
                 "refuter to review every exempted sentence; clearing one costs a review)")

    return (1 if f else 0), sorted(f)

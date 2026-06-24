#!/usr/bin/env python3
"""WP3.1 — analysis-manifest STRUCTURAL integrity (the draft-mode manifest control).

The manifest pins exact record ids + hashes. Structural validation (NOT the output-text binding,
which is WP3.2; NOT the refuter, which is WP3.3) checks every pinned reference still resolves to a
live record AND binds that record's CURRENT hash, so a tampered, superseded, or stale snapshot
turns red:

  - claim_markers[*].claim_hash  == claim_content_hash(live claim)   (status-excluded, WP3.0)
  - claim_evidence_assessment_refs / observation_refs / prediction_refs  == record_hash(live record)
  - artifact_refs[*].content_hash == live evidence.content_hash       (external digest)
  - visual_refs[*].record_hash    == live visual.spec_hash            (the visual's self-hash)
  - manifest_hash == record_hash(analysis, exclude=manifest_hash)     (self-consistency)

Returns (exit_code, findings): 0 clean · 1 a structural finding in valid input. The caller
(draft/answer) runs schema validation FIRST and resolves `Live` only on a clean parse (§13).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import answer_layer as al  # noqa: E402
import validate_schema as vs  # noqa: E402


def validate_manifest_structural(analysis: dict, live: al.Live):
    f = []
    # 1. markers: claim resolves + binds the claim-CONTENT hash
    markers = analysis.get("claim_markers") if isinstance(analysis.get("claim_markers"), dict) else {}
    for mk in sorted(markers):
        mv = markers[mk]
        if not isinstance(mv, dict):  # malformed marker (already schema-flagged) — don't crash
            f.append(f"marker {mk!r} is not a mapping")
            continue
        cid, ch = mv.get("claim_id"), mv.get("claim_hash")
        claim = live.claims.get(cid)
        if claim is None:
            f.append(f"marker {mk!r}: claim {cid!r} does not resolve to a live claim")
        elif ch != live.claim_marker_hash(claim):
            f.append(f"marker {mk!r}: claim_hash is stale for {cid!r} "
                     f"(binds {ch!r}, live claim-content is {live.claim_marker_hash(claim)!r})")
    # 2. hash-bound reference lists resolve + match the live record's current hash
    f += al.check_ref_list(analysis.get("claim_evidence_assessment_refs"), live.cea,
                           "record_hash", live.record_ref_hash, "claim_evidence_assessment")
    f += al.check_ref_list(analysis.get("observation_refs"), live.observations,
                           "record_hash", live.record_ref_hash, "observation")
    f += al.check_ref_list(analysis.get("prediction_refs"), live.predictions,
                           "record_hash", live.record_ref_hash, "prediction")
    f += al.check_ref_list(analysis.get("artifact_refs"), live.evidence,
                           "content_hash", live.artifact_ref_hash, "artifact")
    f += al.check_ref_list(analysis.get("visual_refs"), live.visuals,
                           "record_hash", live.visual_ref_hash, "visual")
    # 3. manifest self-hash consistency (tamper-evident over the whole manifest record)
    if analysis.get("manifest_hash") != vs.record_hash(analysis, exclude=("manifest_hash",)):
        f.append("manifest_hash is self-inconsistent (record_hash(analysis, exclude=manifest_hash) differs)")
    return (1 if f else 0), sorted(f)

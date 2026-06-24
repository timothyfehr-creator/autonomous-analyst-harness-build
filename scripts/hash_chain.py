#!/usr/bin/env python3
"""WP3.0 — the answer-layer hash chain: reusable hash helpers + a reproducible regenerator for the
Milestone-A skeleton's answer layer (context pack → analysis manifest → refuter → visual → output).

Why this exists: the skeleton's answer-layer hashes shipped as format-valid PLACEHOLDERS (WP1.6).
Phase 3 dereferences them, so they must become a real, self-consistent chain:

    claim_content_hash(claim) ─► analysis.claim_markers[*].claim_hash, cea.semantic_review.claim_content_hash
    record_hash(claim/cea/obs/geo) ─► visual + context-pack ref hashes
    evidence.content_hash (external digest, kept) ─► artifact ref hashes
    pack_hash = record_hash(pack, exclude=pack_hash) ─► analysis.context_pack_hash
    file_content_hash(output.md) ─► analysis.output_hash, refuter.output_hash
    spec_hash = record_hash(visual, exclude=spec_hash) ─► analysis.visual_refs[*].record_hash
    manifest_hash = record_hash(analysis, exclude=manifest_hash) ─► refuter.manifest_hash

`regenerate()` is REPRODUCIBLE (idempotent, re-runnable): every dependent hash is computed by
LOADING the written YAML (not a hand-built dict), and self-hash fields are computed with the
self-exclude convention, so the file the test loads and the file this wrote always agree.

The helpers (manifest_hash / pack_hash / spec_hash / file_content_hash / claim_content_hash) are
imported by the Phase-3 gates (WP3.1–3.4) so there is ONE hashing source of truth.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))
import validate_schema as vs  # noqa: E402

SK = REPO / "tests" / "fixtures" / "skeleton"
ZERO = "sha256:" + "0" * 64  # self-hash sentinel: excluded from its own record hash, so its value is irrelevant


# ----------------------------- reusable helpers (WP3.1+ import these) -----------------------------
def claim_content_hash(claim) -> str:
    return vs.claim_content_hash(claim)


def file_content_hash(path: Path) -> str:
    return vs.file_content_hash(path)


def manifest_hash(analysis: dict) -> str:
    return vs.record_hash(analysis, exclude=("manifest_hash",))


def pack_hash(pack: dict) -> str:
    return vs.record_hash(pack, exclude=("pack_hash",))


def spec_hash(visual: dict) -> str:
    return vs.record_hash(visual, exclude=("spec_hash",))


def _load1(path: Path, collection: str):
    return vs.load_yaml_strict(path)[collection][0]


def _selfhash(path: Path, collection: str, field: str) -> str:
    """Compute a record's self-hash from the WRITTEN yaml (field excluded), eliminating dict↔yaml drift."""
    return vs.record_hash(_load1(path, collection), exclude=(field,))


# ----------------------------- the reproducible regenerator (WP3.0) -----------------------------
OUTPUT_MD = "The Skeleton Crossing supports road transport (synthetic). [[c1]]\n"


def regenerate() -> dict:
    """Rebuild the answer-layer skeleton with a real, self-consistent hash chain. Returns the chain."""
    # source records (factbase layer; unchanged except the cea's claim_content_hash, set below)
    claim = _load1(SK / "skeleton_claims.yaml", "claims")
    cc = vs.claim_content_hash(claim)
    rh_claim = vs.record_hash(claim)

    # 1. bind the cea's semantic_review.claim_content_hash to the real content hash (idempotent regex)
    import re
    cea_path = SK / "skeleton_claim_evidence.yaml"
    cea_text = re.sub(r"(claim_content_hash: )sha256:[0-9a-f]{64}", r"\g<1>" + cc, cea_path.read_text())
    cea_path.write_text(cea_text)
    cea = _load1(cea_path, "claim_evidence_assessments")
    rh_cea = vs.record_hash(cea)

    obs = _load1(SK / "skeleton_observations.yaml", "observations"); rh_obs = vs.record_hash(obs)
    geo = _load1(SK / "skeleton_geography.yaml", "geography"); rh_geo = vs.record_hash(geo)
    evd = _load1(SK / "skeleton_evidence.yaml", "evidence"); content_hash = evd["content_hash"]

    # 2. output text fixture (tracked; staged into outputs/ana-skeleton.md at gate time)
    out_path = SK / "skeleton_output.md"
    out_path.write_text(OUTPUT_MD)
    output_h = vs.file_content_hash(out_path)

    # 3. visual (spec_hash via zero-sentinel → load → recompute → rewrite)
    vis_path = SK / "skeleton_visual.yaml"
    vis_path.write_text(_visual_yaml(rh_claim, rh_cea, rh_obs, rh_geo, ZERO))
    sh = _selfhash(vis_path, "visuals", "spec_hash")
    vis_path.write_text(_visual_yaml(rh_claim, rh_cea, rh_obs, rh_geo, sh))

    # 4. context pack (pack_hash via zero-sentinel)
    pack_path = SK / "skeleton_context_pack.yaml"
    pack_path.write_text(_pack_yaml(rh_claim, rh_cea, content_hash, rh_obs, ZERO))
    ph = _selfhash(pack_path, "context_packs", "pack_hash")
    pack_path.write_text(_pack_yaml(rh_claim, rh_cea, content_hash, rh_obs, ph))

    # 5. analysis manifest (manifest_hash via zero-sentinel; refs filled with real hashes)
    ana_path = SK / "skeleton_analysis.yaml"
    ana_path.write_text(_analysis_yaml(ph, output_h, cc, rh_cea, content_hash, rh_obs, sh, ZERO))
    mh = _selfhash(ana_path, "analyses", "manifest_hash")
    ana_path.write_text(_analysis_yaml(ph, output_h, cc, rh_cea, content_hash, rh_obs, sh, mh))

    # 6. refuter (binds the analysis manifest + output)
    (SK / "skeleton_refuter.yaml").write_text(_refuter_yaml(mh, output_h))

    return {"claim_content_hash": cc, "record_hash_claim": rh_claim, "record_hash_cea": rh_cea,
            "record_hash_obs": rh_obs, "record_hash_geo": rh_geo, "content_hash": content_hash,
            "output_hash": output_h, "spec_hash": sh, "pack_hash": ph, "manifest_hash": mh}


def _visual_yaml(rh_claim, rh_cea, rh_obs, rh_geo, sh) -> str:
    return f"""schema_version: "2.0"
visuals:
  - id: vis-skeleton-modes
    visual_type: SCHEMATIC
    title: Transport modes using the Skeleton Crossing (synthetic)
    as_of: "2026-06-22"
    input_claim_refs:
      - {{id: clm-skeleton-crossing-modes, record_hash: {rh_claim}}}
    input_claim_evidence_assessment_refs:
      - {{id: cea-skeleton-owner-to-modes, record_hash: {rh_cea}}}
    input_observation_refs:
      - {{id: obs-skeleton-road, record_hash: {rh_obs}}}
    input_prediction_refs: []
    input_geography_refs:
      - {{id: geo-skeleton-crossing, record_hash: {rh_geo}}}
    data_bindings: {{road_node: obs-skeleton-road}}
    transformation: identity
    filters: []
    aggregation: none
    missing_data_policy: error
    output_path: outputs/vis-skeleton-modes.svg
    renderer: graphviz
    renderer_version: planned
    spec_hash: {sh}
"""


def _pack_yaml(rh_claim, rh_cea, content_hash, rh_obs, ph) -> str:
    return f"""schema_version: "2.0"
context_packs:
  - id: ctx-skeleton
    query: What transport modes use the Skeleton Crossing? (synthetic)
    topics: [transport, infrastructure]
    generated_at: "2026-06-22T12:30:00Z"
    generator_version: wp3.0-synthetic
    selection_policy: skeleton — all reviewed on-topic claims, token budget 4000
    token_budget: 4000
    claim_refs:
      - {{id: clm-skeleton-crossing-modes, record_hash: {rh_claim}}}
    assessment_refs:
      - {{id: cea-skeleton-owner-to-modes, record_hash: {rh_cea}}}
    artifact_refs:
      - {{id: evd-skeleton-owner-record, content_hash: {content_hash}}}
    observation_refs:
      - {{id: obs-skeleton-road, record_hash: {rh_obs}}}
    prediction_refs: []
    omitted_candidates: []
    pack_hash: {ph}
"""


def _analysis_yaml(ph, output_h, cc, rh_cea, content_hash, rh_obs, sh, mh) -> str:
    return f"""schema_version: "2.0"
analyses:
  - id: ana-skeleton
    lifecycle: ANSWER
    question: What transport modes use the Skeleton Crossing? (synthetic)
    context_pack_id: ctx-skeleton
    context_pack_hash: {ph}
    output_path: outputs/ana-skeleton.md
    output_hash: {output_h}
    claim_markers:
      c1:
        claim_id: clm-skeleton-crossing-modes
        claim_hash: {cc}
    claim_evidence_assessment_refs:
      - {{id: cea-skeleton-owner-to-modes, record_hash: {rh_cea}}}
    artifact_refs:
      - {{id: evd-skeleton-owner-record, content_hash: {content_hash}}}
    observation_refs:
      - {{id: obs-skeleton-road, record_hash: {rh_obs}}}
    prediction_refs: []
    visual_refs:
      - {{id: vis-skeleton-modes, record_hash: {sh}}}
    required_refuter_class: HUMAN_OR_DIFFERENT_MODEL
    manifest_hash: {mh}
"""


def _refuter_yaml(mh, output_h) -> str:
    return f"""schema_version: "2.0"
refuters:
  - id: ref-skeleton
    analysis_id: ana-skeleton
    manifest_hash: {mh}
    output_hash: {output_h}
    reviewer_class: HUMAN
    reviewer: human:tim
    reviewed_at: "2026-06-22T13:30:00Z"
    reviewed_claim_ids: [clm-skeleton-crossing-modes]
    reviewed_assessment_ids: [cea-skeleton-owner-to-modes]
    verdicts:
      - claim_id: clm-skeleton-crossing-modes
        verdict: SURVIVES
        displacement_check: PASS
        independence_check: PASS
        freshness_check: PASS
        observation_check: PASS
        reasoning_check: NOT_APPLICABLE
        notes: synthetic skeleton verdict
    alternative_hypotheses: []
    disconfirming_searches:
      - {{query: skeleton crossing no road, result: no contrary artifact}}
    unresolved_gaps: []
"""


if __name__ == "__main__":
    chain = regenerate()
    for k, v in chain.items():
        print(f"  {k}: {v}")
    print("OK — answer-layer skeleton hash chain regenerated (reproducible).")

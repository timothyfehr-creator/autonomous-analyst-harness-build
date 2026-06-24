#!/usr/bin/env python3
"""WP3.1 — live-record resolution for the Phase-3 answer layer (shared by the draft/answer gates).

`Live(root)` loads the factbase records the analysis layer references, by id, from a factbase tree:

    <root>/factbase/{baseline,live}/claims.yaml   claims (union)
    <root>/factbase/claim_evidence.yaml           cea assessments
    <root>/factbase/evidence.yaml                 evidence artifacts
    <root>/factbase/observations.yaml             observations
    <root>/factbase/predictions.yaml              predictions
    <root>/factbase/geography.yaml                geography
    <root>/factbase/{context_packs,analyses,refuters,visuals}.yaml   answer-layer registries

Missing files resolve to empty (the real seed factbase has no answer-layer registries; records
fails closed on empty BEFORE any resolution, so draft/answer never run over nothing). This module
does NOT schema-validate — the gate runs `validate_schema.validate_file` FIRST and bails on a
non-zero before building `Live` (so every record here is already parseable + shape-clean).

The ref-hash helpers centralize the WP3.0 binding conventions (one source of truth):
  marker.claim_hash  -> claim_content_hash(claim)        (status-excluded; stable across re-review)
  cea/obs/pred ref   -> record_hash(record)              (full record)
  artifact ref       -> evidence.content_hash            (external digest, stored field)
  visual ref         -> visual.spec_hash                 (the visual's stored self-hash)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_schema as vs  # noqa: E402


def _load_list(path: Path, collection: str):
    if not path.exists():
        return []
    data = vs.load_yaml_strict(path) or {}
    return data.get(collection) or []


def _by_id(records):
    return {r.get("id"): r for r in records if isinstance(r, dict) and r.get("id")}


class Live:
    def __init__(self, root: Path):
        fb = Path(root) / "factbase"
        claims = _load_list(fb / "baseline" / "claims.yaml", "claims") + \
            _load_list(fb / "live" / "claims.yaml", "claims")
        self.claims = _by_id(claims)
        self.cea = _by_id(_load_list(fb / "claim_evidence.yaml", "claim_evidence_assessments"))
        self.evidence = _by_id(_load_list(fb / "evidence.yaml", "evidence"))
        self.observations = _by_id(_load_list(fb / "observations.yaml", "observations"))
        self.predictions = _by_id(_load_list(fb / "predictions.yaml", "predictions"))
        self.geography = _by_id(_load_list(fb / "geography.yaml", "geography"))
        self.context_packs = _by_id(_load_list(fb / "context_packs.yaml", "context_packs"))
        self.analyses = _by_id(_load_list(fb / "analyses.yaml", "analyses"))
        self.refuters = _by_id(_load_list(fb / "refuters.yaml", "refuters"))
        self.visuals = _by_id(_load_list(fb / "visuals.yaml", "visuals"))

    # ---- ref-hash conventions (WP3.0): the value a manifest/pack ref MUST carry for `rec` ----
    @staticmethod
    def claim_marker_hash(claim) -> str:
        return vs.claim_content_hash(claim)

    @staticmethod
    def record_ref_hash(record) -> str:
        return vs.record_hash(record)

    @staticmethod
    def artifact_ref_hash(evidence) -> str:
        return evidence.get("content_hash")

    @staticmethod
    def visual_ref_hash(visual) -> str:
        return visual.get("spec_hash")

    def refuter_for_analysis(self, analysis_id: str):
        return next((r for r in self.refuters.values() if r.get("analysis_id") == analysis_id), None)


def check_ref_list(refs, resolver: dict, hash_field: str, expected_hash_fn, label: str):
    """Each ref must resolve to a live record AND carry the binding hash that record currently
    computes. A missing record OR a stale hash (a tampered/superseded snapshot) is a finding."""
    f = []
    for ref in refs or []:
        if not isinstance(ref, dict):  # malformed entry (already schema-flagged) — don't crash
            f.append(f"{label} ref entry is not a mapping: {ref!r}")
            continue
        rid = ref.get("id")
        rec = resolver.get(rid)
        if rec is None:
            f.append(f"{label} ref {rid!r} does not resolve to a live record")
            continue
        expected = expected_hash_fn(rec)
        if ref.get(hash_field) != expected:
            f.append(f"{label} ref {rid!r}: stale {hash_field} (binds {ref.get(hash_field)!r}, "
                     f"live record is {expected!r})")
    return f

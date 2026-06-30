#!/usr/bin/env python3
"""WP-AL.1 — the answer-AUTHORING hash-fill helper.

The Phase-3 gates can GRADE an answer layer but nothing AUTHORS one: the context pack, analysis
manifest, and visual carry ~7 binding hashes that, until now, were hand-computed (or regenerated only
for the skeleton fixture by `hash_chain.regenerate`). This module fills those binding hashes into
author-supplied answer-layer records over ANY `--root`, by LOADING the live factbase records they
reference — so there stays ONE hashing source of truth (it imports the same helpers the gates use:
`validate_schema.record_hash/claim_content_hash/file_content_hash` and the `answer_layer.Live`
ref-hash conventions; it does not reinvent them).

Binding conventions filled (answer_layer.Live):
  manifest marker.claim_hash        -> claim_content_hash(claim)      (status-excluded)
  pack/manifest/visual cea·obs·pred·claim·geo ref.record_hash -> record_hash(record)
  artifact ref.content_hash         -> evidence.content_hash         (external digest, carried)
  visual ref.record_hash            -> visual.spec_hash               (the visual's self-hash)
  pack.pack_hash / analysis.manifest_hash / visual.spec_hash -> record_hash(self, exclude=self)
  analysis.output_hash              -> file_content_hash(<root>/output_path)
  analysis.context_pack_hash        -> the referenced pack's pack_hash

A ref that does not resolve to a live record is an authoring error: `fill_root` reports it and writes
nothing (fail-closed). Filling is idempotent — a ref's own value never feeds its hash, so re-running
yields byte-identical files. Fill order is visuals -> packs -> analyses (a manifest reads the pack's
and visuals' self-hashes).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import answer_layer as al  # noqa: E402
import validate_schema as vs  # noqa: E402
import yaml  # noqa: E402

Live = al.Live


def _fill_refs(refs, resolver, field, hash_fn, missing):
    """Set ref[field] = hash_fn(live record) for each ref; record any id that does not resolve."""
    for ref in refs or []:
        if not isinstance(ref, dict):
            continue  # malformed entry — the schema gate flags it; don't crash
        rec = resolver.get(ref.get("id"))
        if rec is None:
            missing.append(ref.get("id"))
            continue
        ref[field] = hash_fn(rec)


def fill_visual(vis: dict, live: Live) -> list:
    missing = []
    _fill_refs(vis.get("input_claim_refs"), live.claims, "record_hash", Live.record_ref_hash, missing)
    _fill_refs(vis.get("input_claim_evidence_assessment_refs"), live.cea, "record_hash", Live.record_ref_hash, missing)
    _fill_refs(vis.get("input_observation_refs"), live.observations, "record_hash", Live.record_ref_hash, missing)
    _fill_refs(vis.get("input_prediction_refs"), live.predictions, "record_hash", Live.record_ref_hash, missing)
    _fill_refs(vis.get("input_geography_refs"), live.geography, "record_hash", Live.record_ref_hash, missing)
    vis["spec_hash"] = vs.record_hash(vis, exclude=("spec_hash",))
    return missing


def fill_pack(pack: dict, live: Live) -> list:
    missing = []
    _fill_refs(pack.get("claim_refs"), live.claims, "record_hash", Live.record_ref_hash, missing)
    _fill_refs(pack.get("assessment_refs"), live.cea, "record_hash", Live.record_ref_hash, missing)
    _fill_refs(pack.get("artifact_refs"), live.evidence, "content_hash", Live.artifact_ref_hash, missing)
    _fill_refs(pack.get("observation_refs"), live.observations, "record_hash", Live.record_ref_hash, missing)
    _fill_refs(pack.get("prediction_refs"), live.predictions, "record_hash", Live.record_ref_hash, missing)
    pack["pack_hash"] = vs.record_hash(pack, exclude=("pack_hash",))
    return missing


def fill_manifest(ana: dict, live: Live, root: Path) -> list:
    missing = []
    for mk in (ana.get("claim_markers") or {}).values():
        claim = live.claims.get(mk.get("claim_id")) if isinstance(mk, dict) else None
        if claim is None:
            missing.append(mk.get("claim_id") if isinstance(mk, dict) else mk)
            continue
        mk["claim_hash"] = Live.claim_marker_hash(claim)
    _fill_refs(ana.get("claim_evidence_assessment_refs"), live.cea, "record_hash", Live.record_ref_hash, missing)
    _fill_refs(ana.get("artifact_refs"), live.evidence, "content_hash", Live.artifact_ref_hash, missing)
    _fill_refs(ana.get("observation_refs"), live.observations, "record_hash", Live.record_ref_hash, missing)
    _fill_refs(ana.get("prediction_refs"), live.predictions, "record_hash", Live.record_ref_hash, missing)
    _fill_refs(ana.get("visual_refs"), live.visuals, "record_hash", Live.visual_ref_hash, missing)
    if ana.get("output_path"):
        op = root / ana["output_path"]
        if op.is_file():
            ana["output_hash"] = vs.file_content_hash(op)
        else:
            missing.append(ana["output_path"])
    pack = live.context_packs.get(ana.get("context_pack_id"))
    if pack is None:
        missing.append(ana.get("context_pack_id"))
    else:
        ana["context_pack_hash"] = vs.record_hash(pack, exclude=("pack_hash",))
    ana["manifest_hash"] = vs.record_hash(ana, exclude=("manifest_hash",))
    return missing


# registry file -> (collection key, per-record filler) in dependency order (visuals -> packs -> analyses)
_REGISTRIES = [
    ("visuals.yaml", "visuals", lambda rec, live, root: fill_visual(rec, live)),
    ("context_packs.yaml", "context_packs", lambda rec, live, root: fill_pack(rec, live)),
    ("analyses.yaml", "analyses", fill_manifest),
]


def fill_root(root: Path):
    """Fill every answer-layer registry under <root>/factbase, writing back only if all refs resolve.
    Returns (exit_code, missing_by_file, filled_counts)."""
    root = Path(root)
    fb = root / "factbase"
    live = Live(root)
    missing_by_file, to_write, filled = {}, [], {}
    for fname, key, filler in _REGISTRIES:
        path = fb / fname
        if not path.is_file():
            continue
        doc = vs.load_yaml_strict(path) or {}
        recs = doc.get(key) or []
        miss = []
        for rec in recs:
            if isinstance(rec, dict):
                miss += filler(rec, live, root)
        if miss:
            missing_by_file[fname] = [m for m in miss if m]
        # refresh the resolver for this answer-layer collection so a LATER manifest reads the FILLED
        # packs'/visuals' self-hashes (the factbase records `live` resolves are untouched by filling).
        if key in ("visuals", "context_packs"):
            setattr(live, key, al._by_id(recs))
        to_write.append((path, doc))
        filled[fname] = len(recs)
    if missing_by_file:
        return 1, missing_by_file, filled
    for path, doc in to_write:
        path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
    return 0, {}, filled


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP-AL.1 — fill answer-layer binding hashes from live records")
    p.add_argument("--root", default=".", help="corpus root containing factbase/ (default: .)")
    args = p.parse_args(argv)
    code, missing, filled = fill_root(Path(args.root))
    if code != 0:
        print("[answer_build] NOT written — unresolved refs (fail closed):", file=sys.stderr)
        for f, ids in missing.items():
            print(f"  {f}: {ids}", file=sys.stderr)
        return code
    print(f"[answer_build] OK — filled answer-layer hashes under {args.root}/factbase: "
          + ", ".join(f"{k}={v}" for k, v in filled.items() if v))
    return 0


if __name__ == "__main__":
    sys.exit(main())

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
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import answer_layer as al  # noqa: E402
import validate_high_impact as v_hi  # noqa: E402
import validate_schema as vs  # noqa: E402
import verify  # noqa: E402
import yaml  # noqa: E402

Live = al.Live


def _slug(text, n=6):
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return "-".join(words[:n])[:48] or "x"


def _fresh_id(base, taken):
    if base not in taken:
        return base
    k = 2
    while f"{base}-v{k}" in taken:
        k += 1
    return f"{base}-v{k}"


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
    op_rel = ana.get("output_path")
    if op_rel:
        op = root / op_rel
        if op.is_file():
            ana["output_hash"] = vs.file_content_hash(op)
        else:
            missing.append(op_rel)
    else:
        # a falsy output_path passes the closed schema (key present, no traversal) but binds no
        # file — fail closed so output_hash can never be left stale/unbound while fill reports clean
        missing.append("output_path: missing/empty (answer text would be unbound)")
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


def scaffold_manifest(spec: dict, live: Live, root: Path):
    """WP-AL.3 — emit an ANSWER-lifecycle analysis manifest from a small author spec
    {question, context_pack_id, output_path, markers:{marker->claim_id}, [required_refuter_class]}.
    Carries the named pack's cea/artifact/observation/prediction refs; markers bind claim_content_hash;
    output_hash/context_pack_hash/manifest_hash filled via the AL.1 helper. REFUSES (returns problems)
    if a marked claim is high-impact but lacks an impact_category (no laundering a high-impact claim
    into an answer without its category). Returns (manifest|None, problems)."""
    pack = live.context_packs.get(spec.get("context_pack_id"))
    if pack is None:
        return None, [f"context pack {spec.get('context_pack_id')!r} not found"]
    markers = spec.get("markers") or {}
    if not markers:
        return None, ["spec needs a non-empty markers map (marker -> claim_id)"]
    problems = []
    for m, cid in markers.items():
        claim = live.claims.get(cid)
        if claim is None:
            problems.append(f"marker {m!r}: claim {cid!r} not found in the corpus")
        elif claim.get("high_impact") and claim.get("impact_category") in (None, "NONE"):
            problems.append(f"marker {m!r}: claim {cid!r} is high_impact but has no impact_category "
                            "(refusing to land a high-impact claim in an answer without its category)")
    if problems:
        return None, problems
    ana = {
        "id": _fresh_id(f"ana-{_slug(spec['question'])}", set(live.analyses)),
        "lifecycle": "ANSWER",
        "question": spec["question"],
        "context_pack_id": pack["id"],
        "context_pack_hash": None,
        "output_path": spec["output_path"],
        "output_hash": None,
        "claim_markers": {m: {"claim_id": cid, "claim_hash": None} for m, cid in markers.items()},
        "claim_evidence_assessment_refs": [dict(r) for r in pack.get("assessment_refs") or []],
        "artifact_refs": [dict(r) for r in pack.get("artifact_refs") or []],
        "observation_refs": [dict(r) for r in pack.get("observation_refs") or []],
        "prediction_refs": [dict(r) for r in pack.get("prediction_refs") or []],
        "visual_refs": [],
        "required_refuter_class": spec.get("required_refuter_class", "HUMAN_OR_DIFFERENT_MODEL"),
        "manifest_hash": None,
    }
    fill_manifest(ana, live, root)
    return ana, []


def _append_record(path: Path, collection: str, record: dict):
    doc = (vs.load_yaml_strict(path) if path.is_file() else None) or {"schema_version": "2.0", collection: []}
    doc.setdefault(collection, []).append(record)
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))
    return doc


def _drop_record(path: Path, collection: str, rec_id: str, doc: dict):
    doc[collection] = [r for r in doc[collection] if r.get("id") != rec_id]
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))


def scaffold_refuter(ana: dict, live: Live, as_of: str, triggers=None):
    """WP-AL.4 — emit a refuter stub whose COVERAGE is correct-by-construction (the gate-computed
    required claim+assessment scope) but whose JUDGMENT is left for an independent reviewer:
    reviewer_class=SAME_MODEL_FRESH_CONTEXT (never independent, §10) and every verdict=REVISE, so an
    UNFILLED scaffold fails `verify.py --mode answer` closed. The reviewer (a human or different model)
    flips reviewer_class to HUMAN/DIFFERENT_MODEL/MIXED and each verdict to SURVIVES (running the
    checks) to certify. Returns (refuter, floor) where floor lists any required factual claim lacking a
    scored support (the answer cannot commit until that is fixed). high_impact is pre-set per claim so
    the reviewer need not recompute it."""
    triggers = triggers if triggers is not None else v_hi.trigger_set()
    required_claims, required_ceas, floor = verify._gate_computed_refuter_scope(ana, live)
    verdicts = []
    for cid in sorted(required_claims):
        claim = live.claims.get(cid) or {}
        computed, _ = v_hi.compute_high_impact(claim, triggers)
        verdicts.append({
            "claim_id": cid, "verdict": "REVISE",  # non-SURVIVES placeholder → blocks the answer until signed
            "high_impact": bool(computed or claim.get("high_impact") is True),
            "displacement_check": "NOT_APPLICABLE", "independence_check": "NOT_APPLICABLE",
            "freshness_check": "NOT_APPLICABLE", "observation_check": "NOT_APPLICABLE",
            "reasoning_check": "NOT_APPLICABLE",
            "notes": "TODO (independent reviewer): run displacement/independence/freshness/observation/"
                     "reasoning, add disconfirming searches for any high-impact claim, then set SURVIVES "
                     "or an honest REVISE/DOWNGRADE/REJECT.",
        })
    base = ana["id"][4:] if ana["id"].startswith("ana-") else ana["id"]
    refuter = {
        "id": _fresh_id(f"ref-{base}", set(live.refuters)),
        "analysis_id": ana["id"],
        "manifest_hash": ana.get("manifest_hash"),
        "output_hash": ana.get("output_hash"),
        "reviewer_class": "SAME_MODEL_FRESH_CONTEXT",  # NOT independent → fails closed until a human/different model signs
        "reviewer": "UNSIGNED-independent-review-required",
        "reviewed_at": as_of,
        "reviewed_claim_ids": sorted(required_claims),
        "reviewed_assessment_ids": sorted(required_ceas),
        "verdicts": verdicts,
        "alternative_hypotheses": [],
        "disconfirming_searches": [],  # the reviewer adds real searches (required for high-impact claims)
        "unresolved_gaps": [],
        "exemptions_reviewed": sorted(ana.get("narrative_exemptions") or []),
    }
    return refuter, floor


def _cmd_refuter(args) -> int:
    root = Path(args.root)
    live = Live(root)
    ana = live.analyses.get(args.analysis)
    if ana is None:
        print(f"[answer_build refuter] analysis {args.analysis!r} not found", file=sys.stderr)
        return 2
    if live.refuter_for_analysis(args.analysis) is not None:
        print(f"[answer_build refuter] a refuter already binds {args.analysis!r} (one per analysis)",
              file=sys.stderr)
        return 1
    refuter, floor = scaffold_refuter(ana, live, args.as_of)
    rpath = root / "factbase" / "refuters.yaml"
    doc = _append_record(rpath, "refuters", refuter)
    sc, sf = vs.validate_file(rpath)
    if sc != 0:
        _drop_record(rpath, "refuters", refuter["id"], doc)
        print("\n".join(sf), file=sys.stderr)
        print(f"\n[answer_build refuter] NOT persisted — scaffold does not schema-validate (exit {sc}).",
              file=sys.stderr)
        return sc
    print(f"[answer_build refuter] OK — scaffolded {refuter['id']!r} (UNSIGNED): covers "
          f"{len(refuter['reviewed_claim_ids'])} claim(s) / {len(refuter['reviewed_assessment_ids'])} "
          f"assessment(s). reviewer_class=SAME_MODEL_FRESH_CONTEXT + verdicts=REVISE → fails `--mode "
          f"answer` until an independent reviewer (HUMAN/DIFFERENT_MODEL/MIXED) signs.")
    if floor:
        print("[answer_build refuter] NOTE — support floor not met for: "
              + "; ".join(floor) + " (the answer cannot commit until fixed via fact.py supersede).")
    return 0


def _cmd_fill(args) -> int:
    code, missing, filled = fill_root(Path(args.root))
    if code != 0:
        print("[answer_build fill] NOT written — unresolved refs (fail closed):", file=sys.stderr)
        for f, ids in missing.items():
            print(f"  {f}: {ids}", file=sys.stderr)
        return code
    print(f"[answer_build fill] OK — filled answer-layer hashes under {args.root}/factbase: "
          + ", ".join(f"{k}={v}" for k, v in filled.items() if v))
    return 0


def _cmd_manifest(args) -> int:
    root = Path(args.root)
    spec = vs.load_yaml_strict(Path(args.spec))
    try:
        ana, problems = scaffold_manifest(spec, Live(root), root)
    except (KeyError, ValueError) as e:
        print(f"[answer_build manifest] spec error: {e}", file=sys.stderr)
        return 2
    if problems:
        for p in problems:
            print(f"[answer_build manifest] {p}", file=sys.stderr)
        return 1
    apath = root / "factbase" / "analyses.yaml"
    doc = _append_record(apath, "analyses", ana)  # write, then prove it composes in --mode draft
    code, lines = verify.draft_check(root, ana["id"], args.as_of)
    if code != 0:
        _drop_record(apath, "analyses", ana["id"], doc)  # fail-closed rollback
        print("\n".join(lines[-6:]), file=sys.stderr)
        print(f"\n[answer_build manifest] NOT persisted — does not compose in --mode draft (exit {code}). "
              f"(check the [[markers]] in {spec.get('output_path')!r} match the marker map.)", file=sys.stderr)
        return code
    print(f"[answer_build manifest] OK — {ana['id']!r} composes in --mode draft. persisted under "
          f"{root}/factbase/analyses.yaml")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="answer-authoring helper (fill / manifest / refuter)")
    sub = p.add_subparsers(dest="cmd", required=True)
    pf = sub.add_parser("fill", help="fill answer-layer binding hashes from live records (AL.1)")
    pf.add_argument("--root", default=".")
    pf.set_defaults(fn=_cmd_fill)
    pm = sub.add_parser("manifest", help="scaffold an ANSWER manifest from a spec + author output.md (AL.3)")
    pm.add_argument("spec", help="manifest spec YAML (question/context_pack_id/output_path/markers)")
    pm.add_argument("--root", default=".")
    pm.add_argument("--as-of", required=True)
    pm.set_defaults(fn=_cmd_manifest)
    pr = sub.add_parser("refuter", help="scaffold a gate-scoped, UNSIGNED refuter for an analysis (AL.4)")
    pr.add_argument("--analysis", required=True)
    pr.add_argument("--root", default=".")
    pr.add_argument("--as-of", required=True)
    pr.set_defaults(fn=_cmd_refuter)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

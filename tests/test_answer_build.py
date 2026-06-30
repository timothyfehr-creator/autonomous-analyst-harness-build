"""WP-AL.1 — the answer-authoring hash-fill helper. Tests run on an ISOLATED tmp_path staged from the
skeleton fixtures (never mutating tests/fixtures/skeleton or private/corpus): zero the answer-layer
binding hashes, fill from live records, and prove draft-clean + idempotent + the pack/marker hash split
+ that a source-record change is tracked by a re-fill."""
import pathlib
import shutil
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import answer_build  # noqa: E402
import fact  # noqa: E402
import validate_schema as vs  # noqa: E402
import verify  # noqa: E402

SK = ROOT / "tests" / "fixtures" / "skeleton"
ASOF = "2026-06-23T00:00:00Z"
_MAP = {
    "skeleton_sources.yaml": "sources.yaml", "skeleton_source_assessments.yaml": "source_assessments.yaml",
    "skeleton_evidence.yaml": "evidence.yaml", "skeleton_claim_evidence.yaml": "claim_evidence.yaml",
    "skeleton_claims.yaml": "baseline/claims.yaml", "skeleton_predictions.yaml": "predictions.yaml",
    "skeleton_observations.yaml": "observations.yaml", "skeleton_geography.yaml": "geography.yaml",
    "skeleton_context_pack.yaml": "context_packs.yaml", "skeleton_analysis.yaml": "analyses.yaml",
    "skeleton_refuter.yaml": "refuters.yaml", "skeleton_visual.yaml": "visuals.yaml",
}
ZERO = "sha256:" + "0" * 64


def _stage(root):
    fb = root / "factbase"
    (fb / "baseline").mkdir(parents=True)
    (fb / "live").mkdir(parents=True)
    for src, dst in _MAP.items():
        shutil.copy(SK / src, fb / dst)
    (fb / "live" / "claims.yaml").write_text('schema_version: "2.0"\nclaims: []\n')
    (root / "outputs").mkdir()
    shutil.copy(SK / "skeleton_output.md", root / "outputs" / "ana-skeleton.md")
    return fb


def _zero_answer_layer(fb):
    """Blank every binding hash in the answer layer (the state an author would hand us)."""
    import re
    for f in ("context_packs.yaml", "analyses.yaml", "visuals.yaml"):
        p = fb / f
        p.write_text(re.sub(r"sha256:[0-9a-f]{64}", ZERO, p.read_text()))


def _read(p):
    return (vs.load_yaml_strict(p) or {})


def test_fill_makes_draft_clean_and_is_idempotent(tmp_path):
    fb = _stage(tmp_path)
    _zero_answer_layer(fb)
    code, missing, filled = answer_build.fill_root(tmp_path)
    assert code == 0 and not missing, missing
    # the filled answer layer composes through the real draft gate
    dcode, lines = verify.draft_check(tmp_path, "ana-skeleton", ASOF)
    assert dcode == 0, lines[-4:]
    # idempotent: a second fill is byte-for-byte identical
    before = {f: (fb / f).read_bytes() for f in ("context_packs.yaml", "analyses.yaml", "visuals.yaml")}
    assert answer_build.fill_root(tmp_path)[0] == 0
    after = {f: (fb / f).read_bytes() for f in ("context_packs.yaml", "analyses.yaml", "visuals.yaml")}
    assert before == after


def test_pack_uses_record_hash_marker_uses_claim_content_hash(tmp_path):
    fb = _stage(tmp_path)
    _zero_answer_layer(fb)
    assert answer_build.fill_root(tmp_path)[0] == 0
    claim = _read(fb / "baseline" / "claims.yaml")["claims"][0]
    cid = claim["id"]
    pack = _read(fb / "context_packs.yaml")["context_packs"][0]
    ana = _read(fb / "analyses.yaml")["analyses"][0]
    pack_ref = next(r for r in pack["claim_refs"] if r["id"] == cid)
    marker = next(m for m in ana["claim_markers"].values() if m["claim_id"] == cid)
    # the SAME claim: pack ref binds the FULL record_hash, the manifest marker binds the content hash
    assert pack_ref["record_hash"] == vs.record_hash(claim)
    assert marker["claim_hash"] == vs.claim_content_hash(claim)
    assert vs.record_hash(claim) != vs.claim_content_hash(claim)  # the trap: they must differ


def test_unresolved_ref_fails_closed_and_writes_nothing(tmp_path):
    fb = _stage(tmp_path)
    _zero_answer_layer(fb)
    p = fb / "context_packs.yaml"
    doc = _read(p)
    doc["context_packs"][0]["claim_refs"].append({"id": "clm-does-not-exist", "record_hash": ZERO})
    p.write_text(yaml.safe_dump(doc, sort_keys=False))
    before = p.read_bytes()
    code, missing, _ = answer_build.fill_root(tmp_path)
    assert code == 1 and "clm-does-not-exist" in missing.get("context_packs.yaml", [])
    assert p.read_bytes() == before  # fail-closed: nothing written


def test_refill_tracks_a_changed_source_record(tmp_path):
    fb = _stage(tmp_path)
    _zero_answer_layer(fb)
    assert answer_build.fill_root(tmp_path)[0] == 0
    h_before = _read(fb / "analyses.yaml")["analyses"][0]["manifest_hash"]
    # change a source claim's content, then re-fill: the chain must move (not be frozen to the old state)
    cp = fb / "baseline" / "claims.yaml"
    doc = _read(cp)
    doc["claims"][0]["text"] = doc["claims"][0]["text"] + " (edited)"
    cp.write_text(yaml.safe_dump(doc, sort_keys=False))
    assert answer_build.fill_root(tmp_path)[0] == 0
    assert _read(fb / "analyses.yaml")["analyses"][0]["manifest_hash"] != h_before


# ---- WP-AL.3: manifest scaffold ----
def _w(tmp, name, obj):
    p = tmp / name
    p.write_text(yaml.safe_dump(obj, sort_keys=False))
    return str(p)


def _corpus_with_pack(tmp):
    spec = {"source": {"id": "src-ref", "title": "Ref", "source_type": "REFERENCE"},
            "artifact": {"artifact_type": "ARTICLE", "url": "https://x.invalid", "retrieved_at": ASOF,
                         "text": "The Example Bridge connects town A and town B."},
            "claim": {"text": "The Example Bridge connects town A and town B.", "topics": ["geography"],
                      "stability": "DURABLE", "review_by": "2027-06-28"},
            "assessment": {"quote": "The Example Bridge connects town A and town B", "summary": "lead",
                           "information_credibility": 2, "reviewer": "model:test"}}
    assert fact.main(["--root", str(tmp), "add", _w(tmp, "f.yaml", spec), "--as-of", ASOF]) == 0
    assert fact.main(["--root", str(tmp), "context", "--topic", "geography",
                      "--query", "What does the Example Bridge connect?", "--as-of", ASOF]) == 0
    pack_id = _read(tmp / "factbase" / "context_packs.yaml")["context_packs"][0]["id"]
    claim_id = _read(tmp / "factbase" / "baseline" / "claims.yaml")["claims"][0]["id"]
    return pack_id, claim_id


def test_manifest_scaffold_composes_in_draft(tmp_path):
    pack_id, claim_id = _corpus_with_pack(tmp_path)
    (tmp_path / "outputs").mkdir(exist_ok=True)
    (tmp_path / "outputs" / "ana-bridge.md").write_text(
        "The Example Bridge connects town A and town B. [[c1]]\n")
    spec = {"question": "What does the Example Bridge connect?", "context_pack_id": pack_id,
            "output_path": "outputs/ana-bridge.md", "markers": {"c1": claim_id}}
    code = answer_build.main(["manifest", _w(tmp_path, "m.yaml", spec), "--root", str(tmp_path), "--as-of", ASOF])
    assert code == 0
    ana = _read(tmp_path / "factbase" / "analyses.yaml")["analyses"][0]
    assert ana["lifecycle"] == "ANSWER" and ana["manifest_hash"].startswith("sha256:")
    assert ana["claim_markers"]["c1"]["claim_hash"].startswith("sha256:")
    assert ana["context_pack_hash"].startswith("sha256:") and ana["output_hash"].startswith("sha256:")


def test_manifest_refuses_high_impact_without_category(tmp_path):
    pack_id, claim_id = _corpus_with_pack(tmp_path)
    live = answer_build.Live(tmp_path)
    live.claims[claim_id]["high_impact"] = True       # simulate a high-impact claim...
    live.claims[claim_id]["impact_category"] = "NONE"  # ...lacking its category
    spec = {"question": "q", "context_pack_id": pack_id, "output_path": "outputs/x.md",
            "markers": {"c1": claim_id}}
    ana, problems = answer_build.scaffold_manifest(spec, live, tmp_path)
    assert ana is None and any("high_impact" in p for p in problems)

"""R5 — the Milestone-A synthetic skeleton is the assembly oracle.

A single referentially-consistent synthetic chain (source → assessment → evidence →
claim-evidence → claim → observation/geography → prediction/events → context pack → analysis →
refuter → visual). At Phase 1 it must validate through EVERY registered schema (shape). As of
WP3.0 the ANSWER-LAYER hash chain is REAL (computed, not placeholder): pack_hash, manifest_hash,
spec_hash, output_hash, and the marker/ref hashes all recompute (see test_*_hash_chain_is_real).
The only placeholder left is `evidence.content_hash`, an EXTERNAL artifact byte digest not
derivable from the record.

This test guards the oracle three ways: (1) every file is schema-clean; (2) the oracle stays
COMPLETE — it must cover every factbase collection, so adding a schema without extending the
skeleton turns this red; (3) the answer-layer hash chain is self-consistent (R5 → Phase-3 upgrade).
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import hash_chain as hc  # noqa: E402
import validate_schema as vs  # noqa: E402

SK = ROOT / "tests" / "fixtures" / "skeleton"

# Every factbase collection the Milestone-A chain must exercise (unit_vocabulary is config, not a
# factbase record, so it is intentionally excluded; the two append-only logs are included).
EXPECTED_COVERAGE = {
    "sources", "groups", "source_assessments", "evidence", "claim_evidence_assessments",
    "claims", "observations", "geography", "predictions", "context_packs", "analyses",
    "refuters", "visuals",
}
EXPECTED_EVENT_LOGS = {"prediction_events", "baseline_events"}


def _load(name):
    return vs.load_yaml_strict(SK / name)


def test_every_skeleton_file_is_schema_clean():
    for path in sorted(SK.glob("*.yaml")) + sorted(SK.glob("*.jsonl")):
        assert vs.main([str(path)]) == 0, f"{path.name} did not validate clean"


def test_skeleton_covers_every_factbase_collection():
    seen = set()
    for path in SK.glob("*.yaml"):
        data = _load(path.name)
        seen |= {k for k in data if k != "schema_version"}
    missing = EXPECTED_COVERAGE - seen
    assert not missing, f"skeleton oracle is missing collections: {sorted(missing)}"
    logs = {p.stem.replace("skeleton_", "") for p in SK.glob("*.jsonl")}
    assert EXPECTED_EVENT_LOGS <= logs, f"skeleton missing event logs: {sorted(EXPECTED_EVENT_LOGS - logs)}"


def test_skeleton_is_referentially_consistent():
    # the oracle's own internal references must resolve (a typo'd oracle is a bad oracle)
    claim = _load("skeleton_claims.yaml")["claims"][0]
    evd = _load("skeleton_evidence.yaml")["evidence"][0]
    cea = _load("skeleton_claim_evidence.yaml")["claim_evidence_assessments"][0]
    obs = _load("skeleton_observations.yaml")["observations"][0]
    geo = _load("skeleton_geography.yaml")["geography"][0]
    ana = _load("skeleton_analysis.yaml")["analyses"][0]
    ref = _load("skeleton_refuter.yaml")["refuters"][0]
    vis = _load("skeleton_visual.yaml")["visuals"][0]

    assert cea["claim_id"] == claim["id"]
    assert cea["artifact_id"] == evd["id"]
    assert obs["claim_id"] == claim["id"]
    assert cea["id"] in obs["claim_evidence_assessment_ids"]
    assert geo["geometry_claim_id"] == claim["id"]
    assert ref["analysis_id"] == ana["id"]
    # the refuter binds to the analysis manifest/output by hash
    assert ref["manifest_hash"] == ana["manifest_hash"]
    assert ref["output_hash"] == ana["output_hash"]
    # the refuter covers exactly the manifest's claim/assessment sets (Phase-3 enforces; here we
    # assert the oracle is already coverage-consistent so Phase-3 has a passing example)
    assert set(ref["reviewed_claim_ids"]) == {m["claim_id"] for m in ana["claim_markers"].values()}
    assert {r["id"] for r in ana["claim_evidence_assessment_refs"]} == set(ref["reviewed_assessment_ids"])
    # the visual's observation input resolves to the chain's observation
    assert any(r["id"] == obs["id"] for r in vis["input_observation_refs"])


def test_answer_layer_hash_chain_is_real():
    # WP3.0 (R5 → Phase-3): the answer-layer hashes are computed, not placeholder. Each binding
    # recomputes from the actual records, so a Phase-3 hashing mistake turns THIS red.
    claim = _load("skeleton_claims.yaml")["claims"][0]
    cea = _load("skeleton_claim_evidence.yaml")["claim_evidence_assessments"][0]
    obs = _load("skeleton_observations.yaml")["observations"][0]
    pack = _load("skeleton_context_pack.yaml")["context_packs"][0]
    ana = _load("skeleton_analysis.yaml")["analyses"][0]
    vis = _load("skeleton_visual.yaml")["visuals"][0]
    cc = vs.claim_content_hash(claim)

    # marker + cea bind the CLAIM-CONTENT hash (stable across re-review), distinct from the full record hash
    assert ana["claim_markers"]["c1"]["claim_hash"] == cc
    assert cea["semantic_review"]["claim_content_hash"] == cc
    assert vs.record_hash(claim) != cc  # distinct roles
    # manifest refs bind real record hashes / the external content hash / the visual spec hash
    assert ana["claim_evidence_assessment_refs"][0]["record_hash"] == vs.record_hash(cea)
    assert ana["observation_refs"][0]["record_hash"] == vs.record_hash(obs)
    assert ana["visual_refs"][0]["record_hash"] == vis["spec_hash"]
    # the self-hashes recompute (pack/manifest/spec) and the output hash binds the prose bytes
    assert ana["context_pack_hash"] == hc.pack_hash(pack)
    assert ana["manifest_hash"] == hc.manifest_hash(ana)
    assert vis["spec_hash"] == hc.spec_hash(vis)
    assert ana["output_hash"] == vs.file_content_hash(SK / "skeleton_output.md")

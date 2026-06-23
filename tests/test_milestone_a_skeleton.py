"""R5 — the Milestone-A synthetic skeleton is the assembly oracle.

A single referentially-consistent synthetic chain (source → assessment → evidence →
claim-evidence → claim → observation/geography → prediction/events → analysis → refuter →
visual). At Phase 1 it must validate through EVERY registered schema (shape). Cross-record
resolution + true record-hash matching are Phase-2/3; the synthetic hashes here are format-valid
placeholders (real record_hash values get computed when the Phase-2 hash gate lands).

This test guards the oracle two ways: (1) every file is schema-clean; (2) the oracle stays
COMPLETE — it must cover every factbase collection, so adding a schema without extending the
skeleton turns this red.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_schema as vs  # noqa: E402

SK = ROOT / "tests" / "fixtures" / "skeleton"

# Every factbase collection the Milestone-A chain must exercise (unit_vocabulary is config, not a
# factbase record, so it is intentionally excluded; the two append-only logs are included).
EXPECTED_COVERAGE = {
    "sources", "groups", "source_assessments", "evidence", "claim_evidence_assessments",
    "claims", "observations", "geography", "predictions", "analyses", "refuters", "visuals",
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

"""WP3.1 — verify.py --mode draft. Composes records + analysis-manifest structural integrity +
context-pack integrity, scoped to a selected analysis. Fail-closed: empty/upstream-2 propagates;
a REQUIRED control that cannot run (missing analysis / referenced pack) is exit 2; SKIP is not PASS.
"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import verify  # noqa: E402

SK = ROOT / "tests" / "fixtures" / "skeleton"
ASOF = "2026-06-23T00:00:00Z"

# skeleton flat file -> factbase tree location (factbase records + answer-layer registries)
_MAP = {
    "skeleton_sources.yaml": "sources.yaml",
    "skeleton_source_assessments.yaml": "source_assessments.yaml",
    "skeleton_evidence.yaml": "evidence.yaml",
    "skeleton_claim_evidence.yaml": "claim_evidence.yaml",
    "skeleton_claims.yaml": "baseline/claims.yaml",
    "skeleton_predictions.yaml": "predictions.yaml",
    "skeleton_observations.yaml": "observations.yaml",
    "skeleton_geography.yaml": "geography.yaml",
    "skeleton_context_pack.yaml": "context_packs.yaml",
    "skeleton_analysis.yaml": "analyses.yaml",
    "skeleton_refuter.yaml": "refuters.yaml",
    "skeleton_visual.yaml": "visuals.yaml",
}


def _stage(root):
    fb = root / "factbase"
    (fb / "baseline").mkdir(parents=True)
    (fb / "live").mkdir(parents=True)
    for src, dst in _MAP.items():
        shutil.copy(SK / src, fb / dst)
    (fb / "live" / "claims.yaml").write_text('schema_version: "2.0"\nclaims: []\n')
    return fb


def _draft(root, analysis=None):
    return verify.draft_check(root, analysis, ASOF)


def test_draft_composes_clean_with_analysis(tmp_path):
    _stage(tmp_path)
    code, lines = _draft(tmp_path, "ana-skeleton")
    assert code == 0, "\n".join(lines)
    joined = "\n".join(lines)
    assert "STRUCTURAL + REVIEWABLE, NOT TRUE" in joined  # banner always present
    assert "PASS" not in joined  # a draft must never read as a verification PASS


def test_draft_without_analysis_is_records_plus_skip(tmp_path):
    _stage(tmp_path)
    code, lines = _draft(tmp_path, None)
    assert code == 0
    assert any("[skip] manifest_structural" in ln for ln in lines)
    assert "PASS" not in "\n".join(lines)  # a SKIP line must never reintroduce the token PASS


def test_draft_empty_factbase_fails_closed():
    # the real seed factbase has zero claims → records empties → draft halts at 2 (R3)
    code, lines = _draft(ROOT, "ana-skeleton")
    assert code == 2 and "records cannot run" in "\n".join(lines)


def test_draft_missing_analysis_is_exit2(tmp_path):
    _stage(tmp_path)
    code, lines = _draft(tmp_path, "ana-does-not-exist")
    assert code == 2 and "not found" in "\n".join(lines)


def test_draft_referenced_pack_missing_is_exit2(tmp_path):
    fb = _stage(tmp_path)
    # drop the context pack the manifest references → a REQUIRED control cannot run → 2
    (fb / "context_packs.yaml").write_text('schema_version: "2.0"\ncontext_packs: []\n')
    code, lines = _draft(tmp_path, "ana-skeleton")
    assert code == 2 and "does not resolve" in "\n".join(lines)


def test_draft_stale_manifest_ref_hash_is_finding(tmp_path):
    fb = _stage(tmp_path)
    # tamper the manifest's cea ref hash → manifest_structural finding (exit 1, in valid input)
    t = (fb / "analyses.yaml").read_text()
    good = t.split("record_hash: ")[1][:71]  # first ref hash in the manifest
    t = t.replace(good, "sha256:" + "0" * 64, 1)
    (fb / "analyses.yaml").write_text(t)
    code, lines = _draft(tmp_path, "ana-skeleton")
    assert code == 1 and any("[manifest]" in ln and "stale" in ln for ln in lines), "\n".join(lines)


def test_draft_stale_pack_ref_hash_is_finding(tmp_path):
    fb = _stage(tmp_path)
    t = (fb / "context_packs.yaml").read_text()
    good = t.split("record_hash: ")[1][:71]
    t = t.replace(good, "sha256:" + "0" * 64, 1)
    (fb / "context_packs.yaml").write_text(t)
    code, lines = _draft(tmp_path, "ana-skeleton")
    assert code == 1 and any("[context_pack]" in ln and "stale" in ln for ln in lines), "\n".join(lines)


def test_draft_upstream_records_failure_propagates_exit2(tmp_path):
    fb = _stage(tmp_path)
    # break an upstream records layer (unknown schema_version) → records 2 → draft 2 (not masked)
    (fb / "claim_evidence.yaml").write_text('schema_version: "9.9"\nclaim_evidence_assessments: []\n')
    code, lines = _draft(tmp_path, "ana-skeleton")
    assert code == 2


def test_draft_malformed_manifest_does_not_crash(tmp_path):
    fb = _stage(tmp_path)
    # a structurally-broken manifest (claim_markers as a list, not a mapping) must produce findings,
    # never an unhandled exception (schema flags it; integrity stays total via isinstance guards)
    (fb / "analyses.yaml").write_text(
        (fb / "analyses.yaml").read_text().replace("claim_markers:\n      c1:",
                                                   "claim_markers:\n      - c1:"))
    code, lines = _draft(tmp_path, "ana-skeleton")
    assert code in (1, 2)  # a finding or fail-closed — but NOT a crash


def test_manifest_observation_backing_must_be_marked():
    # Milestone-A P0 review (feeding-leg seam): an observation_ref whose underlying claim is not a
    # marked claim must fail — a claim the answer leans on must be cited + marked so the refuter
    # covers + contests it.
    import types
    import validate_manifest_structural as vms
    ana = {"claim_markers": {"c1": {"claim_id": "clm-marked", "claim_hash": "h"}},
           "claim_evidence_assessment_refs": [], "observation_refs": [{"id": "obs-1", "record_hash": "h"}],
           "prediction_refs": [], "artifact_refs": [], "visual_refs": [], "manifest_hash": "h"}
    live = types.SimpleNamespace(
        claims={"clm-marked": {"id": "clm-marked"}}, cea={}, predictions={}, evidence={}, visuals={},
        observations={"obs-1": {"id": "obs-1", "claim_id": "clm-UNMARKED"}},
        claim_marker_hash=lambda c: "h", record_ref_hash=lambda r: "h",
        artifact_ref_hash=lambda e: "h", visual_ref_hash=lambda v: "h")
    code, f = vms.validate_manifest_structural(ana, live)
    assert any("not a marked claim" in x and "obs-1" in x for x in f), f


def test_cli_draft_on_staged_root(tmp_path):
    _stage(tmp_path)
    assert verify.main(["--mode", "draft", "--root", str(tmp_path),
                        "--as-of", ASOF, "--analysis", "ana-skeleton"]) == 0

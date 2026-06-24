"""WP3.4 — verify.py --mode answer. The committed-answer composition: draft + output-text binding
(A7 semantic BLOCKS) + required refuter + input-lifecycle reject + visuals. Fail-closed throughout;
--analysis required; a missing refuter is a cannot-run §10 control (exit 2). This is Milestone A.
"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import verify  # noqa: E402

SK = ROOT / "tests" / "fixtures" / "skeleton"
ASOF = "2026-06-23T00:00:00Z"

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
    (root / "outputs").mkdir()
    shutil.copy(SK / "skeleton_output.md", root / "outputs" / "ana-skeleton.md")  # output_path target
    return fb


def _answer(root, analysis="ana-skeleton"):
    return verify.answer_check(root, analysis, ASOF)


def test_answer_composes_clean_milestone_a(tmp_path):
    _stage(tmp_path)
    code, lines = _answer(tmp_path)
    assert code == 0, "\n".join(lines)
    joined = "\n".join(lines)
    assert "VERIFIED PRIVATE answer" in joined and "PASS" not in joined  # never reads as PASS
    assert any("render SKIPPED" in ln for ln in lines)  # WP5 visual skip is allowed, not a pass


def test_answer_requires_analysis(tmp_path):
    _stage(tmp_path)
    code, lines = _answer(tmp_path, None)
    assert code == 2 and "--analysis is required" in "\n".join(lines)


def test_answer_empty_factbase_fails_closed():
    code, lines = _answer(ROOT)
    assert code == 2  # records empties → compose halts


def test_answer_missing_refuter_is_exit2(tmp_path):
    fb = _stage(tmp_path)
    (fb / "refuters.yaml").write_text('schema_version: "2.0"\nrefuters: []\n')
    code, lines = _answer(tmp_path)
    assert code == 2 and "no refuter binds" in "\n".join(lines)


def test_answer_edited_output_breaks_binding(tmp_path):
    _stage(tmp_path)
    (tmp_path / "outputs" / "ana-skeleton.md").write_text("Tampered committed answer. [[c1]]\n")
    code, lines = _answer(tmp_path)
    assert code == 1 and any("[output]" in ln and "output_hash does not bind" in ln for ln in lines)


def test_answer_refuter_coverage_failure_propagates(tmp_path):
    fb = _stage(tmp_path)
    # drop the refuter's reviewed claim → set-equality coverage fails → answer 1
    t = (fb / "refuters.yaml").read_text().replace(
        "reviewed_claim_ids: [clm-skeleton-crossing-modes]", "reviewed_claim_ids: []")
    (fb / "refuters.yaml").write_text(t)
    code, lines = _answer(tmp_path)
    assert code == 1 and any("[refuter]" in ln for ln in lines)


def test_answer_input_lifecycle_helper():
    import types

    def _live(claims, cea=None, packs=None, visuals=None):
        return types.SimpleNamespace(claims={c["id"]: c for c in claims}, cea=cea or {},
                                     context_packs=packs or {}, visuals=visuals or {})

    ana = {"claim_markers": {"c1": {"claim_id": "clm-x", "claim_hash": "h"}},
           "claim_evidence_assessment_refs": [{"id": "cea-x", "record_hash": "h"}],
           "context_pack_id": "ctx-1", "visual_refs": [{"id": "vis-1", "record_hash": "h"}]}
    REVIEWED = {"id": "clm-x", "lifecycle": "REVIEWED", "freshness_status": "CURRENT"}

    # SUPERSEDED via the prose marker
    code, f = verify._answer_input_lifecycle(ana, _live([{**REVIEWED, "lifecycle": "SUPERSEDED"}]))
    assert code == 1 and any("SUPERSEDED" in x for x in f)
    # REVIEW_DUE via the marker (was previously allowed — review fix)
    code, f = verify._answer_input_lifecycle(ana, _live([{**REVIEWED, "freshness_status": "REVIEW_DUE"}]))
    assert code == 1 and any("REVIEW_DUE" in x for x in f)
    # CANDIDATE claim reaching the answer ONLY through the context pack (not a marker) — must be caught
    pack = {"claim_refs": [{"id": "clm-p", "record_hash": "h"}], "assessment_refs": []}
    code, f = verify._answer_input_lifecycle(
        ana, _live([REVIEWED, {"id": "clm-p", "lifecycle": "CANDIDATE", "freshness_status": "CURRENT"}],
                   packs={"ctx-1": pack}))
    assert code == 1 and any("clm-p" in x and "CANDIDATE" in x for x in f)
    # SUPERSEDED claim reaching the answer ONLY through a visual's input_claim_refs — must be caught
    vis = {"input_claim_refs": [{"id": "clm-v", "record_hash": "h"}]}
    code, f = verify._answer_input_lifecycle(
        ana, _live([REVIEWED, {"id": "clm-v", "lifecycle": "SUPERSEDED", "freshness_status": "CURRENT"}],
                   visuals={"vis-1": vis}))
    assert code == 1 and any("clm-v" in x for x in f)
    # a rejected assessment blocks; an all-REVIEWED/CURRENT answer passes
    code, f = verify._answer_input_lifecycle(ana, _live([REVIEWED], cea={"cea-x": {"semantic_review": {"status": "REJECTED"}}}))
    assert code == 1 and any("REJECTED" in x for x in f)
    assert verify._answer_input_lifecycle(ana, _live([REVIEWED]))[0] == 0


def test_cli_answer_on_staged_root(tmp_path):
    _stage(tmp_path)
    assert verify.main(["--mode", "answer", "--root", str(tmp_path),
                        "--as-of", ASOF, "--analysis", "ana-skeleton"]) == 0

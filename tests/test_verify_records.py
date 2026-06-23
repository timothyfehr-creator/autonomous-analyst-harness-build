"""WP2.x — verify.py --mode records composition. Composes the 9 per-snapshot integrity gates in DAG
order with empty-factbase fail-closed (R3) + exit-2 short-circuit propagation + an injectable clock.
The cross-commit reward-hack gate (WP2.2c) is intentionally NOT part of this per-snapshot composer.
"""
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import verify  # noqa: E402

SK = ROOT / "tests" / "fixtures" / "skeleton"
ASOF = "2026-06-23T00:00:00Z"


def _stage(root):
    """Materialize the flat Milestone-A skeleton into a <root>/factbase tree (baseline+live split)."""
    fb = root / "factbase"
    (fb / "baseline").mkdir(parents=True)
    (fb / "live").mkdir(parents=True)
    shutil.copy(SK / "skeleton_sources.yaml", fb / "sources.yaml")
    shutil.copy(SK / "skeleton_source_assessments.yaml", fb / "source_assessments.yaml")
    shutil.copy(SK / "skeleton_evidence.yaml", fb / "evidence.yaml")
    shutil.copy(SK / "skeleton_claim_evidence.yaml", fb / "claim_evidence.yaml")
    shutil.copy(SK / "skeleton_claims.yaml", fb / "baseline" / "claims.yaml")
    (fb / "live" / "claims.yaml").write_text('schema_version: "2.0"\nclaims: []\n')
    shutil.copy(SK / "skeleton_predictions.yaml", fb / "predictions.yaml")
    shutil.copy(SK / "skeleton_observations.yaml", fb / "observations.yaml")
    shutil.copy(SK / "skeleton_geography.yaml", fb / "geography.yaml")
    return fb


def test_real_empty_factbase_fails_closed():
    # the real seed factbase has zero claims → R3 fail-closed
    code, lines = verify.records_check(ROOT, ASOF)
    assert code == 2 and "empty factbase" in "\n".join(lines).lower()


def test_genuinely_empty_root_fails_closed(tmp_path):
    (tmp_path / "factbase" / "baseline").mkdir(parents=True)
    (tmp_path / "factbase" / "live").mkdir(parents=True)
    assert verify.records_check(tmp_path, ASOF)[0] == 2


def test_staged_skeleton_composes_clean(tmp_path):
    _stage(tmp_path)
    code, lines = verify.records_check(tmp_path, ASOF)
    assert code == 0, "\n".join(lines)
    assert "composed clean" in "\n".join(lines)


def test_injected_upstream_failure_propagates_exit2(tmp_path):
    # break the claim_evidence layer (unknown schema_version → gate exit 2); records must HALT at 2,
    # never let a downstream gate's 0/1 mask it (R3 propagation)
    fb = _stage(tmp_path)
    (fb / "claim_evidence.yaml").write_text('schema_version: "9.9"\nclaim_evidence_assessments: []\n')
    code, lines = verify.records_check(tmp_path, ASOF)
    assert code == 2 and "halted" in "\n".join(lines).lower()


def test_single_downstream_finding_propagates_exit1(tmp_path):
    # an over-claimed support_status (CORROBORATED on a single-source claim) → support gate exit 1,
    # no upstream 2 → records aggregates to 1
    fb = _stage(tmp_path)
    txt = (fb / "baseline" / "claims.yaml").read_text().replace("support_status: SUPPORTED", "support_status: CORROBORATED")
    (fb / "baseline" / "claims.yaml").write_text(txt)
    code, _ = verify.records_check(tmp_path, ASOF)
    assert code == 1


def test_corrupt_claims_file_is_not_mislabeled_empty(tmp_path):
    # review should-fix: a present-but-unparseable claims file fails closed as cannot-parse, NOT
    # mislabeled "empty factbase"
    fb = _stage(tmp_path)
    (fb / "baseline" / "claims.yaml").write_text("schema_version: \"2.0\"\nclaims: [unbalanced\n")
    code, lines = verify.records_check(tmp_path, ASOF)
    joined = "\n".join(lines).lower()
    assert code == 2 and "cannot parse" in joined and "empty factbase" not in joined


def test_missing_as_of_on_nonempty_fails_closed(tmp_path):
    # a non-empty compose with no clock → the freshness gate fails closed → records 2
    _stage(tmp_path)
    assert verify.records_check(tmp_path, None)[0] == 2


def test_cli_records_on_staged_root(tmp_path):
    _stage(tmp_path)
    assert verify.main(["--mode", "records", "--root", str(tmp_path), "--as-of", ASOF]) == 0

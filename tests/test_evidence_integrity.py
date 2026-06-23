"""WP2.3a — evidence-artifact integrity gate (validate_evidence.py). Cross-record + cross-file
source resolution on top of the WP1.4 schema. Tests assert the SPECIFIC finding. Failing-first.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_evidence as ve  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
SRC = FIX / "evd_integrity_sources.yaml"


def _run(name):
    sids, gids = ve.load_source_ids(SRC)
    return ve.validate_evidence_file(FIX / name, sids, gids)


def test_valid_passes():
    assert ve.main([str(FIX / "evd_integrity_valid.yaml"), "--sources", str(SRC)]) == 0


def test_duplicate_id_invalid():
    code, findings = _run("evd_dup_id.yaml")
    assert code == 1 and any("duplicate id 'evd-x'" in f for f in findings), findings


def test_duplicate_content_hash_invalid():
    code, findings = _run("evd_dup_content_hash.yaml")
    assert code == 1 and any("duplicate content_hash" in f for f in findings), findings


def test_source_unresolved_invalid():
    code, findings = _run("evd_source_unresolved.yaml")
    assert code == 1 and any("does not resolve to a known source" in f for f in findings), findings


def test_retrieved_before_published_invalid():
    code, findings = _run("evd_retrieved_before_published.yaml")
    assert code == 1 and any("precedes published_at" in f for f in findings), findings


def test_group_as_source_defensive_unit():
    # R-EVD-3 is unreachable via the file path (the schema's ref:src- type rejects a grp- value),
    # so probe the defensive branch directly: a grp- source_id with grp_ids set -> group finding
    findings = ve.check_evidence(
        [{"id": "evd-a", "source_id": "grp-wires", "content_hash": None}],
        src_ids={"src-reuters"}, grp_ids={"grp-wires"})
    assert any("is a non-citable group" in f for f in findings), findings


def test_group_as_source_rejected_at_schema_layer():
    # the reachable path: a grp- in source_id fails at the WP1.4 schema (ref:src- prefix), exit 1,
    # WITHOUT the integrity gate double-reporting
    code, findings = _run("evd_source_is_group.yaml")
    assert code == 1
    assert any("must reference an id with prefix 'src-'" in f for f in findings), findings


def test_empty_factbase_evidence_passes():
    assert ve.main([str(ROOT / "factbase" / "evidence.yaml")]) == 0


def test_skeleton_evidence_passes():
    assert ve.main([str(FIX / "skeleton" / "skeleton_evidence.yaml"),
                    "--sources", str(FIX / "skeleton" / "skeleton_sources.yaml")]) == 0


def test_unparseable_fails_closed():
    assert ve.main([str(FIX / "envelope_unknown_version.yaml"), "--sources", str(SRC)]) == 2


def test_missing_source_registry_fails_closed():
    assert ve.main([str(FIX / "evd_integrity_valid.yaml"), "--sources", str(FIX / "does_not_exist.yaml")]) == 2


def test_schema_break_returns_schema_code_not_masked():
    code, findings = _run("evd_bad_hash.yaml")  # WP1.4 bad-content-hash fixture
    assert code == 1

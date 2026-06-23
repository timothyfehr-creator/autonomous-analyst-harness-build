"""WP1.4 — evidence artifact + claim-evidence assessment schemas + primary_evidence_kind
(V-P1-4 shape). Shape + cross-field rules only; cross-record resolution is Phase 2. Failing-first.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_schema as vs  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def test_complete_artifact_plus_unreviewed_relationship_valid():
    assert vs.main([str(FIX / "evd_cea_valid.yaml")]) == 0


def test_empty_evidence_and_claim_evidence_logs_valid():
    assert vs.main([str(ROOT / "factbase" / "evidence.yaml")]) == 0
    assert vs.main([str(ROOT / "factbase" / "claim_evidence.yaml")]) == 0


def test_signed_url_without_snapshot_invalid():
    assert vs.main([str(FIX / "evd_signed_no_snapshot.yaml")]) == 1


def test_artifact_source_is_group_invalid():
    # source_id must be a src- entity, not a grp- group
    assert vs.main([str(FIX / "evd_source_is_group.yaml")]) == 1


def test_assessment_empty_locator_or_summary_invalid():
    assert vs.main([str(FIX / "cea_empty_summary.yaml")]) == 1


def test_one_artifact_supports_A_refutes_B_valid():
    # the same artifact may SUPPORT one claim and REFUTE another (different assessments)
    assert vs.main([str(FIX / "cea_two_stances.yaml")]) == 0


def test_reviewed_relationship_missing_binding_hash_invalid():
    assert vs.main([str(FIX / "cea_reviewed_missing_hash.yaml")]) == 1


def test_unknown_field_invalid():
    assert vs.main([str(FIX / "evd_unknown_field.yaml")]) == 1


def test_bad_content_hash_invalid():
    assert vs.main([str(FIX / "evd_bad_hash.yaml")]) == 1


def test_primary_evidence_kind_enum_enforced():
    assert vs.main([str(FIX / "cea_bad_primary_kind.yaml")]) == 1


def test_evidence_and_cea_registered():
    assert "evidence" in vs.SCHEMAS and "claim_evidence_assessments" in vs.SCHEMAS


def test_bool_does_not_satisfy_int_enum():
    # information_credibility: true must NOT pass as credibility 1 (Python True==1 quirk)
    assert vs.main([str(FIX / "cea_credibility_bool.yaml")]) == 1

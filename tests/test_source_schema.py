"""WP1.2 — source entity / non-citable group / append-only assessment schemas (shape only).

The real seed `factbase/sources.yaml` (29 entities + 2 non-citable groups) and the empty
assessment log must validate clean; adversarial variants must fail. Cross-record integrity
(supersession chains, member resolution) is WP2.1/2.2, not here. Written failing-first.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_schema as vs  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def test_real_sources_yaml_valid():
    # the shipped 29 entities + 2 groups (two collections in one file) must pass
    assert vs.main([str(ROOT / "factbase" / "sources.yaml")]) == 0


def test_empty_assessment_log_valid():
    assert vs.main([str(ROOT / "factbase" / "source_assessments.yaml")]) == 0


def test_valid_assessment_shape_clean():
    assert vs.main([str(FIX / "sas_valid.yaml")]) == 0  # near-miss control for the two below


def test_citable_group_invalid():
    assert vs.main([str(FIX / "src_citable_group.yaml")]) == 1


def test_group_id_where_source_required_invalid():
    # a grp- id in an assessment's source_id (a source entity is required) must fail
    assert vs.main([str(FIX / "src_group_as_source_id.yaml")]) == 1


def test_per_record_schema_version_invalid():
    assert vs.main([str(FIX / "src_per_record_version.yaml")]) == 1


def test_missing_required_source_field_invalid():
    assert vs.main([str(FIX / "src_missing_field.yaml")]) == 1


def test_bad_source_type_enum_invalid():
    assert vs.main([str(FIX / "src_bad_type.yaml")]) == 1


def test_free_text_reliability_note_on_source_rejected():
    # a reliability note field on a source entity is a prohibited (unknown) field
    assert vs.main([str(FIX / "src_reliability_note.yaml")]) == 1


def test_schema_defs_registered():
    # the source/group/assessment collections are registered with the validator
    for name in ("sources", "groups", "source_assessments"):
        assert name in vs.SCHEMAS, name

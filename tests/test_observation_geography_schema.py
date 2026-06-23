"""WP1.6a — structured observation + geography schemas + the owner-editable unit_vocabulary.

Observation carries the V-P1-5 SCHEMA half: a numeric obs binds source_value/source_unit + a
vocabulary unit and must DECLARE a transformation for any unit/denominator recast. The transform's
correctness + the dimensional-class check (the A5 kill) are WP2.8 integrity, not here. Failing-first.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_schema as vs  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


# ---- unit vocabulary (config registry, self-validating) ----
def test_unit_vocabulary_config_self_validates():
    assert vs.main([str(ROOT / "config" / "unit_vocabulary.yaml")]) == 0


def test_unit_vocabulary_loaded_nonempty():
    import schema_defs
    assert "bpd" in schema_defs.UNIT_VOCABULARY and schema_defs.UNIT_VOCABULARY["bpd"] == "FLOW_VOLUME_RATE"


def test_unit_vocabulary_bad_dimensional_class_invalid():
    assert vs.main([str(FIX / "unit_vocab_bad_class.yaml")]) == 1


# ---- observations ----
def test_numeric_observation_valid():
    assert vs.main([str(FIX / "obs_numeric_valid.yaml")]) == 0


def test_category_observation_valid():
    assert vs.main([str(FIX / "obs_category_valid.yaml")]) == 0


def test_category_unit_must_be_null_invalid():
    # a non-numeric (CATEGORY) observation may not carry a unit
    assert vs.main([str(FIX / "obs_category_unit_set.yaml")]) == 1


def test_empty_observation_registry_valid():
    assert vs.main([str(ROOT / "factbase" / "observations.yaml")]) == 0


def test_unit_not_in_vocabulary_invalid():
    assert vs.main([str(FIX / "obs_unit_not_in_vocab.yaml")]) == 1


def test_numeric_missing_source_value_invalid():
    assert vs.main([str(FIX / "obs_numeric_missing_source_value.yaml")]) == 1


def test_unit_recast_without_transformation_invalid():
    assert vs.main([str(FIX / "obs_unit_recast_no_transformation.yaml")]) == 1


def test_share_without_derived_from_invalid():
    # bare absolute recast as a share (denominator present, no transformation/derived_from) fails
    assert vs.main([str(FIX / "obs_share_no_derived_from.yaml")]) == 1


def test_observation_empty_assessment_ids_invalid():
    assert vs.main([str(FIX / "obs_empty_cea.yaml")]) == 1


def test_observation_bad_locator_hash_invalid():
    assert vs.main([str(FIX / "obs_bad_locator_hash.yaml")]) == 1


def test_observation_unknown_field_invalid():
    assert vs.main([str(FIX / "obs_unknown_field.yaml")]) == 1


# ---- geography ----
def test_geography_valid():
    assert vs.main([str(FIX / "geo_valid.yaml")]) == 0


def test_empty_geography_registry_valid():
    assert vs.main([str(ROOT / "factbase" / "geography.yaml")]) == 0


def test_geography_non_epsg_crs_invalid():
    assert vs.main([str(FIX / "geo_crs_bad.yaml")]) == 1


def test_geography_bad_geometry_type_invalid():
    assert vs.main([str(FIX / "geo_bad_geometry_type.yaml")]) == 1


def test_geography_empty_assessment_ids_invalid():
    assert vs.main([str(FIX / "geo_empty_cea.yaml")]) == 1


def test_observation_and_geography_registered():
    assert {"observations", "geography", "unit_vocabulary"} <= set(vs.SCHEMAS)

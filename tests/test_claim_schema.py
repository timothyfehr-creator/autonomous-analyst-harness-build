"""WP1.3 — type-specific claim schemas (FACT/INFERENCE/ASSUMPTION/PROJECTION) + multi-axis
status + the high_impact field (V-P0-1 schema half). Shape only; cross-file support resolution
is Phase 2. Written failing-first.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_schema as vs  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def test_valid_mixed_type_claims_clean():
    assert vs.main([str(FIX / "claims_valid_mixed.yaml")]) == 0


def test_empty_baseline_and_live_claims_valid():
    assert vs.main([str(ROOT / "factbase" / "baseline" / "claims.yaml")]) == 0
    assert vs.main([str(ROOT / "factbase" / "live" / "claims.yaml")]) == 0


def test_inference_without_premises_invalid():
    assert vs.main([str(FIX / "clm_inference_no_premises.yaml")]) == 1


def test_assumption_with_support_invalid():
    # ASSUMPTION must be UNVERIFIED
    assert vs.main([str(FIX / "clm_assumption_supported.yaml")]) == 1


def test_falsifiable_projection_without_prediction_invalid():
    assert vs.main([str(FIX / "clm_projection_no_prediction.yaml")]) == 1


def test_durable_fact_without_review_by_invalid():
    assert vs.main([str(FIX / "clm_durable_no_review_by.yaml")]) == 1


def test_volatile_fact_without_expiry_invalid():
    assert vs.main([str(FIX / "clm_volatile_no_expiry.yaml")]) == 1


def test_bad_support_status_enum_invalid():
    assert vs.main([str(FIX / "clm_bad_support_status.yaml")]) == 1


def test_high_impact_not_boolean_invalid():
    assert vs.main([str(FIX / "clm_high_impact_not_bool.yaml")]) == 1


def test_unknown_field_invalid():
    assert vs.main([str(FIX / "clm_unknown_field.yaml")]) == 1


def test_claims_schema_registered():
    assert "claims" in vs.SCHEMAS

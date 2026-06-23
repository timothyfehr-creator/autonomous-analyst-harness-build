"""WP1.6b — analysis manifest + refuter + visual schemas (the answer/output layer, §9–§11).

Shape only: hash-bound ref entries, claim markers, verdict records, visual_type input rules.
The cross-record RESOLUTION (refuter set-equality coverage vs the manifest, marker↔answer-text
agreement, hash matching against live records) is Phase-3 integrity, not here. Failing-first.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_schema as vs  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


# ---- analysis manifest ----
def test_analysis_valid():
    assert vs.main([str(FIX / "ana_valid.yaml")]) == 0


def test_analysis_bad_lifecycle_invalid():
    assert vs.main([str(FIX / "ana_bad_lifecycle.yaml")]) == 1


def test_analysis_marker_bad_hash_invalid():
    assert vs.main([str(FIX / "ana_marker_bad_hash.yaml")]) == 1


def test_analysis_ref_wrong_prefix_invalid():
    # an artifact_refs entry must be an evd- id, not a clm- id
    assert vs.main([str(FIX / "ana_bad_ref_prefix.yaml")]) == 1


# ---- refuter ----
def test_refuter_valid():
    assert vs.main([str(FIX / "ref_valid.yaml")]) == 0


def test_refuter_bad_verdict_invalid():
    assert vs.main([str(FIX / "ref_bad_verdict.yaml")]) == 1


def test_refuter_bad_check_value_invalid():
    assert vs.main([str(FIX / "ref_bad_check.yaml")]) == 1


def test_refuter_empty_verdicts_invalid():
    assert vs.main([str(FIX / "ref_empty_verdicts.yaml")]) == 1


def test_refuter_bad_reviewer_class_invalid():
    assert vs.main([str(FIX / "ref_bad_reviewer_class.yaml")]) == 1


# ---- visual ----
def test_visual_valid():
    assert vs.main([str(FIX / "vis_valid.yaml")]) == 0


def test_visual_bad_type_invalid():
    assert vs.main([str(FIX / "vis_bad_visual_type.yaml")]) == 1


def test_chart_without_observations_invalid():
    assert vs.main([str(FIX / "vis_chart_no_observations.yaml")]) == 1


def test_map_without_geography_invalid():
    assert vs.main([str(FIX / "vis_map_no_geography.yaml")]) == 1


def test_answer_layer_registered():
    assert {"analyses", "refuters", "visuals"} <= set(vs.SCHEMAS)

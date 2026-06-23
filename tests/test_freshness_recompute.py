"""WP2.7 — freshness gate (validate_freshness.py). Recomputes freshness_status vs an injectable
--as-of clock and rejects bidirectionally (over-fresh CURRENT-that's-stale AND false-STALE). Tests
pin --as-of 2026-06-23T00:00:00Z (never wall-clock). Failing-first; assert the SPECIFIC finding.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_freshness as vf  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
ASOF = "2026-06-23T00:00:00Z"


def _run(name):
    return vf.validate_freshness([FIX / name], ASOF)


def test_stale_presented_as_current_invalid():
    code, f = _run("fresh_stale_as_current.yaml")
    assert code == 1 and any("recomputes STALE" in x for x in f), f


def test_review_due_presented_as_current_invalid():
    code, f = _run("fresh_review_due_as_current.yaml")
    assert code == 1 and any("recomputes REVIEW_DUE" in x for x in f), f


def test_false_stale_invalid():
    # bidirectional: a still-current claim mislabeled STALE is rejected (suppression vector)
    code, f = _run("fresh_false_stale.yaml")
    assert code == 1 and any("stored STALE but recomputes CURRENT" in x for x in f), f


def test_freshness_on_non_fact_invalid():
    code, f = _run("fresh_current_on_inference.yaml")
    assert code == 1 and any("recomputes NOT_APPLICABLE" in x for x in f), f


def test_review_due_correctly_labeled_valid():
    code, _ = _run("fresh_review_due_valid.yaml")
    assert code == 0


def test_future_current_valid():
    code, _ = _run("fresh_future_current_valid.yaml")
    assert code == 0


def test_volatile_future_current_valid():
    code, _ = _run("fresh_volatile_current_valid.yaml")
    assert code == 0


def test_non_fact_not_applicable_valid():
    code, _ = _run("fresh_napp_inference_valid.yaml")
    assert code == 0


# ---- fail-closed ----
def test_profile_only_volatile_fails_closed():
    # VOLATILE with a named freshness_profile and no expires_at — no registry → exit 2
    assert vf.main([str(FIX / "fresh_profile_only.yaml"), "--as-of", ASOF]) == 2


def test_missing_as_of_fails_closed():
    assert vf.main([str(FIX / "fresh_review_due_valid.yaml")]) == 2


def test_unparseable_as_of_fails_closed():
    assert vf.main([str(FIX / "fresh_review_due_valid.yaml"), "--as-of", "not-a-date"]) == 2


def test_empty_factbase_passes():
    assert vf.main(["--as-of", ASOF]) == 0


def test_skeleton_passes_at_pin():
    assert vf.main([str(FIX / "skeleton" / "skeleton_claims.yaml"), "--as-of", ASOF]) == 0


def test_unparseable_file_fails_closed():
    assert vf.main([str(FIX / "envelope_unknown_version.yaml"), "--as-of", ASOF]) == 2


def test_inactive_lifecycle_excluded():
    # a SUPERSEDED claim is not a live freshness target → not recomputed (no finding even if mislabeled)
    claim = {"id": "clm-s", "epistemic_type": "FACT", "stability": "DURABLE", "lifecycle": "SUPERSEDED",
             "review_by": "2026-03-01T00:00:00Z", "freshness_status": "CURRENT"}
    code, f = vf.check_freshness([claim], vf.schema_defs.iso_instant(ASOF))
    assert code == 0 and not f


def test_review_by_at_asof_is_review_due_inclusive():
    # boundary: as_of EXACTLY == review_by → REVIEW_DUE (inclusive); kills a >=→> mutant
    code, f = _run("fresh_review_by_at_asof.yaml")
    assert code == 1 and any("recomputes REVIEW_DUE" in x for x in f), f


def test_expires_at_at_asof_is_stale_inclusive():
    code, f = _run("fresh_expires_at_at_asof.yaml")
    assert code == 1 and any("recomputes STALE" in x for x in f), f


def test_durable_missing_review_by_fails_closed():
    # the DURABLE-nodate fail-close branch (defensive; pinned so a return-CURRENT mutant dies)
    claim = {"id": "clm-d", "epistemic_type": "FACT", "stability": "DURABLE",
             "lifecycle": "REVIEWED", "review_by": None, "freshness_status": "CURRENT"}
    code, _ = vf.check_freshness([claim], vf.schema_defs.iso_instant(ASOF))
    assert code == 2


def test_compute_freshness_units():
    asof = vf.schema_defs.iso_instant(ASOF)
    assert vf.compute_freshness({"epistemic_type": "INFERENCE"}, asof)[0] == "NOT_APPLICABLE"
    assert vf.compute_freshness({"epistemic_type": "FACT", "stability": "DURABLE",
                                 "review_by": "2026-03-01T00:00:00Z"}, asof)[0] == "REVIEW_DUE"
    assert vf.compute_freshness({"epistemic_type": "FACT", "stability": "VOLATILE",
                                 "expires_at": "2027-01-01T00:00:00Z"}, asof)[0] == "CURRENT"
    assert vf.compute_freshness({"epistemic_type": "FACT", "stability": "APPEND_ONLY_HISTORY"}, asof)[0] == "CURRENT"

"""WP2.4 — type-specific claim integrity gate (validate_claims.py). Cross-record/cross-file rules:
premise + prediction resolution, projection-not-fact, active-cea-on-ASSUMPTION (owns the WP2.3b
deferral), claim supersession. ASSUMED rules (premise acyclicity, date ordering) are DEFERRED for
ratification and intentionally NOT tested. Failing-first; tests assert the SPECIFIC finding.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_claims as vc  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
PRED = FIX / "clm_predictions.yaml"


def _run(*claim_files, cea=None):
    return vc.validate_claims([FIX / f for f in claim_files], cea or (ROOT / "factbase" / "claim_evidence.yaml"), PRED)


def test_cross_file_duplicate_id_invalid():
    code, f = _run("clm_dup_base.yaml", "clm_dup_live.yaml")
    assert code == 1 and any("duplicate id 'clm-x'" in x for x in f), f


def test_premise_unresolved_invalid():
    code, f = _run("clm_premise_unresolved.yaml")
    assert code == 1 and any("premise 'clm-ghost' does not resolve" in x for x in f), f


def test_premise_resolved_passes():
    code, _ = _run("clm_premise_resolved.yaml")
    assert code == 0


def test_falsifiable_prediction_unresolved_invalid():
    code, f = _run("clm_prediction_unresolved.yaml")
    assert code == 1 and any("prediction_id 'prd-ghost' does not resolve" in x for x in f), f


def test_projection_corroborated_invalid():
    code, f = _run("clm_projection_corroborated.yaml")
    assert code == 1 and any("may not carry fact-grade" in x for x in f), f


def test_claim_self_supersede_invalid():
    code, f = _run("clm_self_supersede.yaml")
    assert code == 1 and any("cannot supersede itself" in x for x in f), f


def test_active_cea_on_assumption_invalid():
    # R-CLM-5 — owns the WP2.3b deferral; active (un-superseded, non-REJECTED) cea on an ASSUMPTION
    code, f = _run("clm_with_assumption.yaml", cea=FIX / "cea_active_on_assumption.yaml")
    assert code == 1 and any("active on ASSUMPTION" in x for x in f), f


def test_rejected_cea_on_assumption_passes():
    # near-miss: a REJECTED (inactive) cea on an assumption is permitted history
    code, _ = _run("clm_with_assumption.yaml", cea=FIX / "cea_rejected_on_assumption.yaml")
    assert code == 0


def test_canonical_mixed_passes_with_prediction_registry():
    # claims_valid_mixed has clm-prj-1 -> prd-example-reopen; resolves against the companion registry
    code, _ = _run("claims_valid_mixed.yaml")
    assert code == 0


def test_empty_factbase_passes():
    assert vc.main([]) == 0


def test_skeleton_claims_pass():
    sk = FIX / "skeleton"
    assert vc.main([str(sk / "skeleton_claims.yaml"),
                    "--claim-evidence", str(sk / "skeleton_claim_evidence.yaml"),
                    "--predictions", str(sk / "skeleton_predictions.yaml")]) == 0


def test_unparseable_fails_closed():
    assert vc.main([str(FIX / "envelope_unknown_version.yaml"), "--predictions", str(PRED)]) == 2


def test_missing_prediction_registry_fails_closed():
    assert vc.main([str(FIX / "clm_premise_resolved.yaml"), "--predictions", str(FIX / "nope.yaml")]) == 2


def test_schema_break_returns_schema_code_not_masked():
    code, _ = _run("clm_high_impact_not_bool.yaml")
    assert code == 1

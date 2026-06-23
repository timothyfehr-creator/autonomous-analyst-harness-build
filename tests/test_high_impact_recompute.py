"""WP2.2a — high_impact gate-recompute (V-P0-1, the P0 fix). The gate recomputes high_impact from
the computable triggers (T1 topics, T2-pred prediction) and RAISES a stored false that should be
true. Stored true is always accepted (true→false is deferred, not failed). Empty trigger config →
exit 2 (§13). Tests assert the SPECIFIC finding so a backstopping path can't mask a rule's removal.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_high_impact as vhi  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def _run(name):
    return vhi.validate_high_impact_file(FIX / name, vhi.trigger_set())


# ---- the proving tests (false → true is raised) ----
def test_v_p0_1_proving_test_raises_authored_false():
    code, findings, _ = _run("hi_t1_casualties_false.yaml")
    assert code == 1
    assert any("but computed true" in f and "T1" in f for f in findings), findings


def test_t1_alias_control_raises():
    # the adjudication-row spelling 'control' (alias of §10's 'territorial-control') must trigger
    code, findings, _ = _run("hi_t1_alias_control.yaml")
    assert code == 1
    assert any("'control'" in f for f in findings), findings


def test_t2_prediction_leg_raises():
    code, findings, _ = _run("hi_t2_prediction_false.yaml")
    assert code == 1
    assert any("feeds a prediction" in f for f in findings), findings


# ---- the non-violations (gate is not trigger-happy; true is accepted) ----
def test_valid_clean_passes():
    code, _, _ = _run("hi_valid_clean.yaml")
    assert code == 0


def test_near_miss_substring_passes():
    # 'casualty-methodology' / 'territorial' are substrings, not exact tokens/aliases → not a trigger
    code, _, _ = _run("hi_near_miss_substring.yaml")
    assert code == 0


def test_true_deferred_not_failed():
    # stored true with no computable trigger passes, but emits a [deferred] notice (never silent)
    code, findings, notices = _run("hi_true_deferred_ok.yaml")
    assert code == 0 and not findings
    assert any("deferred, not scored" in n for n in notices), notices


def test_null_high_impact_on_trigger_is_rejected():
    # M1 regression: a casualties claim authored high_impact: null must NOT slip past (schema layer
    # now forbids null on the required V-P0-1 boolean). Previously bypassed both gate and schema.
    assert vhi.main([str(FIX / "hi_null_casualties.yaml")]) == 1


def test_null_high_impact_unit_is_a_mismatch():
    # M1 regression at the gate layer: stored null with computed true IS a mismatch (`is not True`)
    claim = {"id": "clm-n", "topics": ["casualties"], "high_impact": None}
    findings, _ = vhi.check_claims({"claims": [claim]}, vhi.trigger_set())
    assert findings and "computed true" in findings[0]


def test_canonical_mixed_fixture_passes_after_clm_prj_1_flip():
    # clm-prj-1 (FALSIFIABLE + prediction_id) was flipped false→true; the recompute now agrees
    assert vhi.main([str(FIX / "claims_valid_mixed.yaml")]) == 0


# ---- fail-closed + layering ----
def test_empty_trigger_config_exits_2(tmp_path):
    cfg = tmp_path / "empty.yaml"
    cfg.write_text('schema_version: "2.0"\nhigh_impact_triggers: []\n')
    assert vhi.main([str(FIX / "hi_valid_clean.yaml"), "--triggers", str(cfg)]) == 2


def test_empty_factbase_claims_exit_0():
    assert vhi.main([str(ROOT / "factbase" / "baseline" / "claims.yaml"),
                     str(ROOT / "factbase" / "live" / "claims.yaml")]) == 0


def test_skeleton_claims_pass():
    assert vhi.main([str(FIX / "skeleton" / "skeleton_claims.yaml")]) == 0


def test_schema_break_returns_schema_code_not_masked():
    # a shape-broken claim fails at the schema layer (1); recompute does not run / does not mask it
    code, _, _ = _run("clm_high_impact_not_bool.yaml")
    assert code == 1


def test_config_self_validates():
    import validate_schema as vs
    assert vs.main([str(ROOT / "config" / "high_impact_triggers.yaml")]) == 0


def test_normalize_topic():
    assert vhi.normalize_topic("  Casualties ") == "casualties"
    assert vhi.normalize_topic("Territorial-Control") == "territorial-control"


def test_compute_each_leg_isolated():
    trig = vhi.trigger_set()
    assert vhi.compute_high_impact({"topics": ["casualties"]}, trig)[0] is True
    assert vhi.compute_high_impact({"epistemic_type": "PROJECTION", "projection_kind": "FALSIFIABLE",
                                    "prediction_id": "prd-x", "topics": []}, trig)[0] is True
    assert vhi.compute_high_impact({"topics": ["transport"]}, trig)[0] is False

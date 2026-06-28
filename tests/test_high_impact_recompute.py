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


def test_t1_synonym_losses_raises():
    # Milestone-A review: a casualties claim tagged with the synonym 'losses' was escaping the
    # exact-token match; the widened trigger set (2026-06-24) now catches it.
    code, findings, _ = _run("hi_synonym_losses.yaml")
    assert code == 1
    assert any("'losses'" in f for f in findings), findings


def test_t1b_text_leg_catches_topic_laundering():
    # cross-vendor review P0-2: a casualties claim tagged with an innocuous topic ([transport]) but
    # whose TEXT says 'killed 500 civilians' must still compute high-impact (the topics field is not
    # the only evasion surface). Word-boundary, err-high.
    code, findings, _ = _run("hi_text_evasion.yaml")
    assert code == 1
    assert any("T1b" in f and "killed" in f for f in findings), findings


def test_text_leg_is_word_boundary_not_substring():
    import validate_high_impact as vhi
    trig = vhi.trigger_set()
    assert vhi.text_trigger_hits("the air-defence control room", trig) == ["control"]  # whole word
    assert vhi.text_trigger_hits("a controlled demolition", trig) == []  # 'controlled' ≠ 'control'
    assert vhi.text_trigger_hits("redistribution of grain", trig) == []  # not 'attribution'
    assert vhi.text_trigger_hits("500 killed and many wounded", trig) == ["killed", "wounded"]


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


# ---- FR-2 (R2-P0-2): reviewer-assigned impact_category + widened candidate detector ----
def test_impact_category_none_contradicts_trigger():
    # the candidate detector trips on the TEXT ('died', a widened token) but the reviewer stamped
    # impact_category: NONE — a contradiction the records gate must flag (laundering / miscategory).
    code, findings, _ = _run("hi_candidate_uncategorized.yaml")
    assert code == 1
    assert any("impact_category" in f and "NONE" in f for f in findings), findings


def test_impact_category_forces_high_impact():
    # a reviewer-assigned category (CASUALTIES) is an authoritative high-impact signal: it forces
    # high_impact true even with no trigger word (the durable fix, not word-list dependent).
    code, findings, _ = _run("hi_category_forces_high_impact.yaml")
    assert code == 1
    assert any("T0" in f and "impact_category" in f for f in findings), findings


def test_impact_category_consistent_passes():
    code, findings, _ = _run("hi_category_consistent_valid.yaml")
    assert code == 0, findings


def test_widened_trigger_catches_died_and_seized():
    # R2-P0-2 immediate exploit: 'died' / 'seized' were not tokens; the widened candidate detector
    # now catches them (word-boundary, NFC+casefold).
    trig = vhi.trigger_set()
    assert "died" in vhi.text_trigger_hits("five hundred civilians died today", trig)
    assert "seized" in vhi.text_trigger_hits("russian forces seized the town", trig)
    assert vhi.text_trigger_hits("a studied retreat", trig) == []  # 'studied' ≠ 'died' (word-boundary)


def test_category_leg_isolated():
    trig = vhi.trigger_set()
    assert vhi.compute_high_impact({"topics": ["transport"], "impact_category": "CASUALTIES"}, trig)[0] is True
    assert vhi.compute_high_impact({"topics": ["transport"], "impact_category": "NONE"}, trig)[0] is False


def test_schema_rejects_bad_impact_category(tmp_path):
    import validate_schema as vs
    p = tmp_path / "bad_cat.yaml"
    p.write_text((FIX / "hi_category_consistent_valid.yaml").read_text().replace(
        "impact_category: CASUALTIES", "impact_category: BOGUS"))
    code, findings = vs.validate_file(p)
    assert code == 1 and any("impact_category" in f and "enum" in f for f in findings), findings

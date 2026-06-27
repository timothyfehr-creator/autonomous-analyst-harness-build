"""WP3.3 — validate_refuter: exact binding + set-equality coverage + independence floor +
high_impact contest (V-P0-1 refuter half) + check applicability + the A7 exemption-review cost.
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_high_impact as v_hi  # noqa: E402
import validate_refuter as vr  # noqa: E402
import validate_schema as vs  # noqa: E402

SK = ROOT / "tests" / "fixtures" / "skeleton"
TRIG = v_hi.trigger_set()
HM, OH = "sha256:" + "a" * 64, "sha256:" + "b" * 64

_NORMAL = {"id": "clm-n", "text": "t", "epistemic_type": "FACT", "topics": ["transport"],
           "high_impact": False, "support_status": "SUPPORTED", "dispute_status": "UNCONTESTED",
           "freshness_status": "CURRENT", "lifecycle": "REVIEWED", "stability": "DURABLE"}
_HI = {**_NORMAL, "id": "clm-hi", "topics": ["casualties"]}  # gate computes high_impact TRUE


def _live(claims=(_NORMAL,), observations=()):
    return types.SimpleNamespace(claims={c["id"]: c for c in claims},
                                 observations={o["id"]: o for o in observations})


def _verdict(cid, **kw):
    v = {"claim_id": cid, "verdict": "SURVIVES", "displacement_check": "PASS",
         "independence_check": "PASS", "freshness_check": "PASS", "observation_check": "PASS",
         "reasoning_check": "NOT_APPLICABLE"}
    v.update(kw)
    return v


def _ana(claim_ids, cea_ids, obs_refs=(), exemptions=()):
    return {"manifest_hash": HM, "output_hash": OH,
            "claim_markers": {f"c{i}": {"claim_id": c, "claim_hash": "x"} for i, c in enumerate(claim_ids)},
            "claim_evidence_assessment_refs": [{"id": x, "record_hash": "x"} for x in cea_ids],
            "observation_refs": [{"id": o, "record_hash": "x"} for o in obs_refs],
            "narrative_exemptions": list(exemptions)}


def _ref(claim_ids, cea_ids, reviewer_class="HUMAN", verdicts=None, exemptions_reviewed=(),
         manifest_hash=HM, output_hash=OH):
    return {"manifest_hash": manifest_hash, "output_hash": output_hash, "reviewer_class": reviewer_class,
            "reviewed_claim_ids": list(claim_ids), "reviewed_assessment_ids": list(cea_ids),
            "verdicts": verdicts if verdicts is not None else [_verdict(c) for c in claim_ids],
            "exemptions_reviewed": list(exemptions_reviewed)}


def test_normal_answer_passes():
    ana = _ana(["clm-n"], ["cea-1"])
    ref = _ref(["clm-n"], ["cea-1"])
    assert vr.validate_refuter(ref, ana, _live(), TRIG) == (0, [])


def test_wrong_manifest_hash_fails():
    ana = _ana(["clm-n"], ["cea-1"])
    ref = _ref(["clm-n"], ["cea-1"], manifest_hash="sha256:" + "c" * 64)
    code, f = vr.validate_refuter(ref, ana, _live(), TRIG)
    assert code == 1 and any("manifest_hash does not bind" in x for x in f)


def test_coverage_missing_claim_fails():
    ana = _ana(["clm-n", "clm-x"], ["cea-1"])
    ref = _ref(["clm-n"], ["cea-1"], verdicts=[_verdict("clm-n")])  # drops clm-x
    code, f = vr.validate_refuter(ref, ana, _live(), TRIG)
    assert code == 1 and any("reviewed_claim_ids != manifest claim set" in x for x in f)


def test_coverage_extra_claim_fails():
    ana = _ana(["clm-n"], ["cea-1"])
    ref = _ref(["clm-n", "clm-extra"], ["cea-1"], verdicts=[_verdict("clm-n")])
    code, f = vr.validate_refuter(ref, ana, _live(), TRIG)
    assert code == 1 and any("extra ['clm-extra']" in x for x in f)


def test_coverage_assessment_mismatch_fails():
    ana = _ana(["clm-n"], ["cea-1", "cea-2"])
    ref = _ref(["clm-n"], ["cea-1"])
    code, f = vr.validate_refuter(ref, ana, _live(), TRIG)
    assert code == 1 and any("reviewed_assessment_ids != manifest assessment set" in x for x in f)


def test_same_model_on_committed_answer_fails():
    ana = _ana(["clm-n"], ["cea-1"])
    ref = _ref(["clm-n"], ["cea-1"], reviewer_class="SAME_MODEL_FRESH_CONTEXT")
    code, f = vr.validate_refuter(ref, ana, _live(), TRIG)
    assert code == 1 and any("SAME_MODEL_FRESH_CONTEXT is not independent" in x for x in f)


def test_high_impact_false_uncontested_fails():
    # the V-P0-1 kill: gate computes high_impact true (topics=casualties), stored false, the refuter
    # does not contest (no verdict high_impact flag) → fail
    ana = _ana(["clm-hi"], ["cea-1"])
    ref = _ref(["clm-hi"], ["cea-1"], reviewer_class="DIFFERENT_MODEL", verdicts=[_verdict("clm-hi")])
    code, f = vr.validate_refuter(ref, ana, _live([_HI]), TRIG)
    assert code == 1 and any("MUST contest" in x and "V-P0-1" in x for x in f)


def test_high_impact_contested_passes():
    ana = _ana(["clm-hi"], ["cea-1"])
    ref = _ref(["clm-hi"], ["cea-1"], reviewer_class="DIFFERENT_MODEL",
               verdicts=[_verdict("clm-hi", high_impact=True, independence_check="PASS")])
    assert vr.validate_refuter(ref, ana, _live([_HI]), TRIG) == (0, [])


def test_inference_reasoning_check_na_fails():
    inf = {**_NORMAL, "id": "clm-inf", "epistemic_type": "INFERENCE"}
    ana = _ana(["clm-inf"], ["cea-1"])
    ref = _ref(["clm-inf"], ["cea-1"], verdicts=[_verdict("clm-inf", reasoning_check="NOT_APPLICABLE")])
    code, f = vr.validate_refuter(ref, ana, _live([inf]), TRIG)
    assert code == 1 and any("reasoning_check != NOT_APPLICABLE" in x for x in f)


def test_observation_check_na_when_obs_cited_fails():
    obs = {"id": "obs-1", "claim_id": "clm-n"}
    ana = _ana(["clm-n"], ["cea-1"], obs_refs=["obs-1"])
    ref = _ref(["clm-n"], ["cea-1"], verdicts=[_verdict("clm-n", observation_check="NOT_APPLICABLE")])
    code, f = vr.validate_refuter(ref, ana, _live([_NORMAL], [obs]), TRIG)
    assert code == 1 and any("observation_check may not be NOT_APPLICABLE" in x for x in f)


def test_stale_freshness_check_na_fails():
    stale = {**_NORMAL, "id": "clm-s", "freshness_status": "STALE"}
    ana = _ana(["clm-s"], ["cea-1"])
    ref = _ref(["clm-s"], ["cea-1"], verdicts=[_verdict("clm-s", freshness_check="NOT_APPLICABLE")])
    code, f = vr.validate_refuter(ref, ana, _live([stale]), TRIG)
    assert code == 1 and any("freshness_check != NOT_APPLICABLE" in x for x in f)


def test_exemptions_must_be_reviewed():
    ex = "sha256:" + "e" * 64
    ana = _ana(["clm-n"], ["cea-1"], exemptions=[ex])
    ref_unreviewed = _ref(["clm-n"], ["cea-1"])  # exemptions_reviewed empty
    code, f = vr.validate_refuter(ref_unreviewed, ana, _live(), TRIG)
    assert code == 1 and any("exemptions_reviewed != analysis narrative_exemptions" in x for x in f)
    ref_ok = _ref(["clm-n"], ["cea-1"], exemptions_reviewed=[ex])
    assert vr.validate_refuter(ref_ok, ana, _live(), TRIG) == (0, [])


def test_required_claim_without_verdict_fails():
    # set-equality coverage is satisfied by list membership, but a covered claim with NO verdict is
    # not actually adjudicated → fail (coverage must mean adjudication)
    n2 = {**_NORMAL, "id": "clm-n2"}
    ana = _ana(["clm-n", "clm-n2"], ["cea-1"])
    ref = _ref(["clm-n", "clm-n2"], ["cea-1"], verdicts=[_verdict("clm-n")])  # no verdict for clm-n2
    code, f = vr.validate_refuter(ref, ana, _live([_NORMAL, n2]), TRIG)
    assert code == 1 and any("clm-n2" in x and "no verdict entry" in x for x in f), f


def test_survives_verdict_cannot_carry_failed_check():
    ana = _ana(["clm-n"], ["cea-1"])
    bad = _ref(["clm-n"], ["cea-1"], verdicts=[_verdict("clm-n", verdict="SURVIVES", displacement_check="FAIL")])
    code, f = vr.validate_refuter(bad, ana, _live(), TRIG)
    assert code == 1 and any("SURVIVES but" in x and "FAILed" in x for x in f), f
    # an honest negative (a FAILed check with a REJECT verdict) is a valid STORED refuter record
    # (records/standalone mode); it is not flagged as malformed
    ok = _ref(["clm-n"], ["cea-1"], verdicts=[_verdict("clm-n", verdict="REJECT", displacement_check="FAIL")])
    assert vr.validate_refuter(ok, ana, _live(), TRIG) == (0, [])


def test_answer_mode_requires_survives_verdict():
    # cross-vendor review P0-1: a REJECT/REVISE/DOWNGRADE verdict must BLOCK a committed answer,
    # even though the same refuter record is structurally valid for storage.
    ana = _ana(["clm-n"], ["cea-1"])
    for bad_verdict in ("REJECT", "REVISE", "DOWNGRADE"):
        ref = _ref(["clm-n"], ["cea-1"], verdicts=[_verdict("clm-n", verdict=bad_verdict)])
        # structurally valid (records mode)
        assert vr.validate_refuter(ref, ana, _live(), TRIG) == (0, [])
        # but blocks the committed answer (answer mode)
        code, f = vr.validate_refuter(ref, ana, _live(), TRIG, answer_mode=True)
        assert code == 1 and any("requires every claim to SURVIVE" in x for x in f), (bad_verdict, f)
    # a SURVIVES verdict still passes in answer mode
    good = _ref(["clm-n"], ["cea-1"], verdicts=[_verdict("clm-n", verdict="SURVIVES")])
    assert vr.validate_refuter(good, ana, _live(), TRIG, answer_mode=True) == (0, [])


def test_required_refuter_class_enforced():
    # Milestone-A P0 review: the manifest's declared required_refuter_class was decorative. A
    # DIFFERENT_MODEL refuter satisfies HUMAN_OR_DIFFERENT_MODEL; SAME_MODEL does not.
    ana = {**_ana(["clm-n"], ["cea-1"]), "required_refuter_class": "HUMAN_OR_DIFFERENT_MODEL"}
    ref = _ref(["clm-n"], ["cea-1"], reviewer_class="SAME_MODEL_FRESH_CONTEXT")
    code, f = vr.validate_refuter(ref, ana, _live(), TRIG)
    assert code == 1 and any("does not satisfy the manifest's required_refuter_class" in x for x in f)
    assert vr.validate_refuter(_ref(["clm-n"], ["cea-1"], reviewer_class="DIFFERENT_MODEL"),
                               ana, _live(), TRIG) == (0, [])


def test_skeleton_refuter_passes_integration():
    claim = vs.load_yaml_strict(SK / "skeleton_claims.yaml")["claims"][0]
    obs = vs.load_yaml_strict(SK / "skeleton_observations.yaml")["observations"][0]
    ana = vs.load_yaml_strict(SK / "skeleton_analysis.yaml")["analyses"][0]
    ref = vs.load_yaml_strict(SK / "skeleton_refuter.yaml")["refuters"][0]
    code, f = vr.validate_refuter(ref, ana, _live([claim], [obs]), TRIG)
    assert code == 0, f

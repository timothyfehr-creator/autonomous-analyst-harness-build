"""WP2.8 — observation integrity (validate_observations.py). The dimensional half of V-P1-5: a
cross-dimensional-class numeric recast must trace to a resolving derived_from (kills A5), and every
derived_from must resolve. SHAPE is WP1.6 (not re-done). Failing-first; assert the SPECIFIC finding.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import schema_defs  # noqa: E402
import validate_observations as vo  # noqa: E402
import validate_schema as vs  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def _run(name):
    return vo.validate_observations([FIX / name])


def test_a5_cross_class_recast_without_derived_from_fails():
    # the A5 kill (genuinely new beyond WP1.6): cross-class recast, transformation declared, no df
    code, f = _run("obs_a5_cross_class_no_df.yaml")
    assert code == 1 and any("cross-dimensional-class recast" in x and "A5" in x for x in f), f


def test_a5_cross_class_is_wp16_schema_clean():
    # prove WP2.8 is the catcher: the A5 fixture passes the WP1.6 schema (su!=un has a transformation,
    # denominator null) — only the dimensional gate rejects it
    assert vs.main([str(FIX / "obs_a5_cross_class_no_df.yaml")]) == 0


def test_a5_absolute_to_dimensionless_share_fails():
    code, f = _run("obs_a5_share_dimensionless_no_df.yaml")
    assert code == 1 and any("DIMENSIONLESS" in x and "A5" in x for x in f), f


def test_cross_class_with_resolving_derived_from_passes():
    code, _ = _run("obs_cross_class_with_df.yaml")
    assert code == 0


def test_same_class_numerator_conversion_passes():
    # bpd -> m3/day (both FLOW_VOLUME_RATE): a scalar numerator conversion needs no derived_from
    code, _ = _run("obs_same_class_recast.yaml")
    assert code == 0


def test_derived_from_unresolved_fails():
    code, f = _run("obs_derived_from_unresolved.yaml")
    assert code == 1 and any("does not resolve to a known observation" in x for x in f), f


def test_observation_unresolved_claim_or_cea_fails():
    # R3-P1-2: an observation's evidence leg must EXIST when the registries are supplied — a
    # nonexistent claim_id or claim_evidence_assessment_id is a finding (records composition).
    obs = [{"id": "obs-x", "claim_id": "clm-nope", "claim_evidence_assessment_ids": ["cea-nope"]}]
    f = vo.check_observations(obs, {"obs-x"}, claim_ids={"clm-real"}, cea_ids={"cea-real"})
    assert any("clm-nope" in x and "does not resolve" in x for x in f), f
    assert any("cea-nope" in x and "does not resolve" in x for x in f), f
    # standalone gate (registries absent) skips the resolution — no false positive
    assert not vo.check_observations(obs, {"obs-x"})


def test_empty_factbase_passes():
    assert vo.main([]) == 0


def test_skeleton_category_obs_passes():
    # the skeleton observation is CATEGORY → skipped by the numeric dimensional check
    assert vo.main([str(FIX / "skeleton" / "skeleton_observations.yaml")]) == 0


def test_unparseable_fails_closed():
    assert vo.main([str(FIX / "envelope_unknown_version.yaml")]) == 2


def test_empty_vocab_fails_closed(monkeypatch):
    monkeypatch.setattr(schema_defs, "UNIT_VOCABULARY", {})
    assert vo.main([str(FIX / "obs_same_class_recast.yaml")]) == 2


def test_existing_same_class_recast_is_wp16_shape_not_wp28():
    # boundary: the existing same-class recast-without-transformation fixture still fails at WP1.6
    # (schema), NOT via the WP2.8 dimensional check — WP2.8 did not steal the shape rule
    assert vs.main([str(FIX / "obs_unit_recast_no_transformation.yaml")]) == 1


def test_self_referential_derived_from_cannot_self_certify():
    # review should-fix: a cross-class recast whose derived_from points at its own id traces to no
    # supplying record — must fail (the A5 self-certification escape)
    code, f = _run("obs_a5_self_derived.yaml")
    assert code == 1 and any("derived_from cycle" in x for x in f), f


def test_derivation_cycle_caught_unit():
    # a transitive 2-cycle (a→b→a) also self-certifies → flagged
    obs = [{"id": "obs-a", "value_type": "NUMBER", "derived_from": ["obs-b"]},
           {"id": "obs-b", "value_type": "NUMBER", "derived_from": ["obs-a"]}]
    assert vo._derivation_cycles(obs)


def test_in_file_duplicate_id_caught():
    # the sole intra-file dup-id catcher (validate_schema only rejects dup KEYS, not dup id VALUES)
    code, f = _run("obs_dup_id.yaml")
    assert code == 1 and any("duplicate id 'obs-dup'" in x for x in f), f


def test_cross_file_duplicate_id_caught():
    code, f = vo.validate_observations([FIX / "obs_same_class_recast.yaml", FIX / "obs_same_class_recast.yaml"])
    assert code == 1 and any("duplicate id" in x for x in f), f


def test_check_units():
    vocab = schema_defs.UNIT_VOCABULARY
    # cross-class no df → finding; same-class → none; resolving df → none
    cross = [{"id": "o", "value_type": "NUMBER", "source_unit": "tonnes/day", "unit": "tonnes", "derived_from": []}]
    assert vo.check_observations(cross, {"o"})
    same = [{"id": "o", "value_type": "NUMBER", "source_unit": "bpd", "unit": "m3/day", "derived_from": []}]
    assert not vo.check_observations(same, {"o"})
    withdf = [{"id": "o", "value_type": "NUMBER", "source_unit": "tonnes/day", "unit": "tonnes", "derived_from": ["o2"]}]
    assert not vo.check_observations(withdf, {"o", "o2"})

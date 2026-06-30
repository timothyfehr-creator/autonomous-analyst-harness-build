"""WP2.5 — support + corroboration recompute gate (validate_support.py). Recomputes support_status
from active CHECKED SUPPORTS assessments and rejects an over-claim. Ships V-P1-4 (authoritative-
primary), V-P1-10 (credibility floor), F3 (Tier-1 cap); kills A1 (first-party + one wire) and
two-credibility-6. Failing-first; tests assert the SPECIFIC finding.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_support as vsup  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def _run(claims, cea):
    return vsup.validate_support([FIX / claims], FIX / cea)


# ---- the exploit kills + over-claim rejections ----
def test_a1_first_party_plus_wire_not_corroborated():
    code, f = _run("support_a1_claims.yaml", "support_a1_cea.yaml")
    assert code == 1 and any("independent origin" in x for x in f), f


def test_wire_echo_shared_deeper_origin_not_corroborated():
    # Milestone-A review: two outlets with DISTINCT origin_chain[0] but a SHARED deeper source are
    # one origin — independence is by connected component over the full chain, not origin_chain[0].
    code, f = _run("support_wire_echo_claims.yaml", "support_wire_echo_cea.yaml")
    assert code == 1 and any("independent origin" in x for x in f), f


def test_shared_independence_group_not_corroborated():
    # two assessments declaring the SAME independence_group collapse to one origin (§3/§6.1)
    code, f = _run("support_shared_group_claims.yaml", "support_shared_group_cea.yaml")
    assert code == 1 and any("independent origin" in x for x in f), f


def test_independence_components_helper():
    def a(sources, group):
        return {"origin_chain": [{"source_id": s} for s in sources], "independence_group": group}
    # distinct sources + distinct groups → 2 independent origins
    assert vsup.independence_components([a(["src-a"], "g1"), a(["src-b"], "g2")]) == 2
    # shared deeper source → 1
    assert vsup.independence_components([a(["out-a", "wire"], "g1"), a(["out-b", "wire"], "g2")]) == 1
    # shared independence_group → 1
    assert vsup.independence_components([a(["src-a"], "g"), a(["src-b"], "g")]) == 1
    # an unanchored (no source) assessment is not an origin → counts 0
    assert vsup.independence_components([a([], "g1")]) == 0
    assert vsup.independence_components([a(["src-a"], "g1"), a([], None)]) == 1


def test_two_credibility6_not_corroborated():
    code, f = _run("support_twocred6_claims.yaml", "support_twocred6_cea.yaml")
    assert code == 1 and any("credibility <= 3" in x for x in f), f


def test_single_source_not_corroborated():
    code, f = _run("support_single_source_claims.yaml", "support_single_source_cea.yaml")
    assert code == 1 and any("independent origin" in x for x in f), f


def test_unassessed_credibility_fails_floor():
    # V-P1-10 / F3: UNASSESSED credibility cannot clear the <=3 floor → not CORROBORATED
    code, f = _run("support_unassessed_claims.yaml", "support_unassessed_cea.yaml")
    assert code == 1 and any("credibility <= 3" in x for x in f), f


def test_corroborated_without_evidence_invalid():
    code, f = vsup.validate_support([FIX / "support_corroborated_no_cea_claims.yaml"],
                                    ROOT / "factbase" / "claim_evidence.yaml")
    assert code == 1 and any("no active CHECKED SUPPORTS" in x for x in f), f


def test_unchecked_assessment_does_not_earn_supported():
    code, f = _run("support_unchecked_claims.yaml", "support_unchecked_cea.yaml")
    assert code == 1 and any("no active CHECKED SUPPORTS" in x for x in f), f


# ---- valids + the reject-direction lock ----
def test_corroborated_valid_passes():
    code, _ = _run("support_corroborated_valid_claims.yaml", "support_corroborated_valid_cea.yaml")
    assert code == 0


def test_supported_valid_passes():
    code, _ = _run("support_supported_valid_claims.yaml", "support_supported_valid_cea.yaml")
    assert code == 0


def test_underclaim_passes_overclaim_only():
    # stored SUPPORTED while the records earn CORROBORATED → under-label, accepted (over-claim only)
    code, _ = _run("support_underclaim_claims.yaml", "support_underclaim_cea.yaml")
    assert code == 0


# ---- dogfood + fail-closed ----
def test_empty_factbase_passes():
    assert vsup.main([]) == 0


def test_skeleton_supported_passes():
    sk = FIX / "skeleton"
    assert vsup.main([str(sk / "skeleton_claims.yaml"),
                      "--claim-evidence", str(sk / "skeleton_claim_evidence.yaml")]) == 0


def test_unparseable_fails_closed():
    assert vsup.main([str(FIX / "envelope_unknown_version.yaml")]) == 2


def test_missing_cea_registry_fails_closed():
    assert vsup.main([str(FIX / "support_supported_valid_claims.yaml"),
                      "--claim-evidence", str(FIX / "nope.yaml")]) == 2


def test_schema_break_returns_schema_code_not_masked():
    code, _ = _run("clm_high_impact_not_bool.yaml", "support_a1_cea.yaml")
    assert code == 1


# ---- unit tests (the corroboration logic + R4 standing invariant) ----
def test_compute_support_conjunction():
    def cea(origin, kind="OFFICIAL_PRIMARY_DOCUMENT", cred=2):
        return {"primary_evidence_kind": kind, "information_credibility": cred,
                "origin_chain": [{"source_id": origin}]}
    # two independent origins + authoritative + cred<=3 → CORROBORATED
    assert vsup.compute_support([cea("src-a"), cea("src-b", kind=None, cred=3)])[0] == "CORROBORATED"
    # same underlying origin → collapses to 1 → SUPPORTED
    assert vsup.compute_support([cea("src-a"), cea("src-a", kind=None)])[0] == "SUPPORTED"
    # no authoritative-primary anywhere → SUPPORTED
    assert vsup.compute_support([cea("src-a", kind=None), cea("src-b", kind=None)])[0] == "SUPPORTED"
    # empty → UNVERIFIED
    assert vsup.compute_support([])[0] == "UNVERIFIED"


# ---- WP-D: §6.1c declared scope-matched corroboration leg (C2b via corroboration_rating_id) ----
# sas registry: src-a's active leaf is B (sas-a, superseding an older D), src-b D, src-belligerent B.
_SAS = [{"id": "sas-a-old", "source_id": "src-a", "reliability": "D", "supersedes": None},
        {"id": "sas-a", "source_id": "src-a", "reliability": "B", "supersedes": "sas-a-old"},  # active leaf
        {"id": "sas-b", "source_id": "src-b", "reliability": "D", "supersedes": None},
        {"id": "sas-bel", "source_id": "src-belligerent", "reliability": "B", "supersedes": None}]
_BYID = vsup.active_sas_by_id(_SAS)


def _cea(origin, cred=2, link=None, kind=None):
    c = {"primary_evidence_kind": kind, "information_credibility": cred,
         "origin_chain": [{"source_id": origin}]}
    if link:
        c["corroboration_rating_id"] = link
    return c


def test_ac_leg_corroborates_only_with_a_named_scope_rating():
    quals = [_cea("src-a", link="sas-a"), _cea("src-b", cred=3)]
    # 2 independent origins + floor, but the leg is OFF (no resolver) → SUPPORTED
    assert vsup.compute_support(quals)[0] == "SUPPORTED"
    # with the resolver, cea-a names sas-a (active, B, owned by src-a) → C2 satisfied → CORROBORATED
    assert vsup.compute_support(quals, _BYID)[0] == "CORROBORATED"
    # the SAME two origins WITHOUT a named link no longer corroborate (this is the WP-D tightening)
    assert vsup.compute_support([_cea("src-a"), _cea("src-b", cred=3)], _BYID)[0] == "SUPPORTED"


def test_ac_link_must_be_ac_owned_and_active():
    # named a D-rated rating → not A-C → SUPPORTED
    assert vsup.compute_support([_cea("src-b", link="sas-b"), _cea("src-a", cred=3)], _BYID)[0] == "SUPPORTED"
    # named a rating owned by a DIFFERENT source (sas-b is src-b's) on an src-a chain → SUPPORTED
    assert vsup.compute_support([_cea("src-a", link="sas-b"), _cea("src-b", cred=3)], _BYID)[0] == "SUPPORTED"
    # named a SUPERSEDED rating id (sas-a-old) → not an active leaf → SUPPORTED
    assert vsup.compute_support([_cea("src-a", link="sas-a-old"), _cea("src-b", cred=3)], _BYID)[0] == "SUPPORTED"


def test_ac_leg_does_not_relax_two_origin_requirement():
    # a single linked origin is still ONE origin → C1 unmet → SUPPORTED
    assert vsup.compute_support([_cea("src-a", link="sas-a")], _BYID)[0] == "SUPPORTED"


def test_ac_leg_first_party_source_cannot_backdoor():
    # a first-party belligerent chain naming an A-C rating is C3-excluded → still 1 counting origin → SUPPORTED
    fp = _cea("src-belligerent", cred=1, link="sas-bel", kind="FIRST_PARTY_ACTION_RECORD")
    indep = _cea("src-independent", cred=2)
    assert vsup.compute_support([fp, indep], _BYID)[0] == "SUPPORTED"


def test_active_sas_resolver_takes_leaf_and_drops_superseded():
    rel = vsup.active_reliabilities_by_source(_SAS)
    assert rel["src-a"] == {"B"}  # the superseded D leaf is dropped
    byid = vsup.active_sas_by_id(_SAS)
    assert "sas-a-old" not in byid and byid["sas-a"]["reliability"] == "B"  # only active leaves resolve


def test_first_party_excluded_from_independence():
    fp = {"primary_evidence_kind": "FIRST_PARTY_ACTION_RECORD", "information_credibility": 1,
          "origin_chain": [{"source_id": "src-bel"}]}
    wire = {"primary_evidence_kind": None, "information_credibility": 2,
            "origin_chain": [{"source_id": "src-bel"}]}  # republishes the belligerent
    # first-party excluded from the C1 tally; the wire collapses to the same origin → 1 < 2
    assert vsup.compute_support([fp, wire])[0] == "SUPPORTED"


def test_a1_first_party_with_DISTINCT_origin_cannot_be_second_origin():
    # MUST-FIX regression (the A1 kill C3 had no distinguishing test): a belligerent's FIRST_PARTY
    # record at one origin + a single genuinely-independent source at ANOTHER origin must NOT reach
    # CORROBORATED — the first-party record is excluded from the independence tally, so this is 1
    # counting origin, not 2. (With C3 disabled this returns CORROBORATED — the mutant this kills.)
    fp = {"primary_evidence_kind": "FIRST_PARTY_ACTION_RECORD", "information_credibility": 1,
          "origin_chain": [{"source_id": "src-belligerent"}]}
    indep = {"primary_evidence_kind": None, "information_credibility": 2,
             "origin_chain": [{"source_id": "src-independent"}]}
    assert vsup.compute_support([fp, indep])[0] == "SUPPORTED"


def test_floor_rejects_out_of_domain_credibility():
    # should-fix: credibility 0 / negatives are out of the {1..6} domain and must NOT clear the floor
    def cea(origin, cred):
        return {"primary_evidence_kind": "OFFICIAL_PRIMARY_DOCUMENT", "information_credibility": cred,
                "origin_chain": [{"source_id": origin}]}
    assert vsup.compute_support([cea("src-a", 0), cea("src-b", 5)])[0] == "SUPPORTED"
    assert vsup.compute_support([cea("src-a", 2), cea("src-b", 5)])[0] == "CORROBORATED"  # in-domain still works


def test_null_id_assessment_does_not_crash():
    # should-fix: a malformed cea with id:null (and no supersedes) must not raise — fail-closed shape
    ceas = [{"id": None, "claim_id": "clm-x", "artifact_id": "evd-x", "stance": "SUPPORTS",
             "semantic_review": {"status": "CHECKED"}},
            {"id": "cea-ok", "claim_id": "clm-x", "artifact_id": "evd-x", "stance": "SUPPORTS",
             "semantic_review": {"status": "CHECKED"}, "supersedes": None}]
    vsup.active_supports_by_claim(ceas)  # must not raise KeyError


def test_r4_standing_invariant_unassessed_cannot_corroborate():
    # a chain lacking a numeric credibility <=3 cannot contribute to CORROBORATED (Tier-1 cap)
    def cea(origin, cred):
        return {"primary_evidence_kind": "OFFICIAL_PRIMARY_DOCUMENT", "information_credibility": cred,
                "origin_chain": [{"source_id": origin}]}
    assert vsup.compute_support([cea("src-a", "UNASSESSED"), cea("src-b", "UNASSESSED")])[0] == "SUPPORTED"

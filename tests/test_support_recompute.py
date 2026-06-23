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

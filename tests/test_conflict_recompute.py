"""WP2.6 — conflict / stance gate (validate_conflict.py). Recomputes the CONTESTED axis of
dispute_status from active CHECKED assessments and rejects bidirectionally (unearned CONTESTED AND
a stored UNCONTESTED hiding an independent credible conflict). Independence by origin_chain[0].
Failing-first; tests assert the SPECIFIC finding.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_conflict as vcon  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def _run(claims, cea):
    return vcon.validate_conflict([FIX / claims], FIX / cea)


def test_same_origin_both_sides_not_contested():
    # the A-exploit: one underlying origin on both sides cannot manufacture a contest
    code, f = _run("conflict_same_origin_both_sides_claims.yaml", "conflict_same_origin_both_sides_cea.yaml")
    assert code == 1 and any("unearned" in x for x in f), f


def test_legit_contested_passes():
    code, _ = _run("conflict_legit_contested_claims.yaml", "conflict_legit_contested_cea.yaml")
    assert code == 0


def test_uncontested_hiding_conflict_invalid():
    # the WP2.6 departure from WP2.5: an under-labeled UNCONTESTED that hides a real conflict fails
    code, f = _run("conflict_uncontested_hides_refutes_claims.yaml", "conflict_uncontested_hides_refutes_cea.yaml")
    assert code == 1 and any("hidden conflict" in x for x in f), f


def test_unchecked_refutes_does_not_contest():
    code, _ = _run("conflict_unchecked_refutes_claims.yaml", "conflict_unchecked_refutes_cea.yaml")
    assert code == 0


def test_context_only_is_not_a_contest_side():
    code, _ = _run("conflict_context_only_claims.yaml", "conflict_context_only_cea.yaml")
    assert code == 0


def test_mixed_counts_as_structural_opposer():
    code, _ = _run("conflict_mixed_contested_claims.yaml", "conflict_mixed_contested_cea.yaml")
    assert code == 0


def test_empty_factbase_passes():
    assert vcon.main([]) == 0


def test_skeleton_passes():
    sk = FIX / "skeleton"
    assert vcon.main([str(sk / "skeleton_claims.yaml"),
                      "--claim-evidence", str(sk / "skeleton_claim_evidence.yaml")]) == 0


def test_unparseable_fails_closed():
    assert vcon.main([str(FIX / "envelope_unknown_version.yaml")]) == 2


def test_missing_cea_registry_fails_closed():
    assert vcon.main([str(FIX / "conflict_legit_contested_claims.yaml"),
                      "--claim-evidence", str(FIX / "nope.yaml")]) == 2


def test_schema_break_returns_schema_code_not_masked():
    code, _ = _run("clm_high_impact_not_bool.yaml", "conflict_legit_contested_cea.yaml")
    assert code == 1


# ---- unit tests on the pure conflict logic ----
def test_compute_dispute():
    def a(stance, origin, cred=2):
        return {"stance": stance, "information_credibility": cred, "origin_chain": [{"source_id": origin}]}
    # distinct origins, opposing → CONTESTED
    assert vcon.compute_dispute([a("SUPPORTS", "src-a"), a("REFUTES", "src-b")]) == "CONTESTED"
    # same origin both sides → not CONTESTED (duplicate republication / self-contradiction)
    assert vcon.compute_dispute([a("SUPPORTS", "src-x"), a("REFUTES", "src-x")]) == "UNCONTESTED"
    # one-sided → UNCONTESTED
    assert vcon.compute_dispute([a("SUPPORTS", "src-a")]) == "UNCONTESTED"
    # empty → UNKNOWN
    assert vcon.compute_dispute([]) == "UNKNOWN"
    # an UNASSESSED-credibility refuter is not 'credible' → no contest
    assert vcon.compute_dispute([a("SUPPORTS", "src-a"), a("REFUTES", "src-b", cred="UNASSESSED")]) == "UNCONTESTED"
    # review should-fix: a null-origin opposer must not manufacture a contest (the -{None} strips,
    # reachable today — the schema doesn't type origin-link source_ids as non-null)
    assert vcon.compute_dispute([a("SUPPORTS", "src-a"), a("REFUTES", None)]) == "UNCONTESTED"
    assert vcon.compute_dispute([a("SUPPORTS", None), a("REFUTES", "src-b")]) == "UNCONTESTED"
    # review watch: out-of-domain (>6) and bool credibility are not 'credible' (the gate reads cea raw)
    assert vcon.compute_dispute([a("SUPPORTS", "src-a"), a("REFUTES", "src-b", cred=7)]) == "UNCONTESTED"
    assert vcon.compute_dispute([a("SUPPORTS", "src-a"), a("REFUTES", "src-b", cred=True)]) == "UNCONTESTED"


def test_projection_and_assumption_claims_skipped():
    # review watch: the FACT/INFERENCE epistemic_type guard — a PROJECTION/ASSUMPTION is skipped
    # even when the cea holds a real independent conflict (support axis / type bans are other WPs)
    conflict_ceas = [
        {"id": "s", "claim_id": "clm-p", "artifact_id": "e1", "stance": "SUPPORTS",
         "information_credibility": 2, "origin_chain": [{"source_id": "src-a"}], "semantic_review": {"status": "CHECKED"}},
        {"id": "r", "claim_id": "clm-p", "artifact_id": "e2", "stance": "REFUTES",
         "information_credibility": 2, "origin_chain": [{"source_id": "src-b"}], "semantic_review": {"status": "CHECKED"}, "supersedes": None}]
    proj = {"id": "clm-p", "epistemic_type": "PROJECTION", "dispute_status": "UNCONTESTED"}
    assert vcon.check_conflict([proj], conflict_ceas) == []

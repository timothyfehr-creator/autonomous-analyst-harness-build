"""WP2.3b — claim-evidence governance gate (validate_claim_evidence.py). Cross-record/cross-file
resolution + partitioned supersession + the CHECKED artifact_hash binding. Failing-first; tests
assert the SPECIFIC finding. R-CEA-6 (cea-on-assumption) is deferred to WP2.4 and NOT tested here.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_claim_evidence as vce  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
CLAIMS = [FIX / "cea_ce_claims.yaml"]
EVID = FIX / "cea_ce_evidence.yaml"
SRC = FIX / "cea_ce_sources.yaml"
ARGS = ["--claims", str(CLAIMS[0]), "--evidence", str(EVID), "--sources", str(SRC)]


def _run(name):
    refs = vce.load_ref_sets(CLAIMS, EVID, SRC)
    return vce.validate_claim_evidence_file(FIX / name, refs)


def _main(name):
    return vce.main([str(FIX / name), *ARGS])


def test_valid_passes():
    assert _main("cea_ce_valid.yaml") == 0


def test_stale_claim_content_hash_review_fails():
    # cross-vendor review P0-3: a CHECKED review whose claim_content_hash no longer binds the claim
    # (the claim was edited without re-review) must fail — a stale review cannot earn support.
    code, f = _run("cea_stale_cch_cea.yaml")
    assert code == 1 and any("does not bind" in x and "current content" in x for x in f), f


def test_two_pairs_near_miss_passes():
    # same artifact, DIFFERENT claims = two partitions, each one active leaf -> clean
    assert _main("cea_ce_two_pairs_valid.yaml") == 0


def test_claim_unresolved_invalid():
    code, f = _run("cea_claim_unresolved.yaml")
    assert code == 1 and any("claim_id 'clm-ghost' does not resolve" in x for x in f), f


def test_artifact_unresolved_invalid():
    code, f = _run("cea_artifact_unresolved.yaml")
    assert code == 1 and any("artifact_id 'evd-ghost' does not resolve" in x for x in f), f


def test_origin_source_is_group_invalid():
    # the REACHABLE §1 group-as-source case (origin source_id is not schema-typed)
    code, f = _run("cea_origin_source_is_group.yaml")
    assert code == 1 and any("is a non-citable group" in x for x in f), f


def test_origin_source_unresolved_invalid():
    code, f = _run("cea_origin_source_unresolved.yaml")
    assert code == 1 and any("origin_chain[0] source_id 'src-ghost' does not resolve" in x for x in f), f


def test_two_active_leaves_same_pair_invalid():
    code, f = _run("cea_ce_two_leaves.yaml")
    assert code == 1 and any("active leaves" in x for x in f), f


def test_supersede_cross_pair_invalid():
    code, f = _run("cea_supersede_cross_pair.yaml")
    assert code == 1 and any("across different chains" in x for x in f), f


def test_stale_artifact_hash_invalid():
    code, f = _run("cea_stale_artifact_hash.yaml")
    assert code == 1 and any("artifact_hash does not match" in x for x in f), f


def test_duplicate_cea_id_invalid():
    code, f = _run("cea_dup_id.yaml")
    assert code == 1 and any("duplicate id 'cea-x'" in x for x in f), f


def test_origin_artifact_unresolved_invalid():
    code, f = _run("cea_origin_artifact_unresolved.yaml")
    assert code == 1 and any("origin_chain[0] artifact_id 'evd-ghost' does not resolve" in x for x in f), f


def test_baseline_live_claims_union_resolves():
    # clm-b lives ONLY in the second claims file; the union of the two claim files must resolve it
    assert vce.main([str(FIX / "cea_uses_clm_b.yaml"),
                     "--claims", str(FIX / "cea_ce_claims_a_only.yaml"), str(FIX / "cea_ce_claims_b_only.yaml"),
                     "--evidence", str(EVID), "--sources", str(SRC)]) == 0


def test_claims_union_is_load_bearing():
    # with only the a-only claims file, clm-b is unresolved -> proves the union matters (not a no-op)
    assert vce.main([str(FIX / "cea_uses_clm_b.yaml"), "--claims", str(FIX / "cea_ce_claims_a_only.yaml"),
                     "--evidence", str(EVID), "--sources", str(SRC)]) == 1


def test_skeleton_claim_evidence_passes():
    sk = FIX / "skeleton"
    assert vce.main([str(sk / "skeleton_claim_evidence.yaml"),
                     "--claims", str(sk / "skeleton_claims.yaml"),
                     "--evidence", str(sk / "skeleton_evidence.yaml"),
                     "--sources", str(sk / "skeleton_sources.yaml")]) == 0


def test_empty_factbase_claim_evidence_passes():
    assert vce.main([str(ROOT / "factbase" / "claim_evidence.yaml")]) == 0


def test_unparseable_fails_closed():
    assert _main("envelope_unknown_version.yaml") == 2


def test_missing_registry_fails_closed():
    assert vce.main([str(FIX / "cea_ce_valid.yaml"), "--claims", str(FIX / "nope.yaml"),
                     "--evidence", str(EVID), "--sources", str(SRC)]) == 2


def test_schema_break_returns_schema_code_not_masked():
    # CHECKED missing a binding hash fails at the WP1.4 schema (exit 1), governance not masking it
    code, f = _run("cea_reviewed_missing_hash.yaml")
    assert code == 1


# ---- FR-4 (R2-P0-4): origin_chain must be BOUND to the reviewed artifact ----
ORIG_CLAIMS = [FIX / "cea_origin_claims.yaml"]
ORIG_EVID = FIX / "cea_origin_evidence.yaml"
ORIG_SRC = FIX / "cea_origin_sources.yaml"


def _run_origin(name):
    refs = vce.load_ref_sets(ORIG_CLAIMS, ORIG_EVID, ORIG_SRC)
    return vce.validate_claim_evidence_file(FIX / name, refs)


def test_origin_chain_reviewed_artifact_must_be_bound():
    # B1: the reviewed artifact must appear in its OWN origin_chain bound to its real source; a fake
    # independent origin (no binding link) cannot manufacture a second independent origin (R2-P0-4).
    code, f = _run_origin("cea_origin_not_bound_cea.yaml")
    assert code == 1 and any("not bound into its own origin_chain" in x for x in f), f


def test_origin_chain_link_source_must_own_artifact():
    # B2: a link that names an artifact must attribute it to the artifact's REAL source.
    code, f = _run_origin("cea_origin_not_bound_cea.yaml")
    assert code == 1 and any("belongs to source" in x for x in f), f


def test_origin_chain_bound_ok_passes():
    # the near-miss: both reviewed artifacts correctly bound → governance clean (independence
    # collapse of these same-outlet assessments is validate_support's job, not this gate's).
    code, f = _run_origin("cea_origin_bound_ok_cea.yaml")
    assert code == 0, f

"""WP2.2b — source-assessment append-only governance (validate_assessment_governance.py). Structural
supersession-chain integrity + non-empty provenance. Tests assert the SPECIFIC finding (tamper-
evident: a backstopping rule must not mask the removal of the named one). Failing-first.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_assessment_governance as gov  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def _run(name):
    return gov.validate_governance_file(FIX / name)


def test_self_supersede_raised():
    code, findings = _run("sas_self_supersede.yaml")
    assert code == 1
    assert any("cannot supersede itself" in f for f in findings), findings


def test_orphan_supersedes_raised():
    code, findings = _run("sas_orphan_supersedes.yaml")
    assert code == 1
    assert any("does not resolve to a known assessment" in f for f in findings), findings


def test_cycle_raised():
    code, findings = _run("sas_cycle.yaml")
    assert code == 1
    assert any("cycle" in f for f in findings), findings


def test_two_leaves_one_chain_raised():
    code, findings = _run("sas_two_leaves_one_chain.yaml")
    assert code == 1
    assert any("active leaves" in f for f in findings), findings


def test_empty_provenance_raised():
    code, findings = _run("sas_empty_provenance.yaml")
    assert code == 1
    assert any("empty rationale" in f for f in findings), findings


def test_sas_valid_passes():
    # single-node chain (near-miss control)
    assert gov.main([str(FIX / "sas_valid.yaml")]) == 0


def test_valid_linear_chain_passes():
    # a 3-node linear chain has exactly one active leaf
    assert gov.main([str(FIX / "sas_valid_chain.yaml")]) == 0


def test_real_factbase_assessments_pass():
    assert gov.main([str(ROOT / "factbase" / "source_assessments.yaml")]) == 0


def test_skeleton_assessments_pass():
    assert gov.main([str(FIX / "skeleton" / "skeleton_source_assessments.yaml")]) == 0


def test_unparseable_fails_closed():
    assert gov.main([str(FIX / "envelope_unknown_version.yaml")]) == 2


def test_schema_break_returns_schema_code_not_masked():
    # a shape-broken assessment fails at the schema layer (1); governance not run / not masking
    code, findings = _run("sas_schema_bad.yaml")
    assert code == 1
    assert any("unknown field 'bogus_field'" in f for f in findings), findings

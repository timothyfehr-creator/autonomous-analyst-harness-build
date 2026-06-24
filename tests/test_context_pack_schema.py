"""WP3.0 — CONTEXT_PACK_SCHEMA (ctx-) closed-schema shape. Failing-fixture-first: a malformed
pack must be rejected (exit 1) with a specific message; the skeleton pack is the near-miss (0).
Cross-record resolution (ref hashes match LIVE records) is Phase 3 (validate_context_pack, WP3.1).
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_schema as vs  # noqa: E402

FIX = ROOT / "tests" / "fixtures"
SK = ROOT / "tests" / "fixtures" / "skeleton"


def _run(path):
    return vs.validate_file(path)


def test_skeleton_pack_is_schema_clean():  # near-miss control
    code, findings = _run(SK / "skeleton_context_pack.yaml")
    assert code == 0, findings


def test_bad_ref_hash_rejected():
    code, findings = _run(FIX / "ctx_bad_ref_hash.yaml")
    assert code == 1 and any("claim_refs[0].record_hash" in f for f in findings), findings


def test_unknown_field_rejected():
    code, findings = _run(FIX / "ctx_unknown_field.yaml")
    assert code == 1 and any("editorial_note" in f for f in findings), findings


def test_omitted_reason_must_be_in_closed_enum():
    code, findings = _run(FIX / "ctx_omitted_no_reason.yaml")
    assert code == 1 and any("omitted_candidates[0].reason" in f for f in findings), findings


def test_token_budget_must_be_integer(tmp_path):
    p = tmp_path / "ctx_float_budget.yaml"
    p.write_text((SK / "skeleton_context_pack.yaml").read_text().replace(
        "token_budget: 4000", "token_budget: 4000.5"))
    code, findings = _run(p)
    assert code == 1 and any("token_budget" in f and "integer" in f for f in findings), findings

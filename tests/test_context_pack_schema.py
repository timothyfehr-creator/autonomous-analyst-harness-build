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


# ---- WP4.3 / honest-use audit 1c: omitted_candidates anti-laundering (validate_context_pack) ----
import types  # noqa: E402

import validate_context_pack as v_ctx  # noqa: E402


def _live(claims):
    return types.SimpleNamespace(
        claims={c["id"]: c for c in claims}, cea={}, evidence={}, observations={}, predictions={},
        record_ref_hash=lambda r: None, artifact_ref_hash=lambda r: None)


def _pack(omitted):
    p = {"id": "ctx-x", "query": "q", "topics": ["t"], "generated_at": "2026-06-22T12:00:00Z",
         "generator_version": "v1", "selection_policy": "test", "token_budget": 100,
         "claim_refs": [], "assessment_refs": [], "artifact_refs": [], "observation_refs": [],
         "prediction_refs": [], "omitted_candidates": omitted, "pack_hash": None}
    p["pack_hash"] = vs.record_hash(p, exclude=("pack_hash",))
    return p


def test_false_review_due_omission_rejected():
    # reason REVIEW_DUE but the live claim is CURRENT → a current claim hidden behind a stale-ish reason
    live = _live([{"id": "clm-c", "lifecycle": "REVIEWED", "freshness_status": "CURRENT"}])
    code, findings = v_ctx.validate_context_pack(_pack([{"id": "clm-c", "reason": "REVIEW_DUE"}]), live)
    assert code == 1 and any("clm-c" in f and "REVIEW_DUE" in f for f in findings), findings


def test_false_ineligible_omission_rejected():
    # reason INELIGIBLE but the live claim IS REVIEWED+CURRENT (i.e. selectable) → cannot be hidden
    live = _live([{"id": "clm-c", "lifecycle": "REVIEWED", "freshness_status": "CURRENT"}])
    code, findings = v_ctx.validate_context_pack(_pack([{"id": "clm-c", "reason": "INELIGIBLE"}]), live)
    assert code == 1 and any("clm-c" in f and "INELIGIBLE" in f for f in findings), findings


def test_truthful_review_due_and_ineligible_omissions_pass():
    live = _live([{"id": "clm-rd", "lifecycle": "REVIEWED", "freshness_status": "REVIEW_DUE"},
                  {"id": "clm-cand", "lifecycle": "CANDIDATE", "freshness_status": "CURRENT"}])
    code, findings = v_ctx.validate_context_pack(
        _pack([{"id": "clm-rd", "reason": "REVIEW_DUE"}, {"id": "clm-cand", "reason": "INELIGIBLE"}]), live)
    assert code == 0, findings

"""WP-AL.7 — the wired DIFFERENT_MODEL refuter. All offline: the one network seam (`_post_chat`) is
replaced by a canned response, so these tests never touch the network or a key. They run on an ISOLATED
tmp_path staged from the skeleton fixtures (never private/corpus), and prove the tool (a) signs a
committed answer from a genuine SURVIVES review, (b) fails CLOSED on an honest REVISE / an unaddressed
claim, (c) refuses to clobber an existing independent review, (d) never lets the model shrink scope or
flip high_impact, and (e) keeps the key out of every artifact."""
import json
import pathlib
import shutil
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import answer_build as ab  # noqa: E402
import refuter_review as rr  # noqa: E402
import validate_schema as vs  # noqa: E402
import verify  # noqa: E402

SK = ROOT / "tests" / "fixtures" / "skeleton"
ASOF = "2026-06-23T00:00:00Z"
KEY = "sk-TEST-SECRET-do-not-log-0000"
_MAP = {
    "skeleton_sources.yaml": "sources.yaml", "skeleton_source_assessments.yaml": "source_assessments.yaml",
    "skeleton_evidence.yaml": "evidence.yaml", "skeleton_claim_evidence.yaml": "claim_evidence.yaml",
    "skeleton_claims.yaml": "baseline/claims.yaml", "skeleton_predictions.yaml": "predictions.yaml",
    "skeleton_observations.yaml": "observations.yaml", "skeleton_geography.yaml": "geography.yaml",
    "skeleton_context_pack.yaml": "context_packs.yaml", "skeleton_analysis.yaml": "analyses.yaml",
    "skeleton_refuter.yaml": "refuters.yaml", "skeleton_visual.yaml": "visuals.yaml",
}


def _stage(root):
    fb = root / "factbase"
    (fb / "baseline").mkdir(parents=True)
    (fb / "live").mkdir(parents=True)
    for src, dst in _MAP.items():
        shutil.copy(SK / src, fb / dst)
    (fb / "live" / "claims.yaml").write_text('schema_version: "2.0"\nclaims: []\n')
    (root / "outputs").mkdir()
    shutil.copy(SK / "skeleton_output.md", root / "outputs" / "ana-skeleton.md")
    return fb


def _read(p):
    return vs.load_yaml_strict(p) or {}


def _drop_skeleton_refuter(fb):
    (fb / "refuters.yaml").write_text('schema_version: "2.0"\nrefuters: []\n')


def _chat_response(content_obj, model="gpt-test", usage=True):
    """A chat-completions-shaped response wrapping the reviewer's STRICT JSON."""
    r = {"id": "resp-test-1", "model": model,
         "choices": [{"message": {"role": "assistant", "content": json.dumps(content_obj)}}]}
    if usage:
        r["usage"] = {"prompt_tokens": 200, "completion_tokens": 80, "total_tokens": 280}
    return r


def _survives_content(claim_ids):
    """A genuine SURVIVES review covering every required claim (all checks PASS, a real disconfirming
    search so a high-impact skeleton claim is satisfied too)."""
    return {
        "verdicts": [{"claim_id": c, "verdict": "SURVIVES", "displacement_check": "PASS",
                      "independence_check": "PASS", "freshness_check": "PASS",
                      "observation_check": "PASS", "reasoning_check": "PASS",
                      "notes": "tried to refute; could not"} for c in sorted(claim_ids)],
        "alternative_hypotheses": ["a competing reading was considered and rejected"],
        "disconfirming_searches": [{"query": "skeleton crossing not a road bridge",
                                    "result": "no contrary artifact found"}],
        "unresolved_gaps": ["reviewed the same curated pack the author saw"],
    }


def _required_claims(root):
    live = ab.Live(root)
    ana = live.analyses["ana-skeleton"]
    rc, _rce, floor = verify._gate_computed_refuter_scope(ana, live)
    return rc, floor


# ---- end-to-end (staged skeleton, mocked model) ----------------------------------------------------

def test_survives_signs_committed_answer(tmp_path):
    fb = _stage(tmp_path)
    _drop_skeleton_refuter(fb)
    rc, floor = _required_claims(tmp_path)
    assert not floor, floor  # skeleton support floor is met
    resp = _chat_response(_survives_content(rc))
    code, lines = rr.run_review(tmp_path, "ana-skeleton", ASOF, "gpt-test", KEY,
                                post=lambda *a, **k: resp)
    assert code == 0, lines
    ref = _read(fb / "refuters.yaml")["refuters"][0]
    assert ref["reviewer_class"] == "DIFFERENT_MODEL" and ref["reviewer"] == "openai:gpt-test"
    assert set(ref["reviewed_claim_ids"]) >= rc
    # the committed-answer gate now passes end to end
    assert verify.answer_check(tmp_path, "ana-skeleton", ASOF)[0] == 0
    # a reproducibility sidecar was written
    manifests = list((tmp_path / "run_manifests").glob("*.json"))
    assert len(manifests) == 1


def test_honest_revise_blocks_and_is_not_persisted(tmp_path):
    fb = _stage(tmp_path)
    _drop_skeleton_refuter(fb)
    rc, _ = _required_claims(tmp_path)
    content = _survives_content(rc)
    for v in content["verdicts"]:
        v["verdict"] = "REVISE"  # the reviewer honestly declines to certify
    resp = _chat_response(content)
    code, lines = rr.run_review(tmp_path, "ana-skeleton", ASOF, "gpt-test", KEY,
                                post=lambda *a, **k: resp)
    assert code != 0, lines
    assert _read(fb / "refuters.yaml")["refuters"] == []  # fail-closed: nothing persisted
    # but the review DID run → the run-manifest is still recorded (honest residue)
    assert list((tmp_path / "run_manifests").glob("*.json"))
    assert verify.answer_check(tmp_path, "ana-skeleton", ASOF)[0] != 0


def test_unaddressed_claim_stays_revise_and_blocks(tmp_path):
    fb = _stage(tmp_path)
    _drop_skeleton_refuter(fb)
    rc, _ = _required_claims(tmp_path)
    assert rc  # there is at least one required claim to drop
    resp = _chat_response({"verdicts": [], "alternative_hypotheses": [],
                           "disconfirming_searches": [], "unresolved_gaps": []})
    code, lines = rr.run_review(tmp_path, "ana-skeleton", ASOF, "gpt-test", KEY,
                                post=lambda *a, **k: resp)
    assert code != 0
    assert any("no usable verdict" in ln for ln in lines), lines
    assert _read(fb / "refuters.yaml")["refuters"] == []


def test_failed_review_preserves_existing_scaffold(tmp_path):
    # atomicity: a non-certifying review must drop the NEW refuter and leave a replaceable
    # SAME_MODEL_FRESH_CONTEXT scaffold intact (never destroy the scaffold before the new one certifies).
    fb = _stage(tmp_path)
    live = ab.Live(tmp_path)
    scaffold, _ = ab.scaffold_refuter(live.analyses["ana-skeleton"], live, ASOF)
    (fb / "refuters.yaml").write_text(
        yaml.safe_dump({"schema_version": "2.0", "refuters": [scaffold]}, sort_keys=False))
    rc, _ = _required_claims(tmp_path)
    content = _survives_content(rc)
    for v in content["verdicts"]:
        v["verdict"] = "REVISE"
    resp = _chat_response(content)
    code, _ = rr.run_review(tmp_path, "ana-skeleton", ASOF, "gpt-test", KEY, post=lambda *a, **k: resp)
    assert code != 0
    doc = _read(fb / "refuters.yaml")
    assert len(doc["refuters"]) == 1
    assert doc["refuters"][0]["reviewer_class"] == "SAME_MODEL_FRESH_CONTEXT"  # scaffold untouched


def test_survives_replaces_existing_scaffold_with_exactly_one(tmp_path):
    # the success path with a scaffold present: end state is exactly ONE refuter (the signed one).
    fb = _stage(tmp_path)
    live = ab.Live(tmp_path)
    scaffold, _ = ab.scaffold_refuter(live.analyses["ana-skeleton"], live, ASOF)
    (fb / "refuters.yaml").write_text(
        yaml.safe_dump({"schema_version": "2.0", "refuters": [scaffold]}, sort_keys=False))
    rc, _ = _required_claims(tmp_path)
    resp = _chat_response(_survives_content(rc))
    code, _ = rr.run_review(tmp_path, "ana-skeleton", ASOF, "gpt-test", KEY, post=lambda *a, **k: resp)
    assert code == 0
    doc = _read(fb / "refuters.yaml")
    assert len(doc["refuters"]) == 1 and doc["refuters"][0]["reviewer_class"] == "DIFFERENT_MODEL"
    assert verify.answer_check(tmp_path, "ana-skeleton", ASOF)[0] == 0


def test_refuses_to_clobber_a_signed_refuter(tmp_path):
    fb = _stage(tmp_path)
    doc = _read(fb / "refuters.yaml")
    doc["refuters"][0]["reviewer_class"] = "HUMAN"  # an existing independent review
    doc["refuters"][0]["reviewer"] = "human:tim"
    (fb / "refuters.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))
    before = (fb / "refuters.yaml").read_bytes()

    def _boom(*a, **k):
        raise AssertionError("must not call the model when refusing to clobber")
    code, lines = rr.run_review(tmp_path, "ana-skeleton", ASOF, "gpt-test", KEY, post=_boom)
    assert code == 1 and any("clobber" in ln for ln in lines), lines
    assert (fb / "refuters.yaml").read_bytes() == before  # untouched


def test_dry_run_makes_no_call_and_writes_nothing(tmp_path):
    fb = _stage(tmp_path)
    before = (fb / "refuters.yaml").read_bytes()

    def _boom(*a, **k):
        raise AssertionError("dry-run must not touch the network")
    code, lines = rr.run_review(tmp_path, "ana-skeleton", ASOF, "gpt-test", "", dry_run=True, post=_boom)
    assert code == 0, lines
    assert (fb / "refuters.yaml").read_bytes() == before
    assert not (tmp_path / "run_manifests").exists()


def test_key_never_appears_in_any_artifact(tmp_path):
    fb = _stage(tmp_path)
    _drop_skeleton_refuter(fb)
    rc, _ = _required_claims(tmp_path)
    resp = _chat_response(_survives_content(rc))
    code, _ = rr.run_review(tmp_path, "ana-skeleton", ASOF, "gpt-test", KEY, post=lambda *a, **k: resp)
    assert code == 0
    for p in [fb / "refuters.yaml", *(tmp_path / "run_manifests").glob("*.json")]:
        assert KEY not in p.read_text(), p


# ---- pure-function units ---------------------------------------------------------------------------

def test_parse_ignores_model_high_impact_and_extracts_checks():
    content = json.dumps({"verdicts": [{"claim_id": "clm-x", "verdict": "SURVIVES", "high_impact": True,
                                        "displacement_check": "PASS", "independence_check": "FAIL",
                                        "freshness_check": "NOT_APPLICABLE", "observation_check": "PASS",
                                        "reasoning_check": "PASS", "notes": "n"}],
                          "alternative_hypotheses": ["h"],
                          "disconfirming_searches": [{"query": "q", "result": "r"}],
                          "unresolved_gaps": ["g"]})
    vmap, residue = rr.parse_model_verdicts(content)
    assert "clm-x" in vmap
    assert "high_impact" not in vmap["clm-x"]  # the model's flag never enters the verdict
    assert vmap["clm-x"]["independence_check"] == "FAIL"
    assert residue["disconfirming_searches"] == [{"query": "q", "result": "r"}]


def test_parse_tolerates_json_code_fence():
    fenced = "```json\n" + json.dumps({"verdicts": [{"claim_id": "c", "verdict": "SURVIVES"}]}) + "\n```"
    vmap, _ = rr.parse_model_verdicts(fenced)
    assert vmap["c"]["verdict"] == "SURVIVES"


def test_assemble_forces_gate_high_impact_over_model(tmp_path):
    # the model returns a verdict for the skeleton claim; assemble must keep the GATE-computed
    # high_impact (from scaffold_refuter), never the model's word (parse already drops it).
    fb = _stage(tmp_path)
    live = ab.Live(tmp_path)
    ana = live.analyses["ana-skeleton"]
    scaffold, _floor = ab.scaffold_refuter(ana, live, ASOF)
    gate_hi = {v["claim_id"]: v["high_impact"] for v in scaffold["verdicts"]}
    model_v = {cid: {"verdict": "SURVIVES", "displacement_check": "PASS", "independence_check": "PASS",
                     "freshness_check": "PASS", "observation_check": "PASS", "reasoning_check": "PASS",
                     "notes": "x"} for cid in gate_hi}
    ref, _f, unaddressed = rr.assemble_refuter(ana, live, ASOF, "gpt-test", model_v, {})
    assert not unaddressed
    assert ref["reviewer_class"] == "DIFFERENT_MODEL"
    for v in ref["verdicts"]:
        assert v["high_impact"] == gate_hi[v["claim_id"]]  # gate value preserved


def test_run_manifest_has_repro_fields_and_no_key():
    refuter = {"id": "ref-x", "verdicts": [{"claim_id": "c", "verdict": "SURVIVES"}]}
    resp = {"id": "r1", "model": "gpt-x-2026", "usage": {"total_tokens": 42}}
    m = rr.build_run_manifest("ana-x", refuter, "gpt-x", rr.DEFAULT_BASE_URL, 0.0, {"q": 1}, resp, ASOF)
    for k in ("model", "prompt_version", "temperature", "request_hash", "system_prompt_hash",
              "code_version", "usage", "raw_responses", "samples", "survive_votes",
              "model_version_reported"):
        assert k in m, k
    assert m["model_version_reported"] == "gpt-x-2026" and m["usage"]["total_tokens"] == 42
    assert m["samples"] == 1 and m["raw_responses"] == [resp]  # single response wrapped in a list
    assert KEY not in json.dumps(m)  # defensive: the key is never passed to this builder


# ---- multi-sample gate (Phase A hardening) ---------------------------------------------------------

def _scripted_post(responses):
    """A stateful post() returning each response in turn (then the last) — simulates the model's
    run-to-run non-determinism across the multi-sample gate."""
    state = {"i": 0}

    def post(*a, **k):
        r = responses[min(state["i"], len(responses) - 1)]
        state["i"] += 1
        return r
    return post


def _response_verdict(claim_ids, verdict):
    return _chat_response({
        "verdicts": [{"claim_id": c, "verdict": verdict, "displacement_check": "PASS",
                      "independence_check": "PASS", "freshness_check": "PASS",
                      "observation_check": "PASS", "reasoning_check": "PASS", "notes": "x"}
                     for c in sorted(claim_ids)],
        "alternative_hypotheses": [], "disconfirming_searches": [{"query": "q", "result": "r"}],
        "unresolved_gaps": []})


def test_synthesize_majority_and_most_adverse():
    def s(v):
        return ({"c": {"verdict": v, "displacement_check": "PASS", "independence_check": "PASS",
                       "freshness_check": "PASS", "observation_check": "PASS",
                       "reasoning_check": "PASS", "notes": None}},
                {"disconfirming_searches": [{"query": "q", "result": "r"}]})
    syn, res, votes = rr._synthesize_samples(
        [s("SURVIVES"), s("SURVIVES"), s("SURVIVES"), s("SURVIVES"), s("REVISE")], 4, set())
    assert syn["c"]["verdict"] == "SURVIVES" and votes["c"]["survives"] == 4
    assert res["disconfirming_searches"] == [{"query": "q", "result": "r"}]  # unioned + deduped
    syn2, _r, votes2 = rr._synthesize_samples(
        [s("SURVIVES"), s("REVISE"), s("DOWNGRADE"), s("REVISE"), s("REVISE")], 4, set())
    assert syn2["c"]["verdict"] == "DOWNGRADE" and votes2["c"]["survives"] == 1  # most adverse


def test_multisample_commits_robust_claim(tmp_path):
    import glob
    fb = _stage(tmp_path)
    _drop_skeleton_refuter(fb)
    rc, _ = _required_claims(tmp_path)
    resp = _response_verdict(rc, "SURVIVES")  # every sample survives
    code, lines = rr.run_review(tmp_path, "ana-skeleton", ASOF, "gpt-test", KEY,
                                post=lambda *a, **k: resp, samples=5, survive_threshold=4)
    assert code == 0, lines
    assert verify.answer_check(tmp_path, "ana-skeleton", ASOF)[0] == 0
    m = json.loads(open(sorted(glob.glob(str(tmp_path / "run_manifests" / "*.json")))[-1]).read())
    assert m["samples"] == 5 and all(v["survives"] == 5 for v in m["survive_votes"].values())


def test_multisample_blocks_borderline_claim(tmp_path):
    # a claim SURVIVING only 2 of 5 samples must NOT commit at threshold 4 (the non-determinism fix:
    # a lucky-single-SURVIVE claim is reliably caught, and re-rolling can't sneak it through).
    import glob
    fb = _stage(tmp_path)
    _drop_skeleton_refuter(fb)
    rc, _ = _required_claims(tmp_path)
    scripted = _scripted_post([_response_verdict(rc, v) for v in
                               ("SURVIVES", "REVISE", "SURVIVES", "REVISE", "REVISE")])
    code, lines = rr.run_review(tmp_path, "ana-skeleton", ASOF, "gpt-test", KEY,
                                post=scripted, samples=5, survive_threshold=4)
    assert code != 0, lines
    assert _read(fb / "refuters.yaml")["refuters"] == []  # fail-closed, nothing persisted
    m = json.loads(open(sorted(glob.glob(str(tmp_path / "run_manifests" / "*.json")))[-1]).read())
    assert all(v["survives"] == 2 for v in m["survive_votes"].values())  # 2/5 recorded honestly


def test_synthesize_omission_shortfall_never_survives():
    # P0 regression: a claim SURVIVES in <K PRESENT samples and is OMITTED from the rest must NOT
    # synthesize to SURVIVES (a lucky partial SURVIVE via omission cannot slip the gate).
    def present(v):
        return ({"c": {"verdict": v, "displacement_check": "PASS", "independence_check": "PASS",
                       "freshness_check": "PASS", "observation_check": "PASS",
                       "reasoning_check": "PASS", "notes": None}}, {})
    absent = ({}, {})  # the model omitted the claim entirely this sample
    syn, _r, votes = rr._synthesize_samples(
        [present("SURVIVES"), present("SURVIVES"), present("SURVIVES"), absent, absent], 4, set())
    assert votes["c"]["survives"] == 3 and votes["c"]["total"] == 5
    assert syn["c"]["verdict"] != "SURVIVES"  # below threshold -> forced to a blocking verdict


def test_multisample_blocks_omission_shortfall(tmp_path):
    # P0 regression end-to-end: a claim SURVIVES in 3/5 samples and is OMITTED from the other 2 must NOT
    # commit at threshold 4 (the fail-open the adversarial review caught).
    import glob
    fb = _stage(tmp_path)
    _drop_skeleton_refuter(fb)
    rc, _ = _required_claims(tmp_path)
    surv = _response_verdict(rc, "SURVIVES")
    empty = _chat_response({"verdicts": [], "alternative_hypotheses": [],
                            "disconfirming_searches": [], "unresolved_gaps": []})
    scripted = _scripted_post([surv, surv, surv, empty, empty])  # each claim SURVIVES 3/5, omitted 2/5
    code, lines = rr.run_review(tmp_path, "ana-skeleton", ASOF, "gpt-test", KEY,
                                post=scripted, samples=5, survive_threshold=4)
    assert code != 0, lines  # below threshold -> blocked, not committed
    assert _read(fb / "refuters.yaml")["refuters"] == []  # fail-closed
    m = json.loads(open(sorted(glob.glob(str(tmp_path / "run_manifests" / "*.json")))[-1]).read())
    assert all(v["survives"] == 3 for v in m["survive_votes"].values())


def test_redirect_handler_strips_auth_cross_host():
    import urllib.request
    h = rr._NoAuthLeakRedirect()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 headers={"Authorization": "Bearer sk-x", "Content-type": "application/json"})
    cross = h.redirect_request(req, None, 302, "Found", {}, "https://evil.example.com/x")
    assert cross is not None and not any(k.lower() == "authorization" for k in cross.headers)
    same = h.redirect_request(req, None, 302, "Found", {}, "https://api.openai.com/v2/x")
    assert any(k.lower() == "authorization" for k in same.headers)  # same host keeps auth


def test_parse_non_object_raises_valueerror_not_crash():
    # a non-object top level must raise ValueError (run_review catches it -> clean exit 2), never a
    # TypeError/AttributeError traceback.
    import pytest
    for bad in ("[1,2,3]", '"a string"', "42"):
        with pytest.raises(ValueError):
            rr.parse_model_verdicts(bad)


def test_parse_bad_field_types_degrade_closed():
    # a dict whose `verdicts` is not a list must not crash: it yields empty verdicts, so every required
    # claim is unaddressed -> stays REVISE -> blocks (the fail-closed outcome) rather than a traceback.
    vmap, residue = rr.parse_model_verdicts('{"verdicts": 5, "unresolved_gaps": "none"}')
    assert vmap == {} and residue["unresolved_gaps"] == []


def test_parse_duplicate_verdicts_keeps_most_adverse():
    content = json.dumps({"verdicts": [
        {"claim_id": "c", "verdict": "SURVIVES", "independence_check": "PASS"},
        {"claim_id": "c", "verdict": "REJECT", "independence_check": "FAIL"}]})
    vmap, _ = rr.parse_model_verdicts(content)
    assert vmap["c"]["verdict"] == "REJECT"  # the REJECT is not hidden behind the SURVIVES


def test_norm_check_preserves_miscased_fail():
    assert rr._norm_check("fail") == "FAIL" and rr._norm_check("Failed") == "FAIL"
    assert rr._norm_check("n/a") == "NOT_APPLICABLE" and rr._norm_check("banana") == "NOT_APPLICABLE"


def test_pick_strongest_model():
    # version-aware: highest gpt-N.M, dropping non-chat / mini-nano / pro-codex-chat variants
    assert rr.pick_strongest_model(
        ["text-embedding-3-large", "gpt-4o-mini", "gpt-4o", "o3", "gpt-5-2025-08-01", "gpt-5",
         "gpt-5-nano", "whisper-1"]) == "gpt-5"
    # a newer flagship beats the bare original; pro/codex/dated variants are avoided
    assert rr.pick_strongest_model(
        ["gpt-5", "gpt-5.5", "gpt-5.5-pro", "gpt-5.5-codex", "gpt-5.4", "gpt-5.5-2026-04-23",
         "o4-mini"]) == "gpt-5.5"
    assert rr.pick_strongest_model(["text-embedding-3-large", "whisper-1"]) is None
    # only reduced variants remain → relax and take the highest-version one
    assert rr.pick_strongest_model(["gpt-4o-mini", "o1-mini"]) == "gpt-4o-mini"

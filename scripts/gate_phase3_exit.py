#!/usr/bin/env python3
"""Phase-3 EXIT auto-gate — the machine check at the Milestone-A boundary (Phase 3 → Milestone A).

Named witnesses, fail-closed, exit 0 or 2 ONLY (a boundary gate halts or clears, never 1):

  R3 (fail-closed)   W-DRAFT-EMPTY, W-ANSWER-NO-ANALYSIS, W-ANSWER-NO-REFUTER, W-SUBGATE-PROPAGATE
  R5 (skeleton)      W-DRAFT-COMPOSE, W-ANSWER-COMPOSE  (the Milestone-A "passes answer mode" witness)
  R4 (A-exploits)    W-A7-STRUCTURAL, W-A7-SEMANTIC-BLOCKS, W-REFUTER-COVERAGE, W-REFUTER-BINDING,
                     W-V-P0-1-REFUTER (the contest + independence-floor invariants)
  drift backstop     W-PHASE2-GREEN  (which itself wraps the Phase-1 gate — Phases 1-2 cannot regress)

Each witness returns None (clear) or an error string (fail). Run at the boundary:
  pytest -q && python scripts/gate_phase3_exit.py && python scripts/gate_phase2_exit.py
"""
from __future__ import annotations

import shutil
import sys
import tempfile
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_phase2_exit as g2  # noqa: E402
import validate_high_impact as v_hi  # noqa: E402
import validate_output as v_out  # noqa: E402
import validate_refuter as v_ref  # noqa: E402
import validate_schema as vs  # noqa: E402
import verify  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
SK = REPO / "tests" / "fixtures" / "skeleton"
ASOF = "2026-06-23T00:00:00Z"

_MAP = {
    "skeleton_sources.yaml": "sources.yaml", "skeleton_source_assessments.yaml": "source_assessments.yaml",
    "skeleton_evidence.yaml": "evidence.yaml", "skeleton_claim_evidence.yaml": "claim_evidence.yaml",
    "skeleton_claims.yaml": "baseline/claims.yaml", "skeleton_predictions.yaml": "predictions.yaml",
    "skeleton_observations.yaml": "observations.yaml", "skeleton_geography.yaml": "geography.yaml",
    "skeleton_context_pack.yaml": "context_packs.yaml", "skeleton_analysis.yaml": "analyses.yaml",
    "skeleton_refuter.yaml": "refuters.yaml", "skeleton_visual.yaml": "visuals.yaml",
}


def stage_answer_layer(root: Path) -> Path:
    """Materialize the full Milestone-A skeleton (factbase + answer-layer registries + the staged
    output text) into <root>, so draft/answer compose against a real tree."""
    fb = root / "factbase"
    (fb / "baseline").mkdir(parents=True)
    (fb / "live").mkdir(parents=True)
    for src, dst in _MAP.items():
        shutil.copy(SK / src, fb / dst)
    (fb / "live" / "claims.yaml").write_text('schema_version: "2.0"\nclaims: []\n')
    (root / "outputs").mkdir()
    shutil.copy(SK / "skeleton_output.md", root / "outputs" / "ana-skeleton.md")
    return fb


# ---- R3 / R5 witnesses (stage a tmp tree) ----
def _draft_empty() -> str | None:
    code, _ = verify.draft_check(REPO, "ana-skeleton", ASOF)  # real factbase is empty of claims
    return None if code == 2 else f"draft on the empty real factbase returned {code}, expected 2"


def _draft_compose() -> str | None:
    with tempfile.TemporaryDirectory() as d:
        stage_answer_layer(Path(d))
        code, lines = verify.draft_check(Path(d), "ana-skeleton", ASOF)
    return None if code == 0 else f"draft did not compose the skeleton (exit {code}): {lines[-1:]}"


def _answer_compose() -> str | None:  # the Milestone-A witness
    with tempfile.TemporaryDirectory() as d:
        stage_answer_layer(Path(d))
        code, lines = verify.answer_check(Path(d), "ana-skeleton", ASOF)
    return None if code == 0 else f"answer did not compose the skeleton (exit {code}): {lines[-1:]}"


def _answer_no_analysis() -> str | None:
    with tempfile.TemporaryDirectory() as d:
        stage_answer_layer(Path(d))
        code, _ = verify.answer_check(Path(d), None, ASOF)
    return None if code == 2 else f"answer with no --analysis returned {code}, expected 2"


def _answer_no_refuter() -> str | None:
    with tempfile.TemporaryDirectory() as d:
        fb = stage_answer_layer(Path(d))
        (fb / "refuters.yaml").write_text('schema_version: "2.0"\nrefuters: []\n')
        code, _ = verify.answer_check(Path(d), "ana-skeleton", ASOF)
    return None if code == 2 else f"answer with a missing refuter returned {code}, expected 2"


def _subgate_propagate() -> str | None:
    with tempfile.TemporaryDirectory() as d:
        fb = stage_answer_layer(Path(d))
        (fb / "claim_evidence.yaml").write_text('schema_version: "9.9"\nclaim_evidence_assessments: []\n')
        code, _ = verify.answer_check(Path(d), "ana-skeleton", ASOF)
    return None if code == 2 else f"answer over a broken upstream layer returned {code}, expected 2 (no masking)"


# ---- R4 A-exploit standing invariants (minimal in-memory builders) ----
HM, OH = "sha256:" + "a" * 64, "sha256:" + "b" * 64
_NORMAL = {"id": "clm-n", "text": "t", "epistemic_type": "FACT", "topics": ["transport"],
           "high_impact": False, "support_status": "SUPPORTED", "dispute_status": "UNCONTESTED",
           "freshness_status": "CURRENT", "lifecycle": "REVIEWED", "stability": "DURABLE"}
_HI = {**_NORMAL, "id": "clm-hi", "topics": ["casualties"]}


def _live(claims=(_NORMAL,)):
    return types.SimpleNamespace(claims={c["id"]: c for c in claims}, observations={})


def _verdict(cid, **kw):
    v = {"claim_id": cid, "verdict": "SURVIVES", "displacement_check": "PASS",
         "independence_check": "PASS", "freshness_check": "PASS", "observation_check": "PASS",
         "reasoning_check": "NOT_APPLICABLE"}
    v.update(kw)
    return v


def _ana(claim_ids, cea_ids=("cea-1",)):
    return {"manifest_hash": HM, "output_hash": OH,
            "claim_markers": {f"c{i}": {"claim_id": c, "claim_hash": "x"} for i, c in enumerate(claim_ids)},
            "claim_evidence_assessment_refs": [{"id": x, "record_hash": "x"} for x in cea_ids],
            "observation_refs": [], "narrative_exemptions": []}


def _ref(claim_ids, cea_ids=("cea-1",), reviewer_class="HUMAN", verdicts=None, manifest_hash=HM):
    return {"manifest_hash": manifest_hash, "output_hash": OH, "reviewer_class": reviewer_class,
            "reviewed_claim_ids": list(claim_ids), "reviewed_assessment_ids": list(cea_ids),
            "verdicts": verdicts if verdicts is not None else [_verdict(c) for c in claim_ids],
            "exemptions_reviewed": []}


def _ana_with_output(d: Path, name: str, prose: str, markers: dict):
    # distinct filename per analysis: a shared file would let one overwrite another, so the second's
    # output_hash would mismatch and trip the binding check BEFORE the intended marker check (vacuous).
    (d / "outputs").mkdir(exist_ok=True)
    f = d / "outputs" / f"{name}.md"
    f.write_text(prose, encoding="utf-8")
    return {"output_path": f"outputs/{name}.md", "output_hash": vs.file_content_hash(f),
            "claim_markers": markers, "narrative_exemptions": []}


def _a7_structural() -> str | None:
    with tempfile.TemporaryDirectory() as dd:
        d = Path(dd)
        dangling = _ana_with_output(d, "dangling", "Road open. [[c1]] Rail too. [[c9]]\n",
                                    {"c1": {"claim_id": "clm-n", "claim_hash": "x"}})
        extra = _ana_with_output(d, "extra", "Road open. [[c1]]\n",
                                 {"c1": {"claim_id": "clm-n", "claim_hash": "x"},
                                  "c2": {"claim_id": "clm-n", "claim_hash": "x"}})
        c1, f1 = v_out.validate_output(dangling, _live(), d, block_unmarked=True)
        c2, f2 = v_out.validate_output(extra, _live(), d, block_unmarked=True)
    # assert each fires its INTENDED control (not an incidental output-hash mismatch)
    if c1 != 1 or not any("does not resolve" in x for x in f1):
        return f"A7-structural REGRESSED: dangling marker not caught (exit {c1}): {f1}"
    if c2 != 1 or not any("never cited" in x for x in f2):
        return f"A7-structural REGRESSED: extra manifest claim not caught (exit {c2}): {f2}"
    return None


def _a7_semantic_blocks() -> str | None:
    with tempfile.TemporaryDirectory() as dd:
        d = Path(dd)
        ana = _ana_with_output(d, "sem", "Russia lost sixty thousand troops in May. Road open. [[c1]]\n",
                               {"c1": {"claim_id": "clm-n", "claim_hash": "x"}})
        warn = v_out.validate_output(ana, _live(), d, block_unmarked=False)[0]
        block = v_out.validate_output(ana, _live(), d, block_unmarked=True)[0]
    if warn != 0:
        return f"A7-semantic REGRESSED: draft WARN should be exit 0, got {warn}"
    if block != 1:
        return f"A7-semantic REGRESSED: answer should BLOCK an unmarked assertion (exit 1), got {block}"
    return None


def _refuter_coverage() -> str | None:
    code = v_ref.validate_refuter(_ref(["clm-n"], verdicts=[_verdict("clm-n")]),
                                  _ana(["clm-n", "clm-x"]), _live())[0]
    return None if code == 1 else f"REFUTER-COVERAGE REGRESSED: under-coverage returned {code}, expected 1"


def _refuter_binding() -> str | None:
    code = v_ref.validate_refuter(_ref(["clm-n"], manifest_hash="sha256:" + "c" * 64),
                                  _ana(["clm-n"]), _live())[0]
    return None if code == 1 else f"REFUTER-BINDING REGRESSED: wrong manifest_hash returned {code}, expected 1"


def _v_p0_1_refuter() -> str | None:
    triggers = v_hi.trigger_set()
    # uncontested high_impact-false on a trigger (casualties) claim must fail
    uncontested = v_ref.validate_refuter(
        _ref(["clm-hi"], reviewer_class="DIFFERENT_MODEL", verdicts=[_verdict("clm-hi")]),
        _ana(["clm-hi"]), _live([_HI]), triggers)[0]
    # SAME_MODEL_FRESH_CONTEXT on a committed answer must fail (independence floor)
    samemodel = v_ref.validate_refuter(
        _ref(["clm-n"], reviewer_class="SAME_MODEL_FRESH_CONTEXT"), _ana(["clm-n"]), _live(), triggers)[0]
    bad = [n for n, c in (("high_impact-false-uncontested", uncontested),
                          ("same_model-on-committed", samemodel)) if c != 1]
    return f"V-P0-1 REGRESSED: {bad} did not exit 1" if bad else None


def _hi_prose_laundering_blocks() -> str | None:
    # cross-vendor review P0-4: a high-impact assertion hidden beside a low-impact marker must block.
    with tempfile.TemporaryDirectory() as dd:
        d = Path(dd)
        ana = _ana_with_output(d, "hilaunder", "Road open and Russia killed 500 civilians. [[c1]]\n",
                               {"c1": {"claim_id": "clm-n", "claim_hash": "x"}})  # clm-n is low-impact
        code = v_out.validate_output(ana, _live(), d, block_unmarked=True)[0]
    return None if code == 1 else f"HI-PROSE-LAUNDERING REGRESSED: returned {code}, expected 1"


def _refuter_reject_blocks() -> str | None:
    # cross-vendor review P0-1: a REJECT verdict must block a committed answer (answer_mode=True),
    # while remaining a valid stored record (answer_mode=False).
    ref = _ref(["clm-n"], verdicts=[_verdict("clm-n", verdict="REJECT")])
    ana = _ana(["clm-n"])
    stored = v_ref.validate_refuter(ref, ana, _live())[0]
    committed = v_ref.validate_refuter(ref, ana, _live(), answer_mode=True)[0]
    if stored != 0:
        return f"REFUTER-REJECT REGRESSED: a REJECT record should be storable (got {stored}, expected 0)"
    if committed != 1:
        return f"REFUTER-REJECT REGRESSED: a REJECT verdict must block a committed answer (got {committed}, expected 1)"
    return None


def _hi_contest_stored_true() -> str | None:
    # R2-P0-3: a CORRECTLY-stored high_impact: true claim must STILL be contested (the old gate only
    # fired on an author downgrade); and a committed high-impact answer must carry an impact_category.
    triggers = v_hi.trigger_set()
    st = {**_NORMAL, "id": "clm-st", "high_impact": True}
    uncontested = v_ref.validate_refuter(
        _ref(["clm-st"], reviewer_class="DIFFERENT_MODEL", verdicts=[_verdict("clm-st")]),
        _ana(["clm-st"]), _live([st]), triggers)[0]
    uncat = v_ref.validate_refuter(
        _ref(["clm-hi"], reviewer_class="DIFFERENT_MODEL",
             verdicts=[_verdict("clm-hi", high_impact=True, independence_check="PASS")]),
        _ana(["clm-hi"]), _live([_HI]), triggers, answer_mode=True)[0]
    bad = [n for n, c in (("stored-true-uncontested", uncontested),
                          ("answer-uncategorized-high-impact", uncat)) if c != 1]
    return f"HI-CONTEST REGRESSED: {bad} did not exit 1" if bad else None


def _refuter_scope_gate_computed() -> str | None:
    # R2-P0-1: emptying the manifest's assessment refs AND the refuter's reviewed set must NOT pass —
    # the marked claim's active CHECKED support is GATE-COMPUTED into the required set.
    import re
    with tempfile.TemporaryDirectory() as dd:
        d = Path(dd)
        fb = stage_answer_layer(d)
        a = re.sub(r"    claim_evidence_assessment_refs:\n      - \{[^}]*\}\n",
                   "    claim_evidence_assessment_refs: []\n", (fb / "analyses.yaml").read_text())
        (fb / "analyses.yaml").write_text(a)
        r = (fb / "refuters.yaml").read_text().replace(
            "reviewed_assessment_ids: [cea-skeleton-owner-to-modes]", "reviewed_assessment_ids: []")
        (fb / "refuters.yaml").write_text(r)
        code, lines = verify.answer_check(d, "ana-skeleton", ASOF)
    if code != 1 or not any("gate-computed required set" in ln for ln in lines):
        return f"REFUTER-SCOPE REGRESSED: manifest-shrunk answer returned {code}, expected 1 + gate-computed msg"
    return None


def _refuter_dup_verdicts_block() -> str | None:
    # R3-P0-2: a REJECT hidden behind a later SURVIVES (duplicate verdicts for one claim) must block.
    ref = _ref(["clm-n"], verdicts=[_verdict("clm-n", verdict="REJECT"),
                                    _verdict("clm-n", verdict="SURVIVES")])
    code = v_ref.validate_refuter(ref, _ana(["clm-n"]), _live(), answer_mode=True)[0]
    return None if code == 1 else f"DUP-VERDICTS REGRESSED: returned {code}, expected 1"


def _refuter_scope_opposing_visual() -> str | None:
    # R3-P0-1/-4: the gate-computed scope must include active OPPOSING assessments + visual inputs.
    def _c(i, cid, st):
        return {"id": i, "claim_id": cid, "artifact_id": f"evd-{i}", "stance": st,
                "semantic_review": {"status": "CHECKED"}, "supersedes": None}
    live = types.SimpleNamespace(
        claims={"clm-a": {"id": "clm-a", "epistemic_type": "FACT"},
                "clm-v": {"id": "clm-v", "epistemic_type": "FACT"}},
        cea={"s": _c("cea-s", "clm-a", "SUPPORTS"), "r": _c("cea-r", "clm-a", "REFUTES"),
             "vs": _c("cea-vs", "clm-v", "SUPPORTS")},
        context_packs={}, visuals={"v": {"input_claim_refs": [{"id": "clm-v"}],
                                         "input_claim_evidence_assessment_refs": [{"id": "cea-vis"}]}})
    ana = {"claim_markers": {"c": {"claim_id": "clm-a"}}, "claim_evidence_assessment_refs": [],
           "context_pack_id": None, "visual_refs": [{"id": "v"}]}
    rc, rceas, _ = verify._gate_computed_refuter_scope(ana, live)
    missing = [x for x in ("cea-r", "cea-vis") if x not in rceas] + (["clm-v"] if "clm-v" not in rc else [])
    return None if not missing else f"SCOPE REGRESSED: {missing} not in gate-computed refuter scope"


def _multiple_refuters_fail_closed() -> str | None:
    # R3-P0-3: a second refuter binding the same analysis/manifest/output must fail closed.
    with tempfile.TemporaryDirectory() as dd:
        d = Path(dd)
        fb = stage_answer_layer(d)
        text = (fb / "refuters.yaml").read_text()
        _, _, record = text.partition("refuters:\n")
        second = record.replace("id: ref-skeleton", "id: ref-skeleton-negative").replace(
            "verdict: SURVIVES", "verdict: REJECT")
        (fb / "refuters.yaml").write_text(text + second)
        code, lines = verify.answer_check(d, "ana-skeleton", ASOF)
    return None if code == 2 and any("refuters bind" in ln for ln in lines) else \
        f"MULTI-REFUTER REGRESSED: returned {code}, expected 2"


def _visual_spec_self_hash() -> str | None:
    # R3-P1-1: a tampered visual body (spec_hash left unchanged) must fail manifest_structural.
    with tempfile.TemporaryDirectory() as dd:
        d = Path(dd)
        fb = stage_answer_layer(d)
        (fb / "visuals.yaml").write_text((fb / "visuals.yaml").read_text().replace(
            "title: ", "title: TAMPERED ", 1))
        code, lines = verify.draft_check(d, "ana-skeleton", ASOF)
    return None if code == 1 and any("spec_hash is self-inconsistent" in ln for ln in lines) else \
        f"VISUAL-SELF-HASH REGRESSED: returned {code}, expected 1"


def _phase2_green() -> str | None:
    return None if g2.main() == 0 else "the Phase-2 exit gate is not green (cumulative drift reached Phases 1-2)"


def main() -> int:
    witnesses = [
        ("W-DRAFT-EMPTY", _draft_empty), ("W-DRAFT-COMPOSE", _draft_compose),
        ("W-ANSWER-COMPOSE", _answer_compose), ("W-ANSWER-NO-ANALYSIS", _answer_no_analysis),
        ("W-ANSWER-NO-REFUTER", _answer_no_refuter), ("W-SUBGATE-PROPAGATE", _subgate_propagate),
        ("W-A7-STRUCTURAL", _a7_structural), ("W-A7-SEMANTIC-BLOCKS", _a7_semantic_blocks),
        ("W-REFUTER-COVERAGE", _refuter_coverage), ("W-REFUTER-BINDING", _refuter_binding),
        ("W-V-P0-1-REFUTER", _v_p0_1_refuter), ("W-REFUTER-REJECT-BLOCKS", _refuter_reject_blocks),
        ("W-HI-PROSE-LAUNDERING", _hi_prose_laundering_blocks),
        ("W-HI-CONTEST-STORED-TRUE", _hi_contest_stored_true),
        ("W-REFUTER-SCOPE-GATE-COMPUTED", _refuter_scope_gate_computed),
        ("W-REFUTER-DUP-VERDICTS", _refuter_dup_verdicts_block),
        ("W-REFUTER-SCOPE-OPPOSING-VISUAL", _refuter_scope_opposing_visual),
        ("W-MULTIPLE-REFUTERS", _multiple_refuters_fail_closed),
        ("W-VISUAL-SPEC-SELF-HASH", _visual_spec_self_hash), ("W-PHASE2-GREEN", _phase2_green),
    ]
    problems = []
    for name, fn in witnesses:
        msg = fn()
        if msg:
            problems.append(f"{name}: {msg}")
    if problems:
        print("PHASE-3 EXIT GATE: FAIL (halt — fail closed)", file=sys.stderr)
        for p in problems:
            print(f"  [gate] {p}", file=sys.stderr)
        return 2
    print("PHASE-3 EXIT GATE: PASS — answer composes the Milestone-A skeleton; draft/answer fail "
          "closed on empty/missing-analysis/missing-refuter/broken-upstream; the A7 (structural + "
          "semantic-block), refuter coverage/binding, and V-P0-1 contest/independence invariants all "
          "fire; the Phase-2 gate is green. MILESTONE A reached.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

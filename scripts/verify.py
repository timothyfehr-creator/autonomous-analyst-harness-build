#!/usr/bin/env python3
"""WP0.1 — unified verifier (mode ladder).

Modes:
  conversational  Tier 0 is UNVERIFIED BY DESIGN — exit 0 with a loud notice that is never a
                  gate PASS (see CONVERSATION.md). Present so the tier ladder is discoverable.
  scaffold        (default) required governing documents + adjudication READY (reuses the WP0.0
                  gate) + runtime directories + dependency availability. exit 0 / 2.
  records         reserved until Phase 2 — exit 2 (explicitly unavailable; SKIP is not PASS).
  draft / answer  reserved until Phase 3 — exit 2.
  <unknown>       exit 2 (fail closed).

Exit codes (per AGENTS.md): 0 clean · 1 findings in valid input · 2 cannot-run / unavailable.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling import
import check_review_adjudication as cra  # noqa: E402
# Phase-2 integrity gates composed by --mode records (import-not-subprocess; each is __main__-guarded):
import validate_assessment_governance as v_gov  # noqa: E402
import validate_claim_evidence as v_cea  # noqa: E402
import validate_claims as v_clm  # noqa: E402
import validate_conflict as v_con  # noqa: E402
import validate_evidence as v_evd  # noqa: E402
import validate_freshness as v_fresh  # noqa: E402
import validate_high_impact as v_hi  # noqa: E402
import validate_observations as v_obs  # noqa: E402
import validate_schema as vs  # noqa: E402
import validate_sources as v_src  # noqa: E402
import validate_support as v_sup  # noqa: E402
# Phase-3 answer-layer gates (WP3.1+):
import answer_layer as al  # noqa: E402
import validate_context_pack as v_ctx  # noqa: E402
import validate_manifest_structural as v_man  # noqa: E402
import validate_output as v_out  # noqa: E402
import validate_refuter as v_ref  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
REQUIRED_DIRS = ["scripts", "tests", "tests/fixtures", "schemas", "outputs", "analyses", "visuals/specs"]

# Deliberately avoids the token "PASS" — a Tier-0 notice must never read as a verification result (F4).
CONVERSATIONAL_NOTICE = [
    "============================================================",
    "NOTICE — Tier 0 (conversational) is UNVERIFIED BY DESIGN.",
    "No gate runs here. Tier-0 honesty is a discipline, not a",
    "checked invariant (Constitution §15.8). Exit 0 means 'no gate",
    "applies here' — it is NOT a verification result.",
    "See docs/CONVERSATION.md for the labeling contract.",
    "============================================================",
]

UNAVAILABLE: dict[str, str] = {}

# A draft banner must never read as a verification result — deliberately avoids the token "PASS".
DRAFT_BANNER = [
    "============================================================",
    "DRAFT — STRUCTURAL + REVIEWABLE, NOT TRUE.",
    "Checks records integrity + manifest/context coherence + hash",
    "consistency. Does NOT run the refuter; NOT a committed answer.",
    "Exit 0 means 'structure coheres', never 'the answer is true'.",
    "============================================================",
]
# An answer is a VERIFIED PRIVATE answer (refuter-checked), never a publication or truth certificate.
ANSWER_BANNER = [
    "============================================================",
    "ANSWER — VERIFIED PRIVATE answer (refuter-bound), NOT TRUE.",
    "Composes records + manifest + context + output binding +",
    "the required refuter + input lifecycle + visuals. There is no",
    "'release': exit 0 = 'the recorded chain is coherent and",
    "contested', never 'the answer is true' or 'publishable'.",
    "============================================================",
]
# Answer-layer registries draft/answer resolve (beyond the factbase records gates).
ANSWER_LAYER_FILES = ["context_packs.yaml", "analyses.yaml", "refuters.yaml", "visuals.yaml"]


def scaffold_check(root: Path):
    lines: list[str] = []
    code = 0
    # 1. required governing documents + adjudication READY (reuse the WP0.0 gate)
    adj = root / "docs" / "REVIEW_ADJUDICATION.md"
    try:
        c, errs, _infos = cra.check_text(adj.read_text(encoding="utf-8"), root=root, check_files=True)
    except OSError as e:
        c, errs = 2, [(2, f"cannot read {adj}: {e}")]
    if c != 0:
        code = max(code, c)
        lines += [f"  [adjudication] {m}" for _s, m in sorted(errs)]
    else:
        lines.append("  · adjudication READY + required governing documents present")
    # 2. runtime directories
    missing = [d for d in REQUIRED_DIRS if not (root / d).is_dir()]
    if missing:
        code = max(code, 2)
        lines += [f"  [scaffold] missing runtime directory: {d}" for d in sorted(missing)]
    else:
        lines.append(f"  · runtime directories present: {len(REQUIRED_DIRS)}/{len(REQUIRED_DIRS)}")
    # 3. dependency availability (fail closed if a required package is missing)
    try:
        import yaml  # noqa: F401
        lines.append("  · dependency PyYAML importable")
    except ImportError:
        code = max(code, 2)
        lines.append("  [scaffold] PyYAML not importable — run .venv/bin/pip install -r requirements-dev.txt")
    return code, lines


def _count_claims(claims_paths):
    """Return (total_claims, parse_error). A MISSING claims file contributes 0 (an absent baseline/
    live file is 'no claims', i.e. empty); a PRESENT-but-unparseable file is a cannot-run condition
    reported distinctly (so a corrupt factbase isn't mislabeled 'empty')."""
    n = 0
    for cp in claims_paths:
        if not cp.exists():
            continue
        try:
            d = vs.load_yaml_strict(cp) or {}
            n += len(d.get("claims") or [])
        except Exception as e:  # noqa: BLE001
            return None, f"cannot parse {cp.name} ({e})"
    return n, None


def records_check(root: Path, as_of):
    """Compose the Phase-2 integrity gates over the factbase under <root> in dependency order
    (WP2.x). Fail-closed: an empty factbase (zero claims — the DAG spine) → exit 2 (R3 'a production
    gate must fail closed when it expected records and found none'); the FIRST gate returning 2
    short-circuits and PROPAGATES as records=2 (never masked by a downstream 0/1). All gates run over
    explicit paths under <root>/factbase. The cross-commit reward-hack tripwire (WP2.2c) is NOT part
    of this per-snapshot composition. Returns (exit_code, lines)."""
    fb = root / "factbase"
    sources, assessments = fb / "sources.yaml", fb / "source_assessments.yaml"
    evidence, cea = fb / "evidence.yaml", fb / "claim_evidence.yaml"
    claims = [fb / "baseline" / "claims.yaml", fb / "live" / "claims.yaml"]
    predictions, observations = fb / "predictions.yaml", fb / "observations.yaml"

    n_claims, parse_err = _count_claims(claims)
    if parse_err is not None:
        return 2, [f"  [records] {parse_err} — cannot run (fail closed, §13)."]
    if n_claims == 0:
        return 2, ["  [records] empty factbase — zero claims to compose (fail closed, R3: expected "
                   "records and found none)."]
    try:  # resolution sets for the cross-file gates (a bad registry here is §13 cannot-run)
        src_ids, grp_ids = v_evd.load_source_ids(sources)
        cea_refs = v_cea.load_ref_sets(claims, evidence, sources)
        # claim + cea id sets so the observation gate can resolve its backing leg (R3-P1-2)
        obs_claim_ids = cea_refs[0]
        obs_cea_ids = {a.get("id") for a in (vs.load_yaml_strict(cea) or {}).get(
            "claim_evidence_assessments") or [] if isinstance(a, dict)}
    except Exception as e:  # noqa: BLE001
        return 2, [f"  [records] cannot load a registry for resolution (fail closed): {e}"]
    triggers = v_hi.trigger_set()

    def _hi():
        code, finds = 0, []
        for cp in claims:
            c, f, _notices = v_hi.validate_high_impact_file(cp, triggers)  # 3-tuple; notices unscored
            code = max(code, c); finds += f
        return code, finds

    # DAG order; the cross-file ordering constraints (claim_evidence before support/conflict;
    # claims R-CLM-9/10 before freshness) hold by sequence + short-circuit-on-2.
    stages = [
        ("sources", lambda: v_src.validate_sources_file(sources)),
        ("source_assessments", lambda: v_gov.validate_governance_file(assessments)),
        ("evidence", lambda: v_evd.validate_evidence_file(evidence, src_ids, grp_ids)),
        ("claim_evidence", lambda: v_cea.validate_claim_evidence_file(cea, cea_refs)),
        ("high_impact", _hi),
        ("claims", lambda: v_clm.validate_claims(claims, cea, predictions)),
        ("support", lambda: v_sup.validate_support(claims, cea)),
        ("conflict", lambda: v_con.validate_conflict(claims, cea)),
        ("freshness", lambda: v_fresh.validate_freshness(claims, as_of)),
        ("observations", lambda: v_obs.validate_observations([observations], obs_claim_ids, obs_cea_ids)),
    ]
    code, lines = 0, [f"  [records] composing {len(stages)} integrity gates as of {as_of!r} "
                      f"(DAG order; cross-commit reward-hack is a separate gate)."]
    for name, fn in stages:
        c, findings = fn()
        lines += [f"  [{name}] {ln}" for ln in findings]
        if c == 2:  # cannot-run upstream → propagate, do not run downstream on a broken layer
            lines.append(f"  [records] gate {name!r} cannot run (exit 2) — composition halted, fail closed.")
            return 2, lines
        code = max(code, c)
    if code == 0:
        lines.append(f"  [records] all {len(stages)} gates composed clean.")
    return code, lines


def _answer_layer_schema(root: Path, scope: str):
    """Schema-validate any present answer-layer registries (context_packs/analyses/refuters/visuals)
    before resolving them. Returns (code, lines); code 2 = a registry cannot parse (fail closed)."""
    fb = root / "factbase"
    code, lines = 0, []
    for name in ANSWER_LAYER_FILES:
        p = fb / name
        if not p.exists():
            continue
        c, ff = vs.validate_file(p)
        if c == 2:
            return 2, [f"  [{scope}] {name}: cannot parse — fail closed."] + \
                [f"  [{scope}] {x}" for x in ff]
        if c == 1:
            code = max(code, 1)
            lines += [f"  [{scope} schema] {x}" for x in ff]
    return code, lines


def _draft_compose(root: Path, analysis_id, as_of):
    """The structural composition shared by draft + answer (no banner): records (whole-factbase
    integrity, incl. projection→prediction links) + the analysis manifest's structural integrity +
    its context pack (when one is referenced), scoped to the selected analysis. Fail-closed: records
    empty/upstream-2 propagates; a REQUIRED control that cannot run (selected analysis or its
    referenced pack missing) is exit 2. Returns (code, lines)."""
    lines = []
    code, rlines = records_check(root, as_of)
    lines += rlines
    if code == 2:
        lines.append("  [compose] records cannot run (exit 2) — halt, fail closed.")
        return 2, lines
    sc, slines = _answer_layer_schema(root, "compose")
    lines += slines
    if sc == 2:
        lines.append("  [compose] an answer-layer registry cannot parse — fail closed.")
        return 2, lines
    code = max(code, sc)
    live = al.Live(root)
    if analysis_id is None:
        lines.append("  [skip] manifest_structural / context_pack: no --analysis selected "
                     "(not required for a whole-factbase draft; a SKIP never counts as clean).")
        return code, lines
    ana = live.analyses.get(analysis_id)
    if ana is None:
        lines.append(f"  [compose] analysis {analysis_id!r} not found — a required control cannot "
                     f"run (exit 2, fail closed).")
        return 2, lines
    mc, mf = v_man.validate_manifest_structural(ana, live)
    code = max(code, mc)
    lines += [f"  [manifest] {x}" for x in mf]
    cpid = ana.get("context_pack_id")
    pack = live.context_packs.get(cpid) if cpid else None
    if cpid and pack is None:
        lines.append(f"  [compose] analysis references context pack {cpid!r} but it does not "
                     f"resolve — a required control cannot run (exit 2, fail closed).")
        return 2, lines
    if pack is not None:
        cc, cf = v_ctx.validate_context_pack(pack, live, ana.get("context_pack_hash"))
        code = max(code, cc)
        lines += [f"  [context_pack] {x}" for x in cf]
    else:
        lines.append("  [skip] context_pack: analysis references no context pack.")
    return code, lines


def draft_check(root: Path, analysis_id, as_of):
    """`draft` = the structural composition + the STRUCTURAL-NOT-TRUE banner."""
    code, lines = _draft_compose(root, analysis_id, as_of)
    if code == 0:
        lines.append("  [draft] structural composition clean (records + manifest + context). "
                     "Coherent bookkeeping, NOT a truth result.")
    return code, list(DRAFT_BANNER) + lines


def _answer_input_lifecycle(ana: dict, live: al.Live):
    """A committed answer may not lean on a stale/superseded/rejected/unreviewed input (§9). Checks
    EVERY claim the answer rests on — prose markers AND the frozen context pack's claim_refs AND each
    referenced visual's input_claim_refs (a withdrawn claim can feed the answer through any of them);
    plus the assessments cited by the manifest and the pack."""
    f = []
    markers = ana.get("claim_markers") if isinstance(ana.get("claim_markers"), dict) else {}
    claim_ids = {mv.get("claim_id") for mv in markers.values() if isinstance(mv, dict)}
    cea_ids = {r.get("id") for r in (ana.get("claim_evidence_assessment_refs") or []) if isinstance(r, dict)}
    pack = live.context_packs.get(ana.get("context_pack_id"))
    if isinstance(pack, dict):
        claim_ids |= {r.get("id") for r in (pack.get("claim_refs") or []) if isinstance(r, dict)}
        cea_ids |= {r.get("id") for r in (pack.get("assessment_refs") or []) if isinstance(r, dict)}
    for vref in ana.get("visual_refs") or []:
        v = live.visuals.get(vref.get("id")) if isinstance(vref, dict) else None
        if isinstance(v, dict):
            claim_ids |= {r.get("id") for r in (v.get("input_claim_refs") or []) if isinstance(r, dict)}
    for cid in sorted(c for c in claim_ids if c):
        c = live.claims.get(cid)
        if c is None:
            continue
        if c.get("lifecycle") in {"SUPERSEDED", "REJECTED", "CANDIDATE"}:
            f.append(f"claim {cid!r} lifecycle {c.get('lifecycle')!r} — a committed answer needs "
                     f"REVIEWED inputs (not superseded/rejected/unreviewed)")
        if c.get("freshness_status") in {"STALE", "REVIEW_DUE"}:
            f.append(f"claim {cid!r} is {c.get('freshness_status')} — refresh or supersede before committing")
    for aid in sorted(a for a in cea_ids if a):
        a = live.cea.get(aid)
        sr = a.get("semantic_review") if isinstance(a, dict) else None
        if isinstance(sr, dict) and sr.get("status") == "REJECTED":
            f.append(f"assessment {aid!r} semantic_review REJECTED — cannot back a committed answer")
    return (1 if f else 0), sorted(f)


def _answer_visuals(ana: dict, live: al.Live):
    """Referenced visuals: spec + spec_hash are validated by manifest_structural; render/inspection
    is a WP5 control, so a `renderer_version: planned` visual is an ALLOWED skip (never PASS)."""
    lines = []
    for ref in ana.get("visual_refs") or []:
        v = live.visuals.get(ref.get("id")) if isinstance(ref, dict) else None
        if v is None:
            continue  # resolution is manifest_structural's job
        if v.get("renderer_version") == "planned":
            lines.append(f"  [skip] visual {ref.get('id')!r}: render/inspect not landed (WP5) — "
                         f"spec + spec_hash validated upstream, render SKIPPED (a skip is not clean).")
    return 0, lines


def _gate_computed_refuter_scope(ana: dict, live: al.Live):
    """Return (required_claims, required_ceas, floor) COMPUTED from the real factbase — not read from
    the author-shrinkable manifest. A committed answer commits to its prose markers AND its visual
    input claims (a chart asserts them too, R3-P0-4), so required_claims = both. required_ceas =
    manifest refs ∪ context-pack assessment_refs ∪ each referenced visual's
    input_claim_evidence_assessment_refs ∪ the active CHECKED assessments of EVERY stance
    (SUPPORTS ∪ REFUTES ∪ MIXED) for every required FACT/INFERENCE claim — an opposing assessment
    that makes a claim CONTESTED must be reviewed too (R3-P0-1), not just its support. floor: a
    factual required claim must HAVE at least one active CHECKED SUPPORTS assessment."""
    markers = ana.get("claim_markers") if isinstance(ana.get("claim_markers"), dict) else {}
    marked = {mv.get("claim_id") for mv in markers.values() if isinstance(mv, dict)}
    visual_claims = set()
    required = {r.get("id") for r in (ana.get("claim_evidence_assessment_refs") or []) if isinstance(r, dict)}
    pack = live.context_packs.get(ana.get("context_pack_id"))
    if isinstance(pack, dict):
        required |= {r.get("id") for r in (pack.get("assessment_refs") or []) if isinstance(r, dict)}
    for vref in ana.get("visual_refs") or []:
        v = live.visuals.get(vref.get("id")) if isinstance(vref, dict) else None
        if isinstance(v, dict):
            visual_claims |= {r.get("id") for r in (v.get("input_claim_refs") or []) if isinstance(r, dict)}
            required |= {r.get("id") for r in (v.get("input_claim_evidence_assessment_refs") or [])
                         if isinstance(r, dict)}
    required_claims = {c for c in (marked | visual_claims) if c}
    active = v_sup.active_checked_by_claim(list(live.cea.values()))      # every stance (R3-P0-1)
    supports = v_sup.active_supports_by_claim(list(live.cea.values()))   # SUPPORTS only (the floor)
    floor = []
    for cid in sorted(required_claims):
        claim = live.claims.get(cid)
        if not isinstance(claim, dict) or claim.get("epistemic_type") not in {"FACT", "INFERENCE"}:
            continue  # ASSUMPTION/PROJECTION claims carry no evidence
        required |= {a.get("id") for a in (active.get(cid) or []) if isinstance(a, dict)}
        # §6.6 / CONFLICT-1: the support must be credibility-SCORED (1..6), not merely exist. An
        # UNASSESSED support is invisible to the conflict recompute (compute_dispute filters both
        # sides by credibility), so it can hide a real opposing assessment and ship the claim as
        # settled. Requiring a scored support forces the contest into the open (or fails here).
        scored = [a for a in (supports.get(cid) or [])
                  if isinstance(a.get("information_credibility"), int)
                  and not isinstance(a.get("information_credibility"), bool)
                  and 1 <= a["information_credibility"] <= 6]
        if not scored:
            floor.append(f"required {claim.get('epistemic_type')} claim {cid!r} (prose marker or "
                         f"visual input) has no credibility-SCORED active CHECKED SUPPORTS assessment "
                         f"— a committed answer (Tier 2, §6.6) requires a scored support; an unscored "
                         f"support can hide a real conflict (CONFLICT-1)")
    required.discard(None)
    return required_claims, required, floor


def answer_check(root: Path, analysis_id, as_of):
    """`answer` = draft composition + output-text binding (A7 semantic half BLOCKS) + the required
    refuter + input-lifecycle reject + visuals. --analysis is REQUIRED; a missing refuter is a
    cannot-run §10 control (exit 2). There is no 'release': a verified PRIVATE answer, not truth."""
    if analysis_id is None:
        return 2, list(ANSWER_BANNER) + ["  [answer] --analysis is required (a committed answer "
                                         "names its analysis) — fail closed."]
    code, body = _draft_compose(root, analysis_id, as_of)
    lines = list(ANSWER_BANNER) + body
    if code == 2:
        lines.append("  [answer] structural composition cannot run (exit 2) — answer halts, fail closed.")
        return 2, lines
    live = al.Live(root)
    ana = live.analyses.get(analysis_id)
    if ana is None:
        return 2, lines + [f"  [answer] analysis {analysis_id!r} not found — fail closed."]
    # A committed answer requires the analysis to be in the ANSWER lifecycle (cross-vendor review
    # P1-1): a DRAFT analysis is a work-in-progress, not a committed answer.
    if ana.get("lifecycle") != "ANSWER":
        code = max(code, 1)
        lines.append(f"  [answer] analysis lifecycle is {ana.get('lifecycle')!r} — committed-answer "
                     f"mode requires lifecycle ANSWER (a DRAFT analysis is not a committed answer).")
    # A committed answer must COMMIT to at least one claim. Empty claim_markers is a degenerate
    # "answer that cites nothing" — it would make the refuter's set-equality vacuously satisfied and
    # switch off the independence floor (Milestone-A P0 review). Reject it.
    if not (isinstance(ana.get("claim_markers"), dict) and ana["claim_markers"]):
        code = max(code, 1)
        lines.append("  [answer] a committed answer must cite at least one claim — claim_markers is "
                     "empty (a refuter would then review nothing). Mark the load-bearing claims.")
    oc, of = v_out.validate_output(ana, live, root, block_unmarked=True)
    lines += [f"  [output] {x}" for x in of]
    if oc == 2:
        lines.append("  [answer] output binding cannot run (exit 2) — fail closed.")
        return 2, lines
    code = max(code, oc)
    refuter = live.refuter_for_analysis(analysis_id)
    if refuter is None:
        lines.append(f"  [answer] no refuter binds analysis {analysis_id!r} — the §10 refuter control "
                     f"cannot run (exit 2, fail closed). SKIP is not PASS.")
        return 2, lines
    # R3-P0-3: there is no refuter supersession model, so MORE THAN ONE refuter binding the same
    # (analysis, manifest_hash, output_hash) is ambiguous — refuter_for_analysis picks the first,
    # which would let a cherry-picked SURVIVES hide a REJECT sibling. Fail closed.
    bound = sorted(r.get("id") for r in live.refuters.values()
                   if isinstance(r, dict) and r.get("analysis_id") == analysis_id
                   and r.get("manifest_hash") == ana.get("manifest_hash")
                   and r.get("output_hash") == ana.get("output_hash"))
    if len(bound) > 1:
        lines.append(f"  [answer] {len(bound)} refuters bind analysis {analysis_id!r} at the same "
                     f"manifest/output hash ({bound}) — a committed answer requires exactly one "
                     f"(no supersession model); a negative sibling cannot be cherry-picked away. "
                     f"Fail closed. [R3-P0-3]")
        return 2, lines
    # R2-P0-1 / R3-P0-1 / R3-P0-4: gate-compute the refuter's required claim + assessment scope from
    # the factbase (the author cannot shrink it via the manifest), including opposing assessments and
    # visual input claims, and enforce the support floor for factual required claims.
    required_claims, required_ceas, floor = _gate_computed_refuter_scope(ana, live)
    if floor:
        code = max(code, 1)
        lines += [f"  [refuter] {x}" for x in floor]
    rc, rf = v_ref.validate_refuter(refuter, ana, live, answer_mode=True,
                                    required_ceas=required_ceas, required_claims=required_claims)
    code = max(code, rc)
    lines += [f"  [refuter] {x}" for x in rf]
    lc, lf = _answer_input_lifecycle(ana, live)
    code = max(code, lc)
    lines += [f"  [inputs] {x}" for x in lf]
    _vc, vlines = _answer_visuals(ana, live)
    lines += vlines
    if code == 0:
        lines.append("  [answer] committed answer composes: records + manifest + context + output "
                     "binding + refuter + input lifecycle + visuals. A VERIFIED PRIVATE answer — "
                     "coherent + contested bookkeeping, NOT a truth or publication claim.")
    return code, lines


def run_mode(mode, root: Path, as_of=None, analysis_id=None):
    """Return (exit_code, output_lines) for a mode. None defaults to scaffold."""
    if mode is None:
        mode = "scaffold"
    if mode == "conversational":
        return 0, list(CONVERSATIONAL_NOTICE)
    if mode == "scaffold":
        return scaffold_check(root)
    if mode == "records":
        return records_check(root, as_of)
    if mode == "draft":
        return draft_check(root, analysis_id, as_of)
    if mode == "answer":
        return answer_check(root, analysis_id, as_of)
    if mode in UNAVAILABLE:
        return 2, [f"  mode '{mode}' is unavailable until {UNAVAILABLE[mode]} lands "
                   f"(fail closed — an inactive control is exit 2, never a silent pass)."]
    return 2, [f"  unknown mode '{mode}'. Valid modes: conversational, scaffold, records, draft, answer."]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Analyst Harness v3 unified verifier")
    p.add_argument("--mode", default="scaffold")  # no choices: unknown modes fail closed in run_mode
    p.add_argument("--root", type=Path, default=REPO_ROOT)
    p.add_argument("--as-of", default=None, help="injectable clock for records/draft (freshness)")
    p.add_argument("--analysis", default=None, help="analysis id to draft/answer (e.g. ana-skeleton)")
    args = p.parse_args(argv)
    code, lines = run_mode(args.mode, args.root, args.as_of, args.analysis)
    for ln in lines:
        print(ln)
    if code == 0 and args.mode not in ("conversational",):
        print("OK — checks clean. (Coherent bookkeeping, NOT a truth certificate.)")
    return code


if __name__ == "__main__":
    sys.exit(main())

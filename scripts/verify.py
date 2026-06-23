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

UNAVAILABLE = {
    "draft": "Phase 3 (WP3.1)",
    "answer": "Phase 3 (WP3.4)",
}


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
        ("observations", lambda: v_obs.validate_observations([observations])),
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


def run_mode(mode, root: Path, as_of=None):
    """Return (exit_code, output_lines) for a mode. None defaults to scaffold."""
    if mode is None:
        mode = "scaffold"
    if mode == "conversational":
        return 0, list(CONVERSATIONAL_NOTICE)
    if mode == "scaffold":
        return scaffold_check(root)
    if mode == "records":
        return records_check(root, as_of)
    if mode in UNAVAILABLE:
        return 2, [f"  mode '{mode}' is unavailable until {UNAVAILABLE[mode]} lands "
                   f"(fail closed — an inactive control is exit 2, never a silent pass)."]
    return 2, [f"  unknown mode '{mode}'. Valid modes: conversational, scaffold, records, draft, answer."]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Analyst Harness v3 unified verifier")
    p.add_argument("--mode", default="scaffold")  # no choices: unknown modes fail closed in run_mode
    p.add_argument("--root", type=Path, default=REPO_ROOT)
    p.add_argument("--as-of", default=None, help="injectable clock for --mode records (freshness)")
    args = p.parse_args(argv)
    code, lines = run_mode(args.mode, args.root, args.as_of)
    for ln in lines:
        print(ln)
    if code == 0 and args.mode not in ("conversational",):
        print("OK — checks clean. (Coherent bookkeeping, NOT a truth certificate.)")
    return code


if __name__ == "__main__":
    sys.exit(main())

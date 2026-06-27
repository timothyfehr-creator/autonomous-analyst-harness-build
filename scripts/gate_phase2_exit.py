#!/usr/bin/env python3
"""Phase-2 EXIT auto-gate — the machine check at the integrity-gates boundary (Phase 2 → Phase 3).

Witnesses (fail-closed; exit 0 = clear, 2 = a witness failed → halt; never exit 1, mirroring
gate_phase1_exit):
  W-RECORDS-EMPTY    `records` fails closed on the real (empty-of-claims) factbase → exit 2 (R3).
  W-RECORDS-COMPOSE  the Milestone-A skeleton, staged into a factbase tree, composes through all
                     integrity gates → records exit 0 (the valid-set green path).
  W-A-EXPLOITS       the R4 STANDING INVARIANTS — each named cold-review exploit still fires (exit 1)
                     against its gate: A1 (first-party + one wire ≠ CORROBORATED), two-credibility-6,
                     high_impact-recompute (V-P0-1), A5 (cross-dimensional-class recast, V-P1-5),
                     and same-origin-both-sides conflict suppression. A later WP cannot silently
                     regress these.
  W-PHASE1-GREEN     the Phase-1 exit gate still passes (cumulative-drift tripwire).

Complements the pytest suite (run both at the boundary: `pytest -q && python scripts/gate_phase2_exit.py`).
Invokes gates in-process (no subprocess, no pytest dependency).
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling import
import gate_phase1_exit  # noqa: E402
import validate_conflict as v_con  # noqa: E402
import validate_high_impact as v_hi  # noqa: E402
import validate_observations as v_obs  # noqa: E402
import validate_support as v_sup  # noqa: E402
import verify  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
FIX = REPO / "tests" / "fixtures"
SK = FIX / "skeleton"
ASOF = "2026-06-23T00:00:00Z"  # a fixed pin — the gate must not depend on wall-clock


def stage_skeleton(root: Path) -> Path:
    """Materialize the flat Milestone-A skeleton into a <root>/factbase tree (baseline+live split)."""
    fb = root / "factbase"
    (fb / "baseline").mkdir(parents=True)
    (fb / "live").mkdir(parents=True)
    for src, dst in [("skeleton_sources.yaml", "sources.yaml"),
                     ("skeleton_source_assessments.yaml", "source_assessments.yaml"),
                     ("skeleton_evidence.yaml", "evidence.yaml"),
                     ("skeleton_claim_evidence.yaml", "claim_evidence.yaml"),
                     ("skeleton_claims.yaml", "baseline/claims.yaml"),
                     ("skeleton_predictions.yaml", "predictions.yaml"),
                     ("skeleton_observations.yaml", "observations.yaml"),
                     ("skeleton_geography.yaml", "geography.yaml")]:
        shutil.copy(SK / src, fb / dst)
    (fb / "live" / "claims.yaml").write_text('schema_version: "2.0"\nclaims: []\n')
    return fb


def _records_empty() -> str | None:
    code, _ = verify.records_check(REPO, ASOF)
    return None if code == 2 else f"records on the empty real factbase returned {code}, expected 2"


def _records_compose() -> str | None:
    tmp = Path(tempfile.mkdtemp())
    try:
        stage_skeleton(tmp)
        code, lines = verify.records_check(tmp, ASOF)
        return None if code == 0 else f"records did not compose the skeleton (exit {code}): {lines[-3:]}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _a_exploits() -> str | None:
    """Each named exploit must still be REJECTED (exit 1) by its gate — the R4 standing invariants."""
    checks = {
        "A1 (first-party + one wire)":
            lambda: v_sup.validate_support([FIX / "support_a1_claims.yaml"], FIX / "support_a1_cea.yaml")[0],
        "two-credibility-6":
            lambda: v_sup.validate_support([FIX / "support_twocred6_claims.yaml"], FIX / "support_twocred6_cea.yaml")[0],
        "high_impact-recompute (V-P0-1)":
            lambda: v_hi.validate_high_impact_file(FIX / "hi_t1_casualties_false.yaml", v_hi.trigger_set())[0],
        "high_impact-text-laundering (P0-2)":
            lambda: v_hi.validate_high_impact_file(FIX / "hi_text_evasion.yaml", v_hi.trigger_set())[0],
        "A5 cross-class recast (V-P1-5)":
            lambda: v_obs.validate_observations([FIX / "obs_a5_cross_class_no_df.yaml"])[0],
        "conflict same-origin-both-sides":
            lambda: v_con.validate_conflict([FIX / "conflict_same_origin_both_sides_claims.yaml"],
                                            FIX / "conflict_same_origin_both_sides_cea.yaml")[0],
        "wire-echo (shared deeper origin)":
            lambda: v_sup.validate_support([FIX / "support_wire_echo_claims.yaml"],
                                           FIX / "support_wire_echo_cea.yaml")[0],
        "shared-independence-group":
            lambda: v_sup.validate_support([FIX / "support_shared_group_claims.yaml"],
                                           FIX / "support_shared_group_cea.yaml")[0],
        "conflict deep-shared-origin":
            lambda: v_con.validate_conflict([FIX / "conflict_deep_shared_origin_claims.yaml"],
                                            FIX / "conflict_deep_shared_origin_cea.yaml")[0],
    }
    bad = [f"{name}: exit {code} (expected 1 — STANDING INVARIANT REGRESSED)"
           for name, fn in checks.items() if (code := fn()) != 1]
    return "; ".join(bad) if bad else None


def _phase1_green() -> str | None:
    return None if gate_phase1_exit.main() == 0 else "Phase-1 exit gate is no longer green (cumulative drift)"


def main() -> int:
    witnesses = [("W-RECORDS-EMPTY", _records_empty), ("W-RECORDS-COMPOSE", _records_compose),
                 ("W-A-EXPLOITS", _a_exploits), ("W-PHASE1-GREEN", _phase1_green)]
    problems = []
    for name, fn in witnesses:
        msg = fn()
        if msg:
            problems.append(f"{name}: {msg}")
    if problems:
        print("PHASE-2 EXIT GATE: FAIL (halt — fail closed)", file=sys.stderr)
        for p in problems:
            print(f"  [gate] {p}", file=sys.stderr)
        return 2
    print("PHASE-2 EXIT GATE: PASS — records composes the Milestone-A skeleton, fails closed on an "
          "empty factbase, the A1/two-cred-6/high_impact/A5/conflict standing invariants all fire, "
          "and the Phase-1 gate is green. Cleared to enter Phase 3.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

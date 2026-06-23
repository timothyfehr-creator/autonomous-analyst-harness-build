#!/usr/bin/env python3
"""Phase-1 EXIT auto-gate — the machine check at the schema-freeze boundary (Phase 1 → Phase 2).

Three independent witnesses, fail-closed:
  R1  the frozen canonicalization golden vector still holds (a SECOND copy, independent of the
      pytest copy — if hashing drifts, at least one witness turns red);
  R5  the Milestone-A synthetic skeleton composes through every Phase-1 schema (exit 0 each);
  seeds  the real (empty) factbase registries are schema-clean.

Exit 0 = gate clear, continue to Phase 2 · 2 = a witness failed, halt (fail closed).
This complements the pytest conformance suite (R2); it does not replace it. Run both at the
boundary: `pytest -q && python scripts/gate_phase1_exit.py`.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_schema as vs  # noqa: E402

REPO = Path(__file__).resolve().parent.parent

# R1 — frozen golden vector (independent second copy; FROZEN, must never change). Mirrors
# tests/test_schema_core.py::GOLDEN so a drift in canonicalize() is caught here too.
GOLDEN = [
    ({"b": 1, "a": 2}, (), '{"a":2,"b":1}'),
    ({"id": "x", "computed": 9, "n": {"z": 1, "y": 2}}, ("computed",), '{"id":"x","n":{"y":2,"z":1}}'),
    ({"a": None, "b": 1}, (), '{"a":null,"b":1}'),
    ({"items": [3, 1, 2]}, (), '{"items":[3,1,2]}'),
    ({"t": True, "f": False}, (), '{"f":false,"t":true}'),
]

SKELETON_DIR = REPO / "tests" / "fixtures" / "skeleton"
FACTBASE_SEEDS = [
    "sources.yaml", "source_assessments.yaml", "evidence.yaml", "claim_evidence.yaml",
    "observations.yaml", "geography.yaml", "predictions.yaml", "prediction_events.jsonl",
    "baseline_events.jsonl", "baseline/claims.yaml", "live/claims.yaml",
]


def _check_golden() -> list[str]:
    bad = []
    for obj, exclude, expected in GOLDEN:
        got = vs.canonicalize(obj, exclude)
        if got != expected:
            bad.append(f"R1 canonicalize drift: {obj!r} exclude={exclude} -> {got!r} (want {expected!r})")
        want_h = "sha256:" + hashlib.sha256(expected.encode("utf-8")).hexdigest()
        if vs.record_hash(obj, exclude) != want_h:
            bad.append(f"R1 record_hash drift for {obj!r}")
    return bad


def _check_paths(paths, label) -> list[str]:
    bad = []
    for p in paths:
        if not p.exists():
            bad.append(f"{label}: missing {p.name}")
            continue
        code, findings = vs.validate_file(p)
        if code != 0:
            bad.append(f"{label}: {p.name} did not validate clean (exit {code}): {findings[:2]}")
    return bad


def main() -> int:
    problems = []
    problems += _check_golden()
    skeleton = sorted(SKELETON_DIR.glob("*.yaml")) + sorted(SKELETON_DIR.glob("*.jsonl"))
    if not skeleton:
        problems.append("R5: no Milestone-A skeleton files found")
    problems += _check_paths(skeleton, "R5 skeleton")
    problems += _check_paths([REPO / "factbase" / s for s in FACTBASE_SEEDS], "seed")

    if problems:
        print("PHASE-1 EXIT GATE: FAIL (halt — fail closed)", file=sys.stderr)
        for p in problems:
            print(f"  [gate] {p}", file=sys.stderr)
        return 2
    print("PHASE-1 EXIT GATE: PASS — golden vector intact, Milestone-A skeleton composes through "
          "every Phase-1 schema, factbase seeds clean. Cleared to enter Phase 2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

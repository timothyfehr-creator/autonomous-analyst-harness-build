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
    "records": "Phase 2 (WP2.x records composition)",
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


def run_mode(mode, root: Path):
    """Return (exit_code, output_lines) for a mode. None defaults to scaffold."""
    if mode is None:
        mode = "scaffold"
    if mode == "conversational":
        return 0, list(CONVERSATIONAL_NOTICE)
    if mode == "scaffold":
        return scaffold_check(root)
    if mode in UNAVAILABLE:
        return 2, [f"  mode '{mode}' is unavailable until {UNAVAILABLE[mode]} lands "
                   f"(fail closed — an inactive control is exit 2, never a silent pass)."]
    return 2, [f"  unknown mode '{mode}'. Valid modes: conversational, scaffold, records, draft, answer."]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Analyst Harness v3 unified verifier")
    p.add_argument("--mode", default="scaffold")  # no choices: unknown modes fail closed in run_mode
    p.add_argument("--root", type=Path, default=REPO_ROOT)
    args = p.parse_args(argv)
    code, lines = run_mode(args.mode, args.root)
    for ln in lines:
        print(ln)
    if code == 0 and args.mode not in ("conversational",):
        print("OK — scaffold checks clean. (Coherent bookkeeping, NOT a truth certificate.)")
    return code


if __name__ == "__main__":
    sys.exit(main())

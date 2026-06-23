#!/usr/bin/env python3
"""Phase-1 gate pre-flight — machine guard that blocks Segment 2 (any WP1.x) until the gate is
cleared. Per `docs/REVIEW_ADJUDICATION.md`'s binding condition, Phase 1 may not start until:

  1. the four doc-fixes are present in the governing docs (CONSTITUTION + DATA_MODEL), detected
     by each fix's anchor token (see docs/PHASE1_DOC_FIXES_DRAFT.md); AND
  2. an independent cross-vendor/human review is logged — `independent_review_complete: true`
     in the adjudication frontmatter.

Fail closed: anything missing → exit 2 (do NOT start WP1.x). Cleared → exit 0.

The anchor token is an attestation that the human applied the corresponding fix; it is not a
proof of semantic correctness (that is the independent review's job).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent

# finding id -> anchor token that the applied doc-fix must introduce into a governing doc.
# These cover the four findings the adjudication's binding condition names (V-P0-1, V-P1-4,
# V-P1-5, V-P1-10) plus F3 (the adjacent §6.6 corroboration-bar fix) — strictly stricter.
REQUIRED_TOKENS = {
    "V-P0-1": "gate-computed high_impact",
    "V-P1-4": "primary_evidence_kind",
    "V-P1-5": "unit_vocabulary",
    "V-P1-10": "credibility floor",
    "F3": "caps support at SUPPORTED",
}
GOVERNING_DOCS = ("docs/CONSTITUTION.md", "docs/DATA_MODEL.md")


def _governing_text(root: Path) -> str:
    parts = []
    for rel in GOVERNING_DOCS:
        try:
            parts.append((root / rel).read_text(encoding="utf-8"))
        except OSError:
            pass  # missing governing doc -> token simply won't be found -> blocker
    return "\n".join(parts)


def _independent_review_done(root: Path) -> bool:
    try:
        text = (root / "docs" / "REVIEW_ADJUDICATION.md").read_text(encoding="utf-8")
    except OSError:
        return False
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return False
    try:
        fm = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return False
    return isinstance(fm, dict) and fm.get("independent_review_complete") is True


def _norm(s: str) -> str:
    # collapse all whitespace so a soft-wrapped anchor phrase still matches (markdown prose wraps)
    return re.sub(r"\s+", " ", s)


def preflight(root: Path):
    """Return (exit_code, blockers). 0 = gate cleared; 2 = blocked / fail closed."""
    blockers = []
    gov = _norm(_governing_text(root))
    for fid, token in REQUIRED_TOKENS.items():
        if _norm(token) not in gov:
            blockers.append(f"doc-fix {fid} not yet in governing docs (missing anchor: {token!r})")
    if not _independent_review_done(root):
        blockers.append("independent cross-vendor/human review not logged "
                        "(set independent_review_complete: true in docs/REVIEW_ADJUDICATION.md)")
    return (2 if blockers else 0), blockers


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Phase-1 gate pre-flight (blocks WP1.x until cleared)")
    p.add_argument("--root", type=Path, default=REPO_ROOT)
    args = p.parse_args(argv)
    code, blockers = preflight(args.root)
    if code == 0:
        print("Phase-1 GATE CLEARED — independent review logged and all four doc-fixes present. "
              "Segment 2 (WP1.x) may proceed.")
    else:
        print("Phase-1 GATE BLOCKED — do NOT start WP1.x. Outstanding:", file=sys.stderr)
        for b in blockers:
            print(f"  - {b}", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())

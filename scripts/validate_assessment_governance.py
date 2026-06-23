#!/usr/bin/env python3
"""WP2.2b — source-assessment append-only governance (STRUCTURAL, single-file).

Source assessments are append-only, scoped judgments; the current one is the active leaf of a
supersession chain (DATA_MODEL §2, §14: "In-place edits and deletions are prohibited once
committed; correction creates a superseding record"). This gate enforces the invariants checkable
within ONE committed file (the cross-COMMIT half — no in-place rating edit, no deletions, no
same-commit collusion — is the git-range gate, WP2.2c):

  - no self-supersede (a record cannot supersede itself — a self-loop is not a chain);
  - no orphan supersedes (every non-null supersedes resolves to a known sas- in the same log);
  - no supersession cycle (following supersedes must terminate at a null root);
  - exactly one ACTIVE leaf per chain (per connected supersedes component): the un-superseded
    record. Zero (a cycle) or two+ (a fork) is invalid (parallels §ce "one active leaf per chain");
  - required provenance present AND non-empty (the schema checks presence; this adds non-emptiness
    for the free-text fields the schema can't type: scope, rationale, sample_definition, assessed_by).

Out of scope (flagged): cross-chain de-dup over free-text `scope` (non-computable); `source_id`
resolution against the source registry (a consuming gate, WP2.3); `assessed_at` monotonicity (not
in the docs). Schema runs first; a malformed log fails at the schema layer unmasked.

Exit codes: 0 clean · 1 a governance violation · 2 cannot-run / fail closed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling import
import supersession  # noqa: E402
import validate_schema as vs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LOG = REPO_ROOT / "factbase" / "source_assessments.yaml"
_NONEMPTY_FIELDS = ("scope", "rationale", "sample_definition", "assessed_by")
_ZERO_WIDTH = "​‌‍⁠﻿"  # ZWSP/ZWNJ/ZWJ/word-joiner/BOM (str.strip leaves these)


def _is_blank(v) -> bool:
    """A provenance field is blank unless it is a string with real content. Catches null, non-string
    (list/int), empty, whitespace-only, AND zero-width-only (which str.strip does not remove)."""
    if not isinstance(v, str):
        return True
    return not v.strip().strip(_ZERO_WIDTH).strip()


def check_assessment_governance(data) -> list[str]:
    """Structural supersession + provenance findings for a schema-clean assessment log. The
    supersession-structural checks are the shared supersession.check_supersession (no partition —
    a chain is any connected component); provenance non-emptiness is assessment-specific."""
    recs = data.get("source_assessments", []) or []
    findings = supersession.check_supersession(recs, label="assessment")
    for r in recs:
        for fld in _NONEMPTY_FIELDS:
            if _is_blank(r.get(fld)):
                findings.append(f"assessment {r.get('id')!r} has an empty {fld}")
    return sorted(findings)


def validate_governance_file(path: Path):
    """Return (exit_code, findings). Schema first; integrity only on a schema-clean parse."""
    code, schema_findings = vs.validate_file(path)
    if code != 0:
        return code, schema_findings
    data = vs.load_yaml_strict(path)
    findings = check_assessment_governance(data)
    return (1 if findings else 0), [f"{path.name}: {f}" for f in findings]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP2.2b source-assessment governance gate")
    p.add_argument("paths", nargs="*", type=Path)
    args = p.parse_args(argv)
    paths = args.paths or [DEFAULT_LOG]
    code, all_findings = 0, []
    for path in paths:
        c, findings = validate_governance_file(path)
        code = max(code, c)
        all_findings += findings
    for f in sorted(all_findings):
        print(f"  [finding] {f}", file=sys.stderr)
    if code == 0:
        print("OK — assessment governance clean. (Structural append-only checks; NOT a truth certificate.)")
    return code


if __name__ == "__main__":
    sys.exit(main())

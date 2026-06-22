#!/usr/bin/env python3
"""WP0.0 — Review-adjudication gate.

Verifies that `docs/REVIEW_ADJUDICATION.md` records a *complete, coherent* adjudication before
any implementation work package may run, and that the governing documents it depends on exist.

A green result means the adjudication bookkeeping is coherent and governance is READY. It does
NOT mean the review was correct or the design is sound (see the review doc + Accepted
limitations). Fail closed: a check that cannot genuinely run exits 2.

Exit codes (fixed, per AGENTS.md):
  0  clean
  1  findings in otherwise-valid input (duplicate finding ID; disposition outside the enum)
  2  usage error / the gate could not genuinely run / governance is not READY
     (unreadable or unparseable file; missing frontmatter key; external_review_complete != true;
      open_p0_p1 != 0; governance_status != READY; a P0/P1 finding missing a required field;
      a BLOCKING disposition remains; a required governing document is absent)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

# The authoritative disposition enum lives in the gate, not in the file it checks — so the
# ledger cannot quietly widen its own allowed set. Mirror of docs/REVIEW_ADJUDICATION.md.
ALLOWED_DISPOSITIONS = {
    "RESOLVED_IN_DESIGN",
    "PLANNED_FIX",
    "ACCEPTED_WITH_LIMITS",
    "BLOCKING",
    "REJECTED_WITH_EVIDENCE",
}

# A markdown table data row is a "finding row" iff its first cell matches one of these IDs.
FINDING_ID_RE = re.compile(r"^(N\d+|F\d+|V-[A-Za-z0-9.\-]+)$")

# Governing documents WP0.0 confirms exist (repo-relative). Missing any → exit 2.
REQUIRED_FILES = [
    "docs/CONSTITUTION.md",
    "docs/CONVERSATION.md",
    "docs/DATA_MODEL.md",
    "docs/EXAMPLE_WORKFLOW.md",
    "docs/KNOWLEDGE.md",
    "docs/TOOLING.md",
    "docs/PROGRESS.md",
    "docs/REVIEW_PROMPT.md",
    "docs/RED_TEAM_BRIEF.md",
    "docs/REVIEW_ADJUDICATION.md",
    "IMPLEMENTATION_PLAN.md",
    "MERGE_NOTES.md",
    "AGENTS.md",
    "CLAUDE.md",
    "README.md",
    "skills/fact-repository/SKILL.md",
    "skills/visuals/SKILL.md",
    "factbase/README.md",
    "factbase/sources.yaml",
    "factbase/source_assessments.yaml",
    "factbase/evidence.yaml",
    "factbase/claim_evidence.yaml",
    "factbase/observations.yaml",
    "factbase/geography.yaml",
    "factbase/predictions.yaml",
    "factbase/baseline/claims.yaml",
    "factbase/live/claims.yaml",
    "factbase/baseline_events.jsonl",
    "factbase/prediction_events.jsonl",
]

REQUIRED_FRONTMATTER = ("external_review_complete", "open_p0_p1", "governance_status")


def parse_frontmatter(text: str):
    """Return the YAML frontmatter dict, or None if absent/unparseable."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return None
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def parse_findings(text: str):
    """Return a list of finding dicts parsed from every markdown table finding row."""
    findings = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if not cells or not FINDING_ID_RE.match(cells[0]):
            continue
        findings.append(
            {
                "id": cells[0],
                "severity": cells[1] if len(cells) > 1 else "",
                "disposition": cells[2] if len(cells) > 2 else "",
                "governing_change": cells[3] if len(cells) > 3 else "",
                "proof": cells[4] if len(cells) > 4 else "",
                "ncells": len(cells),
                "line": lineno,
            }
        )
    return findings


def check_text(text: str, root: Path | None = None, check_files: bool = True):
    """Core gate. Returns (exit_code, errors, infos). exit_code is the max severity seen."""
    errors: list[tuple[int, str]] = []  # (severity, message)
    infos: list[str] = []

    fm = parse_frontmatter(text)
    if fm is None:
        return 2, [(2, "frontmatter missing or unparseable")], infos

    for key in REQUIRED_FRONTMATTER:
        if key not in fm:
            errors.append((2, f"frontmatter missing required key: {key}"))
    if fm.get("external_review_complete") is not True:
        errors.append((2, "external_review_complete is not true — cold review incomplete"))
    if fm.get("open_p0_p1") != 0:
        errors.append((2, f"open_p0_p1 is {fm.get('open_p0_p1')!r}, must be 0"))
    if fm.get("governance_status") != "READY":
        errors.append((2, f"governance_status is {fm.get('governance_status')!r}, must be READY"))

    findings = parse_findings(text)
    if not findings:
        errors.append((2, "no finding rows found — adjudication ledger is empty"))

    seen: dict[str, int] = {}
    for f in findings:
        if f["id"] in seen:
            errors.append((1, f"duplicate finding ID {f['id']} (lines {seen[f['id']]}, {f['line']})"))
        seen[f["id"]] = f["line"]

        if f["disposition"] not in ALLOWED_DISPOSITIONS:
            errors.append((1, f"{f['id']}: disposition {f['disposition']!r} is not in the allowed enum"))
        if f["disposition"] == "BLOCKING":
            errors.append((2, f"{f['id']}: BLOCKING disposition remains — governance cannot be READY"))

        # Every P0/P1 finding must carry a governing change AND a proving test.
        if f["severity"] in ("P0", "P1"):
            if f["ncells"] < 5 or not f["governing_change"] or not f["proof"]:
                errors.append((2, f"{f['id']} ({f['severity']}): missing governing change and/or proving test"))

    infos.append(f"frontmatter: governance_status={fm.get('governance_status')}, "
                 f"open_p0_p1={fm.get('open_p0_p1')}, external_review_complete={fm.get('external_review_complete')}")
    infos.append(f"findings parsed: {len(findings)} "
                 f"(P0={sum(1 for f in findings if f['severity']=='P0')}, "
                 f"P1={sum(1 for f in findings if f['severity']=='P1')}, "
                 f"P2={sum(1 for f in findings if f['severity']=='P2')})")

    if check_files:
        base = root or Path.cwd()
        missing = [rel for rel in REQUIRED_FILES if not (base / rel).exists()]
        for rel in sorted(missing):
            errors.append((2, f"required governing document missing: {rel}"))
        infos.append(f"required documents present: {len(REQUIRED_FILES) - len(missing)}/{len(REQUIRED_FILES)}")

    code = max((sev for sev, _ in errors), default=0)
    return code, errors, infos


def main(argv=None) -> int:
    repo_root = Path(__file__).resolve().parent.parent
    p = argparse.ArgumentParser(description="WP0.0 review-adjudication gate")
    p.add_argument("--adjudication", type=Path,
                   default=repo_root / "docs" / "REVIEW_ADJUDICATION.md")
    p.add_argument("--root", type=Path, default=repo_root,
                   help="repo root for the required-files check")
    p.add_argument("--no-file-check", action="store_true",
                   help="skip the required-documents existence check")
    args = p.parse_args(argv)

    try:
        text = args.adjudication.read_text(encoding="utf-8")
    except OSError as e:
        print(f"[FAIL closed] cannot read {args.adjudication}: {e}", file=sys.stderr)
        return 2

    code, errors, infos = check_text(text, root=args.root, check_files=not args.no_file_check)

    for line in infos:
        print(f"  · {line}")
    for sev, msg in sorted(errors):  # deterministic order
        print(f"  [{'BLOCK' if sev == 2 else 'FINDING'}] {msg}", file=sys.stderr)

    if code == 0:
        print("OK — adjudication is coherent and governance is READY. "
              "(Coherent bookkeeping, NOT a truth certificate.)")
    else:
        print(f"FAILED — review-adjudication gate exit {code}.", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())

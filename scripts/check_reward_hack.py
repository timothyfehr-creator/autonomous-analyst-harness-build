#!/usr/bin/env python3
"""WP2.2c — cross-commit reward-hack range gate (V-P1-7) + the git-diff half of assessment governance.

The cold review's gaming concern (REVIEW_ADJUDICATION V-P1-7; Constitution §13 "changing oracle
data is reviewed separately and may not silently benefit a claim/visual in the same change";
IMPLEMENTATION_PLAN WP2.2 "no deletions or in-place rating changes ... a new/changed assessment
cannot benefit a claim introduced or upgraded in the same commit"). A single commit could move the
goalposts (a gate/threshold/test) AND the ball (a factbase record) together; splitting that across
two commits dodges a one-commit check, so this gate diffs across a RANGE (base..head).

Rules over `git diff base..head` (each finding names its rule):
  R-RH      an ORACLE path changed AND an EXISTING factbase record was modified/deleted (status
            M/D) in the range — gate-weakening + benefiting-data co-change. (net-new data, status A,
            does NOT trip — adding a record is not reward-hacking.)
  R-EDIT    an in-place rating change of a committed assessment (same sas- id, reliability differs
            base→head) — append-only is violated; correction must be a superseding record.
  R-DELETE  a committed assessment id present at base is gone at head.
  R-HI      a factbase claim's high_impact flipped true→false, or its §10 trigger inputs (topics /
            prediction_id) changed on an existing claim — the all-DATA high_impact tamper (R4).
  R-COLLUDE a factbase assessment and a factbase claim both changed in the range (a new/upgraded
            assessment benefiting a claim) — IMPLEMENTATION_PLAN WP2.2 / the social-source-upgrade
            fixture.

Carve-outs (printed, never silent): a `Reviewed-separately:` trailer on EVERY commit in the range
clears R-RH/R-COLLUDE (the §13 "reviewed separately" escape made auditable; a dishonest trailer is a
logged residual, not closed). DATA = `factbase/**` only (the answer-affecting records — the
"benefiting claim/visual"); `tests/**` + `config/**` + `scripts/**` are ORACLE (test inputs,
expectations, thresholds, and code are all goalposts).

`--base` is REQUIRED (no safe auto-base in a no-remote single branch). Missing/unresolvable base or
non-git → exit 2 (fail closed). Exit codes: 0 clean · 1 flagged · 2 cannot-run.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
_ATTEST_TRAILER = "Reviewed-separately:"
_TRIGGER_INPUTS = ("topics", "prediction_id")


# ----------------------------- path classification (ordered, first-match-wins) -----------------------------
def classify_path(path: str) -> str:
    """ORACLE (goalposts) | DATA (factbase records) | UNCLASSIFIED. Ordered so fixture/test files
    are ORACLE, never DATA — only the factbase is the benefiting 'ball'."""
    p = path.replace("\\", "/")
    if p.startswith("factbase/"):
        return "DATA"
    if p.startswith("tests/") or p.startswith("config/") or p.startswith("scripts/"):
        return "ORACLE"
    return "UNCLASSIFIED"


# ----------------------------- git helpers (fail-closed) -----------------------------
class GitError(Exception):
    pass


def _git(root: Path, *args: str) -> str:
    try:
        r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    except FileNotFoundError as e:
        raise GitError(f"git not available ({e})")
    if r.returncode != 0:
        raise GitError(f"git {' '.join(args)} failed: {r.stderr.strip()}")
    return r.stdout


def _resolve(root: Path, rev: str) -> str:
    return _git(root, "rev-parse", "--verify", f"{rev}^{{commit}}").strip()


def _changed(root: Path, base: str, head: str):
    out = _git(root, "diff", "--name-status", f"{base}..{head}")
    changed = []
    for line in out.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0][0]  # R100 -> 'R'; take the first char
        path = parts[-1]      # for renames the new path is last
        changed.append((status, path))
    return changed


def _show_yaml(root: Path, rev: str, path: str):
    try:
        out = _git(root, "show", f"{rev}:{path}")
    except GitError:
        return None  # absent at this rev (e.g. added file)
    try:
        return yaml.safe_load(out)
    except yaml.YAMLError:
        return None


def _attested(root: Path, base: str, head: str) -> bool:
    """True iff EVERY commit in base..head carries the Reviewed-separately: trailer (all-or-nothing)."""
    out = _git(root, "log", "--format=%B%x1e", f"{base}..{head}")
    commits = [c for c in out.split("\x1e") if c.strip()]
    return bool(commits) and all(_ATTEST_TRAILER in c for c in commits)


def _records(doc, key):
    if isinstance(doc, dict) and isinstance(doc.get(key), list):
        return {r.get("id"): r for r in doc[key] if isinstance(r, dict)}
    return {}


def _record_changes(root: Path, base: str, head: str, changed):
    """Diff factbase claim + assessment files by record id between base and head."""
    claim_changes, assessment_changes = [], []
    data_paths = {p for s, p in changed if classify_path(p) == "DATA"}
    for path in sorted(data_paths):
        base_doc, head_doc = _show_yaml(root, base, path), _show_yaml(root, head, path)
        # claims
        b, h = _records(base_doc, "claims"), _records(head_doc, "claims")
        for cid in sorted(set(b) | set(h)):
            bc, hc = b.get(cid), h.get(cid)
            if bc and hc:
                ti = sorted(k for k in _TRIGGER_INPUTS if bc.get(k) != hc.get(k))
                claim_changes.append({"id": cid, "base_hi": bc.get("high_impact"),
                                      "head_hi": hc.get("high_impact"), "trigger_inputs_changed": ti,
                                      "status": "M"})
            elif hc and not bc:
                claim_changes.append({"id": cid, "base_hi": None, "head_hi": hc.get("high_impact"),
                                      "trigger_inputs_changed": [], "status": "A"})
        # assessments
        b, h = _records(base_doc, "source_assessments"), _records(head_doc, "source_assessments")
        for sid in sorted(set(b) | set(h)):
            ba, ha = b.get(sid), h.get(sid)
            if ba and ha:
                assessment_changes.append({"id": sid, "base_reliability": ba.get("reliability"),
                                           "head_reliability": ha.get("reliability"), "status": "M"})
            elif ha and not ba:
                assessment_changes.append({"id": sid, "base_reliability": None,
                                           "head_reliability": ha.get("reliability"), "status": "A"})
            elif ba and not ha:
                assessment_changes.append({"id": sid, "base_reliability": ba.get("reliability"),
                                           "head_reliability": None, "status": "D"})
    return claim_changes, assessment_changes


# ----------------------------- pure evaluation (unit-testable) -----------------------------
def evaluate(changed, claim_changes, assessment_changes, attested: bool):
    """Pure reward-hack logic given the diff data. Returns (exit_code, findings)."""
    findings, cleared = [], []
    oracle = sorted({p for s, p in changed if classify_path(p) == "ORACLE"})
    data_md = sorted({p for s, p in changed if classify_path(p) == "DATA" and s in ("M", "D")})

    # R-RH: gate-weakening + benefiting-data co-change (cleared by an all-commit attestation)
    if oracle and data_md:
        msg = (f"R-RH reward-hack co-change: ORACLE {oracle} changed alongside modified factbase "
               f"data {data_md} in the same range")
        (cleared if attested else findings).append(msg)

    # R-EDIT / R-DELETE: append-only assessment governance over the range
    for a in assessment_changes:
        if a["status"] == "M" and a["base_reliability"] != a["head_reliability"]:
            findings.append(f"R-EDIT in-place rating change of committed assessment {a['id']!r}: "
                            f"{a['base_reliability']!r}→{a['head_reliability']!r} (use a superseding record)")
        if a["status"] == "D":
            findings.append(f"R-DELETE committed assessment {a['id']!r} was deleted (append-only)")

    # R-HI: all-DATA high_impact tamper on an existing claim (R4)
    for c in claim_changes:
        if c["status"] == "M" and c["base_hi"] is True and c["head_hi"] is False:
            findings.append(f"R-HI high_impact flipped true→false on claim {c['id']!r} (V-P0-1 tamper)")
        if c["status"] == "M" and c["trigger_inputs_changed"]:
            findings.append(f"R-HI §10 trigger inputs {c['trigger_inputs_changed']} changed on existing "
                            f"claim {c['id']!r} (possible high_impact-trigger dodge)")

    # R-COLLUDE: an assessment change benefiting a claim change in the same range (no adjudication)
    a_changed = [a["id"] for a in assessment_changes if a["status"] in ("A", "M")]
    c_changed = [c["id"] for c in claim_changes if c["status"] in ("A", "M")]
    if a_changed and c_changed:
        msg = (f"R-COLLUDE assessment(s) {sorted(a_changed)} changed in the same range as claim(s) "
               f"{sorted(c_changed)} (a new/changed assessment may not benefit a same-range claim "
               f"without a named adjudication exception)")
        (cleared if attested else findings).append(msg)

    return (1 if findings else 0), sorted(findings), sorted(cleared)


def run(root: Path, base: str, head: str):
    """Gather the diff data from git and evaluate. Fail closed (exit 2) on any git error."""
    try:
        base_sha, head_sha = _resolve(root, base), _resolve(root, head)
        changed = _changed(root, base_sha, head_sha)
        attested = _attested(root, base_sha, head_sha)
        claim_changes, assessment_changes = _record_changes(root, base_sha, head_sha, changed)
    except GitError as e:
        return 2, [f"cannot run reward-hack gate (fail closed): {e}"], []
    return evaluate(changed, claim_changes, assessment_changes, attested)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP2.2c cross-commit reward-hack range gate (V-P1-7)")
    p.add_argument("--base", required=True, help="base ref (REQUIRED; no safe auto-base)")
    p.add_argument("--head", default="HEAD")
    p.add_argument("--root", type=Path, default=REPO_ROOT)
    args = p.parse_args(argv)
    code, findings, cleared = run(args.root, args.base, args.head)
    for c in sorted(cleared):
        print(f"  [cleared-by-attestation] {c}", file=sys.stderr)
    for f in sorted(findings):
        print(f"  [finding] {f}", file=sys.stderr)
    if code == 0:
        print("OK — no reward-hack co-change in range. (Tripwire, NOT a truth certificate.)")
    return code


if __name__ == "__main__":
    sys.exit(main())

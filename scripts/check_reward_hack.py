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
logged residual, not closed). DATA = `factbase/**` only (the answer-affecting claim / assessment /
claim-evidence records); `tests/**` + `config/**` + `scripts/**` are ORACLE (test inputs,
expectations, thresholds, and code are all goalposts). The answer/visual layer
(analyses/visuals/outputs) is chartered to WP3/WP5.1, which carry their own co-change protection.

`--base` is REQUIRED (no safe auto-base in a no-remote single branch). Missing/unresolvable base or
non-git → exit 2 (fail closed). Exit codes: 0 clean · 1 flagged · 2 cannot-run.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling import
import validate_schema as vs  # noqa: E402  (for the frozen record_hash — in-place-edit detection)

REPO_ROOT = Path(__file__).resolve().parent.parent
# Anchored trailer (a casual prose mention or an empty-valued trailer cannot clear the gate).
_ATTEST_RE = re.compile(r"(?mi)^\s*Reviewed-separately:\s*\S")
# The full §10 T2 conjunction validate_high_impact recomputes on (a change to any is suspicious).
_TRIGGER_INPUTS = ("topics", "prediction_id", "epistemic_type", "projection_kind")


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
    # --no-renames: a `git mv` of a factbase file would otherwise appear as one 'R' row on the NEW
    # path, hiding the deleted old path and letting a rename-and-edit dodge every record rule.
    out = _git(root, "diff", "--no-renames", "--name-status", f"{base}..{head}")
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
    """True iff EVERY commit in base..head carries an anchored Reviewed-separately: <value> trailer
    (all-or-nothing). A dishonest trailer remains a printed, auditable residual (not a silent pass);
    R-EDIT/R-DELETE/R-HI are never clearable by attestation."""
    out = _git(root, "log", "--format=%B%x1e", f"{base}..{head}")
    commits = [c for c in out.split("\x1e") if c.strip()]
    return bool(commits) and all(_ATTEST_RE.search(c) for c in commits)


def _records(doc, key):
    if isinstance(doc, dict) and isinstance(doc.get(key), list):
        return {r.get("id"): r for r in doc[key] if isinstance(r, dict)}
    return {}


def _record_changes(root: Path, base: str, head: str, changed):
    """Diff factbase claim / assessment / claim-evidence records BY ID, reconciled GLOBALLY across
    all changed DATA paths. Global-by-id (not per-current-path) so a renamed-and-edited record is
    still matched base→head (a `git mv` cannot reclassify a true→false flip as a clean status 'A')."""
    data_paths = sorted({p for s, p in changed if classify_path(p) == "DATA"})
    base_c, head_c, base_a, head_a, base_e, head_e = ({}, {}, {}, {}, {}, {})
    for path in data_paths:
        bd, hd = _show_yaml(root, base, path), _show_yaml(root, head, path)
        base_c.update(_records(bd, "claims")); head_c.update(_records(hd, "claims"))
        base_a.update(_records(bd, "source_assessments")); head_a.update(_records(hd, "source_assessments"))
        base_e.update(_records(bd, "claim_evidence_assessments")); head_e.update(_records(hd, "claim_evidence_assessments"))

    claim_changes = []
    for cid in sorted(set(base_c) | set(head_c)):
        bc, hc = base_c.get(cid), head_c.get(cid)
        if bc and hc:
            ti = sorted(k for k in _TRIGGER_INPUTS if bc.get(k) != hc.get(k))
            claim_changes.append({"id": cid, "status": "M", "base_hi": bc.get("high_impact"),
                                  "head_hi": hc.get("high_impact"), "trigger_inputs_changed": ti})
        elif hc and not bc:
            claim_changes.append({"id": cid, "status": "A", "base_hi": None,
                                  "head_hi": hc.get("high_impact"), "trigger_inputs_changed": []})

    assessment_changes = []
    for sid in sorted(set(base_a) | set(head_a)):
        ba, ha = base_a.get(sid), head_a.get(sid)
        if ba and ha:  # content_changed via the frozen record_hash → catches ALL in-place edits
            assessment_changes.append({"id": sid, "status": "M",
                                       "content_changed": vs.record_hash(ba) != vs.record_hash(ha)})
        elif ha and not ba:
            assessment_changes.append({"id": sid, "status": "A", "content_changed": False})
        elif ba and not ha:
            assessment_changes.append({"id": sid, "status": "D", "content_changed": False})

    cea_changes = []  # the layer a source upgrade actually benefits a claim through (DATA_MODEL §4)
    for eid in sorted(set(base_e) | set(head_e)):
        be, he = base_e.get(eid), head_e.get(eid)
        if be and he:
            benefit = (be.get("stance") != he.get("stance")
                       or be.get("information_credibility") != he.get("information_credibility"))
            cea_changes.append({"id": eid, "status": "M", "benefit_changed": benefit})
        elif he and not be:
            cea_changes.append({"id": eid, "status": "A", "benefit_changed": True})

    return claim_changes, assessment_changes, cea_changes


# ----------------------------- pure evaluation (unit-testable) -----------------------------
def evaluate(changed, claim_changes, assessment_changes, cea_changes, attested: bool):
    """Pure reward-hack logic given the diff data. Returns (exit_code, findings, cleared)."""
    findings, cleared = [], []
    oracle = sorted({p for s, p in changed if classify_path(p) == "ORACLE"})
    data_md = sorted({p for s, p in changed if classify_path(p) == "DATA" and s in ("M", "D")})

    # R-RH: gate-weakening + benefiting-data co-change (cleared by an all-commit attestation)
    if oracle and data_md:
        msg = (f"R-RH reward-hack co-change: ORACLE {oracle} changed alongside modified factbase "
               f"data {data_md} in the same range")
        (cleared if attested else findings).append(msg)

    # R-EDIT / R-DELETE: append-only assessment governance over the range (ANY content edit, by hash)
    for a in assessment_changes:
        if a["status"] == "M" and a["content_changed"]:
            findings.append(f"R-EDIT in-place edit of committed assessment {a['id']!r} (content "
                            f"changed; a correction must be a superseding record, DATA_MODEL §14)")
        if a["status"] == "D":
            findings.append(f"R-DELETE committed assessment {a['id']!r} was deleted (append-only)")

    # R-HI: all-DATA high_impact tamper on an existing claim (R4)
    for c in claim_changes:
        if c["status"] == "M" and c["base_hi"] is True and c["head_hi"] is False:
            findings.append(f"R-HI high_impact flipped true→false on claim {c['id']!r} (V-P0-1 tamper)")
        if c["status"] == "M" and c["trigger_inputs_changed"]:
            findings.append(f"R-HI §10 trigger inputs {c['trigger_inputs_changed']} changed on existing "
                            f"claim {c['id']!r} (possible high_impact-trigger dodge)")

    # R-COLLUDE: an assessment change benefiting a claim in the same range (no adjudication). The
    # benefit may route through the claim record OR through the claim-evidence layer (stance/
    # credibility), which is where a source upgrade actually changes a support verdict (§4/§13).
    a_changed = sorted(a["id"] for a in assessment_changes if a["status"] in ("A", "M"))
    benefit = sorted([c["id"] for c in claim_changes if c["status"] in ("A", "M")]
                     + [e["id"] for e in cea_changes if e["status"] == "A"
                        or (e["status"] == "M" and e["benefit_changed"])])
    if a_changed and benefit:
        msg = (f"R-COLLUDE assessment(s) {a_changed} changed in the same range as benefiting "
               f"claim/claim-evidence record(s) {benefit} (a new/changed assessment may not benefit "
               f"a same-range claim without a named adjudication exception)")
        (cleared if attested else findings).append(msg)

    return (1 if findings else 0), sorted(findings), sorted(cleared)


def run(root: Path, base: str, head: str):
    """Gather the diff data from git and evaluate. Fail closed (exit 2) on any git error."""
    try:
        base_sha, head_sha = _resolve(root, base), _resolve(root, head)
        changed = _changed(root, base_sha, head_sha)
        attested = _attested(root, base_sha, head_sha)
        claim_changes, assessment_changes, cea_changes = _record_changes(root, base_sha, head_sha, changed)
    except GitError as e:
        return 2, [f"cannot run reward-hack gate (fail closed): {e}"], []
    return evaluate(changed, claim_changes, assessment_changes, cea_changes, attested)


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

#!/usr/bin/env python3
"""WP2.6 — conflict / stance gate: recompute `dispute_status` (CONTESTED) from the evidence.

Constitution §6.4: `CONTESTED` requires independent credible positions that materially disagree;
duplicate republication cannot satisfy both sides; credible mixed stances on an `UNCONTESTED` claim
fail. This gate recomputes the CONTESTED axis from a claim's ACTIVE CHECKED assessments and rejects
a stored label that disagrees — BIDIRECTIONALLY (a deliberate departure from WP2.5's over-claim-only
convention, forced by §6.4's "credible mixed stances on an UNCONTESTED claim fail"):
  - a stored UNCONTESTED/UNKNOWN that HIDES an independent credible conflict fails;
  - a stored CONTESTED with no such conflict in the evidence fails (unearned).

A contest exists iff there is a credible SUPPORTS position and a credible opposing position
(REFUTES, or MIXED as a structural opposer) at DISTINCT underlying origins — independence is counted
by `origin_chain[0].source_id` (reusing WP2.5's collapse), so a source that appears on both sides
(self-contradiction / duplicate republication) cannot manufacture a contest. CONTEXT_ONLY never
counts as a side; only active CHECKED assessments enter the tally.

DECISIONS (owner-flaggable, defaults chosen per the autonomy contract):
  - "credible" = CHECKED + a credibility SCORE (information_credibility ∈ {1..6}, not UNASSESSED).
    The §6.1b ≤3 floor is scoped to corroboration, not conflict; using "scored" honors §6.4's
    anti-hiding intent (a moderate-credibility REFUTES still registers a conflict). ALTERNATIVE the
    owner may pick: require ≤3 — a one-line change in `_is_credible`.
  - The gate polices ONLY the CONTESTED axis; UNKNOWN vs UNCONTESTED (both "no established conflict")
    is doc-undefined and not policed here.
  - Recompute scoped to FACT/INFERENCE (mirrors WP2.5); ASSUMPTION carries no evidence; PROJECTION
    unpinned → skipped.

Out of scope: support_status (WP2.5, read-only here), freshness (WP2.7), observation (WP2.8); TRUE
material disagreement and the answer-render "keep the losing side visible" clause are the WP3.3
refuter / Phase-3 answer mode. Schema-first; cea registry required (unreadable → exit 2); empty → 0.
Exit codes: 0 / 1 / 2.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling import
import validate_schema as vs  # noqa: E402
import validate_support as vsup  # noqa: E402  (active_checked_by_claim, _origin0, RECOMPUTE_TYPES, DEFAULT_*)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLAIMS = vsup.DEFAULT_CLAIMS
DEFAULT_CEA = vsup.DEFAULT_CEA
_OPPOSING = {"REFUTES", "MIXED"}  # MIXED counts as a structural opposer; true materiality is WP3.3


def _is_credible(a) -> bool:
    """Conflict 'credible' bar: a credibility SCORE in {1..6} (UNASSESSED / non-int fail). CHECKED is
    already guaranteed by active_checked_by_claim. (Owner-flaggable: tighten to <=3 if preferred.)"""
    cred = a.get("information_credibility")
    return isinstance(cred, int) and not isinstance(cred, bool) and 1 <= cred <= 6


def compute_dispute(active_checked) -> str:
    """Return UNKNOWN / UNCONTESTED / CONTESTED from a claim's active CHECKED assessments."""
    credible = [a for a in active_checked if _is_credible(a)]
    pro = {vsup._origin0(a) for a in credible if a.get("stance") == "SUPPORTS"} - {None}
    con = {vsup._origin0(a) for a in credible if a.get("stance") in _OPPOSING} - {None}
    contested = any(p != c for p in pro for c in con)  # distinct underlying origins on each side
    if contested:
        return "CONTESTED"
    return "UNCONTESTED" if credible else "UNKNOWN"


def check_conflict(claims, ceas) -> list[str]:
    """CONTESTED-axis findings for the schema-clean merged claim set (bidirectional)."""
    findings = []
    active = vsup.active_checked_by_claim(ceas)
    for c in claims:
        if c.get("epistemic_type") not in vsup.RECOMPUTE_TYPES:
            continue
        stored, computed = c.get("dispute_status"), compute_dispute(active.get(c.get("id"), []))
        if computed == "CONTESTED" and stored != "CONTESTED":
            findings.append(f"claim {c.get('id')!r}: dispute_status stored {stored} but an independent "
                            f"credible conflict exists in the evidence — a hidden conflict (§6.4)")
        elif stored == "CONTESTED" and computed != "CONTESTED":
            findings.append(f"claim {c.get('id')!r}: dispute_status stored CONTESTED but no independent "
                            f"credible conflict in the evidence (computed {computed}) — unearned")
    return sorted(findings)


def validate_conflict(claims_paths, cea_path):
    """Return (exit_code, findings). Schema-first per claims file; recompute on the merged set."""
    schema_findings, code = [], 0
    for p in claims_paths:
        c, f = vs.validate_file(p)
        code = max(code, c)
        schema_findings += f
    if code != 0:
        return code, schema_findings
    try:
        cea_data = vs.load_yaml_strict(cea_path) or {}
        ceas = cea_data.get("claim_evidence_assessments") or []
    except Exception as e:  # noqa: BLE001 — registry read/parse failure is §13 fail-closed
        return 2, [f"cannot read the claim-evidence registry for conflict recompute (fail closed): {e}"]
    merged = []
    for p in claims_paths:
        d = vs.load_yaml_strict(p) or {}
        merged += [c for c in (d.get("claims") or []) if isinstance(c, dict)]
    findings = check_conflict(merged, ceas)
    return (1 if findings else 0), findings


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP2.6 conflict / stance gate (dispute_status recompute)")
    p.add_argument("paths", nargs="*", type=Path, help="claim files (default baseline+live)")
    p.add_argument("--claim-evidence", type=Path, default=DEFAULT_CEA)
    args = p.parse_args(argv)
    claims_paths = args.paths or DEFAULT_CLAIMS
    code, findings = validate_conflict(claims_paths, args.claim_evidence)
    for f in sorted(findings):
        print(f"  [finding] {f}", file=sys.stderr)
    if code == 0:
        print("OK — conflict/dispute_status recompute clean. (Structural contest; NOT a truth certificate.)")
    return code


if __name__ == "__main__":
    sys.exit(main())

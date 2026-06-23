#!/usr/bin/env python3
"""WP2.2a — `high_impact` gate-recompute (V-P0-1, the P0 fix).

The #1 cold-review finding: `high_impact` was author-set and never gate-recomputed, so an analyst
could silently downgrade a casualties/attribution/territorial-control claim. Per Constitution §10
("high_impact is not author-set ... the author may not set it false ... a stored value is
recomputed and a mismatch fails"), this gate recomputes the field from the triggers it can see and
RAISES a stored `false` that should be `true`.

What is computable at records scope (the false→true direction — a LOWER BOUND on high_impact):
  T1  topics ∩ trigger tokens (config/high_impact_triggers.yaml, oracle data) — exact token match
      after NFC + casefold + strip (NOT substring: "attribution" ≠ "redistribution").
  T2-pred  a FALSIFIABLE projection carrying a non-null prediction_id ("feeds a prediction").

DEFERRED (NOT scored here; printed as a [deferred] notice so an unscannable leg is never silently
treated as a clean `false`): "feeds a manifest / shared visual" (WP3.2 / Phase 5) and "contradicts
a prior recorded claim" (WP2.6). Because those legs aren't computable, a stored `true` is ALWAYS
accepted (the author may flag up; only flagging DOWN past a visible trigger is the violation). The
refuter-must-contest half of §10 is WP3.3.

Empty/unreadable trigger config → exit 2 (§13 empty-rule-set: a gate that scans nothing and reports
success is worse than no gate). Schema runs first; a malformed claims file fails at the schema layer
without recompute masking it.

Exit codes: 0 clean · 1 a stored false that recomputes true · 2 cannot-run / fail closed.
"""
from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling import
import schema_defs  # noqa: E402
import validate_schema as vs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLAIMS = [REPO_ROOT / "factbase" / "baseline" / "claims.yaml",
                  REPO_ROOT / "factbase" / "live" / "claims.yaml"]


def normalize_topic(s) -> str:
    """The match key for topic↔trigger comparison: NFC, casefold, strip. Exact-token (callers
    compare equality, never substring)."""
    return unicodedata.normalize("NFC", str(s)).casefold().strip()


def trigger_set(tokens=None) -> set[str]:
    toks = schema_defs.HIGH_IMPACT_TRIGGER_TOKENS if tokens is None else tokens
    return {normalize_topic(t) for t in toks}


def compute_high_impact(claim: dict, triggers: set[str]) -> tuple[bool, list[str]]:
    """Return (computed_lower_bound, reasons). Only the computable triggers (T1, T2-pred)."""
    reasons = []
    topics = claim.get("topics") or []
    if isinstance(topics, list):
        hit = sorted({normalize_topic(t) for t in topics} & triggers)
        if hit:
            reasons.append(f"T1 topic(s) {hit} intersect the high_impact trigger set")
    if (claim.get("epistemic_type") == "PROJECTION"
            and claim.get("projection_kind") == "FALSIFIABLE"
            and claim.get("prediction_id")):
        reasons.append("T2 a falsifiable projection feeds a prediction")
    return (bool(reasons), reasons)


def check_claims(data, triggers: set[str]) -> tuple[list[str], list[str]]:
    """Return (findings, deferred_notices) for a schema-clean claims envelope."""
    findings, notices = [], []
    for claim in data.get("claims", []) or []:
        cid = claim.get("id")
        computed, reasons = compute_high_impact(claim, triggers)
        stored = claim.get("high_impact")
        if computed and stored is False:
            findings.append(f"claim {cid!r}: high_impact stored false but computed true "
                            f"({'; '.join(reasons)}) — author may not set it false (§10/V-P0-1)")
        elif stored is True and not computed:
            notices.append(f"claim {cid!r}: high_impact true accepted on author's word — the "
                           f"manifest/visual (WP3.2/Ph5) and contradiction (WP2.6) legs are not "
                           f"computable at records scope [deferred, not scored]")
    return sorted(findings), sorted(notices)


def validate_high_impact_file(path: Path, triggers: set[str]):
    """Return (exit_code, findings, notices). Schema first; integrity only on a clean parse."""
    code, schema_findings = vs.validate_file(path)
    if code != 0:
        return code, schema_findings, []
    data = vs.load_yaml_strict(path)
    findings, notices = check_claims(data, triggers)
    return (1 if findings else 0), [f"{path.name}: {f}" for f in findings], notices


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP2.2a high_impact recompute gate (V-P0-1)")
    p.add_argument("paths", nargs="*", type=Path)
    p.add_argument("--triggers", type=Path, default=None,
                   help="override trigger config path (else config/high_impact_triggers.yaml)")
    args = p.parse_args(argv)

    # Trigger oracle: load (optionally from an override path) and FAIL CLOSED if empty (§13).
    if args.triggers is not None:
        tokens = _load_tokens_from(args.triggers)
    else:
        tokens = schema_defs.HIGH_IMPACT_TRIGGER_TOKENS
    triggers = trigger_set(tokens)
    if not triggers:
        print("[FAIL closed] high_impact trigger set is empty/unreadable — a gate that scans "
              "nothing is worse than no gate (§13). Check config/high_impact_triggers.yaml.",
              file=sys.stderr)
        return 2

    paths = args.paths or DEFAULT_CLAIMS
    code, all_findings, all_notices = 0, [], []
    for path in paths:
        c, findings, notices = validate_high_impact_file(path, triggers)
        code = max(code, c)
        all_findings += findings
        all_notices += notices
    for n in sorted(all_notices):
        print(f"  [deferred] {n}", file=sys.stderr)
    for f in sorted(all_findings):
        print(f"  [finding] {f}", file=sys.stderr)
    if code == 0:
        print("OK — high_impact recompute clean. (Lower-bound recompute; NOT a truth certificate.)")
    return code


def _load_tokens_from(path: Path):
    """Load trigger tokens from an explicit config path (for tests / overrides). Empty on error."""
    try:
        doc = vs.load_yaml_strict(path) or {}
    except Exception:
        return []
    entries = doc.get("high_impact_triggers", []) if isinstance(doc, dict) else []
    if not isinstance(entries, list):
        return []
    return [e["token"] for e in entries if isinstance(e, dict) and "token" in e]


if __name__ == "__main__":
    sys.exit(main())

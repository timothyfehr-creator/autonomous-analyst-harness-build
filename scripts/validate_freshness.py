#!/usr/bin/env python3
"""WP2.7 — freshness gate: recompute `freshness_status` against an INJECTABLE clock.

Constitution §6.5 / §5: freshness is the NOW-RELATIVE state of a claim's temporal contract — it must
derive from the declared dates vs a clock, never from wall-clock-at-runtime (reproducibility). This
gate recomputes `freshness_status` from (epistemic_type, stability, declared dates, `--as-of`) and
rejects a stored label that disagrees, BIDIRECTIONALLY (DATA_MODEL §5/§14 "recompute and reject a
mismatch" / "reject drift"): both an over-fresh stored CURRENT that is actually REVIEW_DUE/STALE AND
a false STALE that suppresses a still-current claim fail. (This departs from WP2.5/high_impact's
over-claim-only — owner-flaggable; the literal §5/§14 wording is symmetric and the false-STALE
direction is a real suppression vector.)

Recompute:
  - epistemic_type != FACT            → NOT_APPLICABLE (the support/freshness axes are FACT contracts;
                                        a non-FACT carrying CURRENT/REVIEW_DUE/STALE is unearned);
  - FACT + DURABLE                    → REVIEW_DUE iff as_of >= review_by, else CURRENT (inclusive
                                        boundary: "becomes REVIEW_DUE AT review_by");
  - FACT + VOLATILE + expires_at      → STALE iff as_of >= expires_at, else CURRENT;
  - FACT + VOLATILE + only a named freshness_profile → CANNOT-RUN (no profile registry exists yet) →
                                        exit 2, fail-closed (deferred until config/freshness_profiles);
  - FACT + APPEND_ONLY_HISTORY        → CURRENT (an event ledger never goes stale; canonical label
                                        flagged owner-confirmable).
Claims with lifecycle SUPERSEDED/REJECTED are excluded from the recompute (IMPLEMENTATION_PLAN WP2.7).

`--as-of` is REQUIRED (no silent wall-clock; absent/unparseable → exit 2). Out of scope: clock-free
date ordering (review_by/expires_at >= created_at = WP2.4, owner-ratified); support (WP2.5); conflict
(WP2.6); observation (WP2.8); the valid_as_of-vs-newest-evidence-endpoint leg + the answer-render
"keep stale visibly distinguishable" clause (Phase 3/4). NOTE for records-mode: validate_claims
(R-CLM-9/10 clock-free ordering) must run BEFORE this gate so a date-precedes-created_at incoherence
is caught first; WP2.7 standalone does not compose it. Schema-first; empty factbase → 0. Exit 0/1/2.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling import
import schema_defs  # noqa: E402  (iso_instant)
import validate_schema as vs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLAIMS = [REPO_ROOT / "factbase" / "baseline" / "claims.yaml",
                  REPO_ROOT / "factbase" / "live" / "claims.yaml"]
_INACTIVE = {"SUPERSEDED", "REJECTED"}


def compute_freshness(claim, as_of):
    """Return (freshness_status, problem). problem='profile' signals a fail-closed (no registry)."""
    if claim.get("epistemic_type") != "FACT":
        return "NOT_APPLICABLE", None
    stab = claim.get("stability")
    if stab == "DURABLE":
        rb = schema_defs.iso_instant(claim.get("review_by"))
        if rb is None:
            return None, "nodate"
        return ("REVIEW_DUE" if as_of >= rb else "CURRENT"), None
    if stab == "VOLATILE":
        ex = schema_defs.iso_instant(claim.get("expires_at"))
        if ex is None:
            return None, "profile"  # freshness_profile-only → unresolvable, fail closed
        return ("STALE" if as_of >= ex else "CURRENT"), None
    if stab == "APPEND_ONLY_HISTORY":
        return "CURRENT", None  # event ledger never expires
    return "NOT_APPLICABLE", None  # defensive (FACT with an unexpected stability)


def check_freshness(claims, as_of):
    """Return (exit_code, findings). Bidirectional recompute-and-reject vs the injected clock."""
    findings = []
    for c in claims:
        if c.get("lifecycle") in _INACTIVE:
            continue  # inactive leaves are not live freshness targets
        computed, problem = compute_freshness(c, as_of)
        if problem == "profile":
            return 2, [f"claim {c.get('id')!r}: VOLATILE with a named freshness_profile and no "
                       f"expires_at — no profile registry to resolve (fail closed, §13)"]
        if problem == "nodate":
            return 2, [f"claim {c.get('id')!r}: DURABLE FACT with an unparseable/absent review_by "
                       f"(fail closed)"]
        stored = c.get("freshness_status")
        if computed is not None and stored != computed:
            findings.append(f"claim {c.get('id')!r}: freshness_status stored {stored} but recomputes "
                            f"{computed} as of {as_of.isoformat()}")
    return (1 if findings else 0), sorted(findings)


def validate_freshness(claims_paths, as_of_str):
    """Return (exit_code, findings). Schema-first per claims file; recompute on the merged set."""
    if not as_of_str:
        return 2, ["--as-of is required (no wall-clock default; a freshness gate without a clock "
                   "cannot run, §13)"]
    as_of = schema_defs.iso_instant(as_of_str)
    if as_of is None:
        return 2, [f"--as-of {as_of_str!r} is not a parseable ISO datetime (fail closed)"]
    schema_findings, code = [], 0
    for p in claims_paths:
        c, f = vs.validate_file(p)
        code = max(code, c)
        schema_findings += f
    if code != 0:
        return code, schema_findings
    merged = []
    for p in claims_paths:
        d = vs.load_yaml_strict(p) or {}
        merged += [c for c in (d.get("claims") or []) if isinstance(c, dict)]
    return check_freshness(merged, as_of)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP2.7 freshness gate (freshness_status recompute vs --as-of)")
    p.add_argument("paths", nargs="*", type=Path, help="claim files (default baseline+live)")
    p.add_argument("--as-of", default=None, help="REQUIRED injectable clock (ISO datetime, UTC Z)")
    args = p.parse_args(argv)
    claims_paths = args.paths or DEFAULT_CLAIMS
    code, findings = validate_freshness(claims_paths, args.as_of)
    for f in sorted(findings):
        print(f"  [finding] {f}", file=sys.stderr)
    if code == 0:
        print("OK — freshness recompute clean. (Now-relative state vs the injected clock; NOT a truth certificate.)")
    return code


if __name__ == "__main__":
    sys.exit(main())

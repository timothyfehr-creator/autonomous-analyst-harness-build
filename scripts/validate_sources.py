#!/usr/bin/env python3
"""WP2.1 — source registry INTEGRITY gate (first Phase-2 gate, DAG root).

Schema (WP1.2) checks each record's shape; this adds the cross-record rules a single-record
check can't see (DATA_MODEL §1, Constitution §3):
  - global ID uniqueness across sources AND groups (one namespace);
  - every group `member_ids` entry resolves to a KNOWN `src-` source (and is a src-, not a grp-);
  - active-window coherence (`active_to` not before `active_from`).

The "a group ID may not stand where a source is required" rule is enforced at the CONSUMING gates
(evidence/assessment, WP2.2–2.3) where a src- reference is expected; here we keep the registry
itself coherent. Schema is run first: an unparseable file fails closed (2); shape findings (1) are
returned WITHOUT integrity (don't double-report on malformed records); only a schema-clean file is
integrity-checked.

Exit codes: 0 clean · 1 findings in valid input · 2 cannot-run / fail closed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling import
import validate_schema as vs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCES = REPO_ROOT / "factbase" / "sources.yaml"


def check_sources(data) -> list[str]:
    """Cross-record integrity findings for a schema-clean sources file. Deterministically sorted."""
    findings = []
    sources = data.get("sources", []) or []
    groups = data.get("groups", []) or []

    seen: dict[str, str] = {}
    for coll, recs in (("sources", sources), ("groups", groups)):
        for r in recs:
            rid = r.get("id")
            if rid in seen:
                findings.append(f"duplicate id {rid!r} (appears in {seen[rid]} and {coll})")
            else:
                seen[rid] = coll

    src_ids = {r.get("id") for r in sources}
    for g in groups:
        gid = g.get("id")
        for m in g.get("member_ids", []) or []:
            if not (isinstance(m, str) and m.startswith("src-")):
                findings.append(f"group {gid!r} member {m!r} must be a src- source id")
            elif m not in src_ids:
                findings.append(f"group {gid!r} member {m!r} does not resolve to a known source")

    for s in sources:
        af, at = s.get("active_from"), s.get("active_to")
        if isinstance(af, str) and isinstance(at, str) and at < af:
            findings.append(f"source {s.get('id')!r} active_to {at!r} precedes active_from {af!r}")

    return sorted(findings)


def validate_sources_file(path: Path):
    """Return (exit_code, findings) with every finding prefixed by the file name exactly once.
    Schema first; integrity runs only on a schema-clean parse (no double-reporting on malformed
    records). `vs.validate_file` already prefixes its findings, so integrity findings are prefixed
    here to match."""
    code, schema_findings = vs.validate_file(path)
    if code != 0:
        # 2 = unparseable/fail-closed; 1 = shape findings — either way, don't run integrity on it.
        return code, schema_findings
    data = vs.load_yaml_strict(path)
    integrity = check_sources(data)
    return (1 if integrity else 0), [f"{path.name}: {f}" for f in integrity]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP2.1 source registry integrity gate")
    p.add_argument("paths", nargs="*", type=Path, default=[DEFAULT_SOURCES])
    args = p.parse_args(argv)
    paths = args.paths or [DEFAULT_SOURCES]
    code, all_findings = 0, []
    for path in paths:
        c, findings = validate_sources_file(path)
        code = max(code, c)
        all_findings += findings
    for f in sorted(all_findings):
        print(f"  [finding] {f}", file=sys.stderr)
    if code == 0:
        print("OK — source registry integrity clean. (Coherent bookkeeping, NOT a truth certificate.)")
    return code


if __name__ == "__main__":
    sys.exit(main())

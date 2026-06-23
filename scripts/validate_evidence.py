#!/usr/bin/env python3
"""WP2.3a — evidence-artifact INTEGRITY gate (cross-record + cross-file source resolution).

Schema (WP1.4 EVIDENCE_SCHEMA) checks each artifact's shape; this adds the rules a single-record
check can't (DATA_MODEL §3, §1; Constitution §3):
  - R-EVD-1 artifact id uniqueness (two list records may share an `id:` and slip the strict loader);
  - R-EVD-2 `source_id` RESOLVES to a known `src-` entity in the source registry (cross-file —
    the schema only checks the `src-` prefix; WP2.1's docstring defers resolution to here);
  - R-EVD-3 `source_id` is not a non-citable GROUP (DATA_MODEL §1 "a group ID cannot appear where a
    source entity is required"). Defensive: the WP1.4 schema types `source_id` as `ref:src-`, so a
    `grp-` value already fails at the schema layer and never reaches here — the reachable
    group-as-source enforcement is on `origin_chain[i].source_id` (WP2.3b). Kept for robustness;
  - R-EVD-4 content-hash uniqueness: two DISTINCT artifacts sharing one `content_hash` is one
    artifact (DATA_MODEL §14 "Artifacts are immutable by content hash; a changed object is a new
    artifact") — a finding (format is already the schema's `hash` type);
  - R-EVD-5 date coherence: `retrieved_at` not before `published_at` (you cannot retrieve before
    publication) — owner-ratified into DATA_MODEL §3 (2026-06-23). `occurred_at` ordering is NOT
    enforced (embargo/forward-dating is legitimate).

Schema runs first (unparseable→2, shape-broken→1 without integrity). The source registry is
required to resolve references: a missing/unreadable/duplicate-key sources file → exit 2 (§13
cannot-run). An empty evidence list → 0 (seed state). Exit codes: 0 / 1 / 2.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling import
import schema_defs  # noqa: E402  (iso_instant — robust date ordering)
import validate_schema as vs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_EVIDENCE = REPO_ROOT / "factbase" / "evidence.yaml"
DEFAULT_SOURCES = REPO_ROOT / "factbase" / "sources.yaml"


def load_source_ids(sources_path: Path):
    """Return (src_ids, grp_ids) or raise to signal fail-closed. The source file must itself parse."""
    data = vs.load_yaml_strict(sources_path)  # raises DuplicateKey / OSError / YAMLError
    if not isinstance(data, dict):
        raise ValueError(f"{sources_path.name}: not a mapping")
    src_ids = {s.get("id") for s in (data.get("sources") or []) if isinstance(s, dict)}
    grp_ids = {g.get("id") for g in (data.get("groups") or []) if isinstance(g, dict)}
    return src_ids, grp_ids


def check_evidence(records, src_ids, grp_ids) -> list[str]:
    """Cross-record + cross-file integrity findings for a schema-clean evidence list."""
    findings = []
    seen = {}
    by_hash = defaultdict(list)
    for r in records:
        rid = r.get("id")
        if rid in seen:
            findings.append(f"duplicate id {rid!r}")
        else:
            seen[rid] = True

        sid = r.get("source_id")
        if sid not in src_ids:
            if sid in grp_ids:  # defensive (unreachable via the ref:src- schema type)
                findings.append(f"source_id {sid!r} is a non-citable group; an artifact needs a source entity")
            else:
                findings.append(f"source_id {sid!r} does not resolve to a known source")

        ch = r.get("content_hash")
        if ch is not None:
            by_hash[ch].append(rid)

        pub, ret = schema_defs.iso_instant(r.get("published_at")), schema_defs.iso_instant(r.get("retrieved_at"))
        if pub is not None and ret is not None and ret < pub:
            findings.append(f"artifact {rid!r} retrieved_at {r.get('retrieved_at')!r} "
                            f"precedes published_at {r.get('published_at')!r}")

    for ch, rids in by_hash.items():
        if len(rids) > 1:
            findings.append(f"duplicate content_hash {ch!r} shared by artifacts {sorted(rids)} "
                            f"(identical content is one artifact)")
    return sorted(findings)


def validate_evidence_file(path: Path, src_ids, grp_ids):
    """Return (exit_code, findings). Schema first; integrity only on a schema-clean parse."""
    code, schema_findings = vs.validate_file(path)
    if code != 0:
        return code, schema_findings
    data = vs.load_yaml_strict(path)
    findings = check_evidence(data.get("evidence", []) or [], src_ids, grp_ids)
    return (1 if findings else 0), [f"{path.name}: {f}" for f in findings]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP2.3a evidence-artifact integrity gate")
    p.add_argument("paths", nargs="*", type=Path)
    p.add_argument("--sources", type=Path, default=DEFAULT_SOURCES,
                   help="source registry for source_id resolution (default factbase/sources.yaml)")
    args = p.parse_args(argv)
    try:
        src_ids, grp_ids = load_source_ids(args.sources)
    except Exception as e:  # noqa: BLE001 — ANY read/parse failure of the registry is §13 fail-closed
        print(f"[FAIL closed] cannot read source registry {args.sources} for resolution ({e})", file=sys.stderr)
        return 2

    paths = args.paths or [DEFAULT_EVIDENCE]
    code, all_findings = 0, []
    for path in paths:
        c, findings = validate_evidence_file(path, src_ids, grp_ids)
        code = max(code, c)
        all_findings += findings
    for f in sorted(all_findings):
        print(f"  [finding] {f}", file=sys.stderr)
    if code == 0:
        print("OK — evidence-artifact integrity clean. (Coherent bookkeeping, NOT a truth certificate.)")
    return code


if __name__ == "__main__":
    sys.exit(main())

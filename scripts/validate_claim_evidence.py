#!/usr/bin/env python3
"""WP2.3b — claim-evidence assessment GOVERNANCE gate (resolution + supersession + hash binding).

Schema (WP1.4 CLAIM_EVIDENCE_SCHEMA) checks each assessment's shape + the CHECKED-binds-three-hashes
SHAPE; this adds the cross-record/cross-file rules (DATA_MODEL §4, §1, §14; Constitution §6.1–6.2):
  - R-CEA-1 cea id uniqueness;
  - R-CEA-2 `claim_id` RESOLVES to a known `clm-` (across baseline + live claims);
  - R-CEA-3 `artifact_id` RESOLVES to a known `evd-`;
  - R-CEA-4 each `origin_chain[i].source_id` resolves to a `src-` and is NOT a `grp-` group (the
    REACHABLE "a group ID cannot stand where a source is required" case, §1 — origin source_ids are
    not schema-typed); each origin `artifact_id` (where present) resolves to a known `evd-`;
  - R-CEA-5 exactly one ACTIVE leaf per `(claim_id, artifact_id)` chain, and a supersedes edge may
    not cross pairs (shared supersession helper, partitioned);
  - R-CEA-7 a CHECKED `semantic_review.artifact_hash` must EQUAL the resolved artifact's
    `content_hash` (the binding the schema only shape-checks).

DEFERRED (NOT enforced here, by design): "active assessment on an ASSUMPTION is invalid" →
IMPLEMENTATION_PLAN routes it to WP2.4 (single owner, no double-report). The `claim_content_hash`
and `relationship_input_hash` EQUALITY is deferred — verified not reproducible from the frozen
record_hash, so a check now would false-fail; it lands with the capture/compose tooling. Support /
corroboration math (stance/credibility VALUES) is WP2.5; conflict is WP2.6; semantic displacement
is the WP3.3 refuter.

Schema runs first. Every referenced registry (claims / evidence / sources) is required to resolve
references — a missing/unreadable/duplicate-key one → exit 2 (§13 cannot-run). Empty cea list → 0.
Exit codes: 0 / 1 / 2.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling import
import supersession  # noqa: E402
import validate_schema as vs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CEA = REPO_ROOT / "factbase" / "claim_evidence.yaml"
DEFAULT_CLAIMS = [REPO_ROOT / "factbase" / "baseline" / "claims.yaml",
                  REPO_ROOT / "factbase" / "live" / "claims.yaml"]
DEFAULT_EVIDENCE = REPO_ROOT / "factbase" / "evidence.yaml"
DEFAULT_SOURCES = REPO_ROOT / "factbase" / "sources.yaml"


def load_ref_sets(claims_paths, evidence_path, sources_path):
    """Return (clm_ids, evd_hashes{id->content_hash}, src_ids, grp_ids). Raises on any read failure."""
    clm_ids = set()
    for cp in claims_paths:
        d = vs.load_yaml_strict(cp) or {}
        clm_ids |= {c.get("id") for c in (d.get("claims") or []) if isinstance(c, dict)}
    ed = vs.load_yaml_strict(evidence_path) or {}
    evd_hashes = {e.get("id"): e.get("content_hash")
                  for e in (ed.get("evidence") or []) if isinstance(e, dict)}
    sd = vs.load_yaml_strict(sources_path) or {}
    src_ids = {s.get("id") for s in (sd.get("sources") or []) if isinstance(s, dict)}
    grp_ids = {g.get("id") for g in (sd.get("groups") or []) if isinstance(g, dict)}
    return clm_ids, evd_hashes, src_ids, grp_ids


def check_claim_evidence(records, clm_ids, evd_hashes, src_ids, grp_ids) -> list[str]:
    """Cross-record/cross-file governance findings for a schema-clean claim-evidence log."""
    findings = []
    seen = {}
    for r in records:
        rid = r.get("id")
        if rid in seen:
            findings.append(f"duplicate id {rid!r}")
        else:
            seen[rid] = True

        if r.get("claim_id") not in clm_ids:
            findings.append(f"assessment {rid!r} claim_id {r.get('claim_id')!r} does not resolve to a known claim")
        aid = r.get("artifact_id")
        if aid not in evd_hashes:
            findings.append(f"assessment {rid!r} artifact_id {aid!r} does not resolve to a known artifact")

        for i, link in enumerate(r.get("origin_chain") or []):
            if not isinstance(link, dict):
                continue
            sid = link.get("source_id")
            if sid not in src_ids:
                if sid in grp_ids:
                    findings.append(f"assessment {rid!r} origin_chain[{i}] source_id {sid!r} is a "
                                    f"non-citable group; an origin needs a source entity")
                else:
                    findings.append(f"assessment {rid!r} origin_chain[{i}] source_id {sid!r} does not "
                                    f"resolve to a known source")
            laid = link.get("artifact_id")
            if laid is not None and laid not in evd_hashes:
                findings.append(f"assessment {rid!r} origin_chain[{i}] artifact_id {laid!r} does not "
                                f"resolve to a known artifact")

        sr = r.get("semantic_review")
        if isinstance(sr, dict) and sr.get("status") == "CHECKED" and aid in evd_hashes:
            if sr.get("artifact_hash") != evd_hashes[aid]:
                findings.append(f"assessment {rid!r} CHECKED artifact_hash does not match artifact "
                                f"{aid!r} content_hash (the binding is to the wrong/edited artifact)")

    # one active leaf per (claim_id, artifact_id) chain; a supersedes edge may not cross pairs
    findings += supersession.check_supersession(
        records, partition_key=lambda r: (r.get("claim_id"), r.get("artifact_id")), label="assessment")
    return sorted(findings)


def validate_claim_evidence_file(path: Path, refs):
    code, schema_findings = vs.validate_file(path)
    if code != 0:
        return code, schema_findings
    data = vs.load_yaml_strict(path)
    findings = check_claim_evidence(data.get("claim_evidence_assessments", []) or [], *refs)
    return (1 if findings else 0), [f"{path.name}: {f}" for f in findings]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP2.3b claim-evidence governance gate")
    p.add_argument("paths", nargs="*", type=Path)
    p.add_argument("--claims", type=Path, nargs="*", default=None)
    p.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    p.add_argument("--sources", type=Path, default=DEFAULT_SOURCES)
    args = p.parse_args(argv)
    claims_paths = args.claims if args.claims else DEFAULT_CLAIMS
    try:
        refs = load_ref_sets(claims_paths, args.evidence, args.sources)
    except Exception as e:  # noqa: BLE001 — any registry read/parse failure is §13 fail-closed
        print(f"[FAIL closed] cannot read a referenced registry for resolution ({e})", file=sys.stderr)
        return 2

    paths = args.paths or [DEFAULT_CEA]
    code, all_findings = 0, []
    for path in paths:
        c, findings = validate_claim_evidence_file(path, refs)
        code = max(code, c)
        all_findings += findings
    for f in sorted(all_findings):
        print(f"  [finding] {f}", file=sys.stderr)
    if code == 0:
        print("OK — claim-evidence governance clean. (Coherent bookkeeping, NOT a truth certificate.)")
    return code


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""WP2.4 — type-specific claim INTEGRITY gate.

Schema (WP1.3 CLAIM_SCHEMA + _claim_extra) checks each claim's shape and its variant-required
fields; this adds the cross-record/cross-file rules a single-record check can't (Constitution §4,
DATA_MODEL §5/§14, IMPLEMENTATION_PLAN WP2.4):
  - R-CLM-1  claim id uniqueness across the UNION of baseline + live claim files (one namespace;
             the schema validates each file in isolation and can't see a cross-file dup);
  - R-CLM-2  INFERENCE `premise_claim_ids` each resolve to a known `clm-` (shape gives non-empty
             list only; the prefix + existence are unchecked at the schema layer);
  - R-CLM-5  an ACTIVE claim-evidence assessment on an ASSUMPTION claim is invalid (DATA_MODEL §4
             "Active claim-evidence assessments on assumptions are invalid"). WP2.4 is the SOLE
             owner (WP2.3b deliberately deferred this). ACTIVE = un-superseded leaf AND
             semantic_review.status != REJECTED (an assumption carries no evidence link at all).
             Fires only when claim_id RESOLVES to an ASSUMPTION — an unresolved claim_id stays the
             claim-evidence gate's finding (no double-report);
  - R-CLM-6  a FALSIFIABLE projection's `prediction_id` resolves to a known `prd-` in the
             prediction registry (cross-file; shape gives presence + prefix only);
  - R-CLM-8  a PROJECTION is never fact-grade: support_status != CORROBORATED (DATA_MODEL §5
             "Neither may be assigned fact support status"). The earned-support VALUE is WP2.5;
  - R-CLM-12 claim supersession integrity (no self-supersede / orphan / cycle; one active leaf)
             via the shared supersession helper, over the merged claim set.

DEFERRED — NOT enforced (by design):
  - premise ACYCLICITY and review_by/expires_at >= created_at ORDERING are NOT in the governing
    docs (Constitution §13: gate-driving rules must live in the oracle). Surfaced for ratification,
    not silently codified. `scenario_id` has no registry to resolve against (presence is schema-
    checked; no registry invented). The earned support VALUE → WP2.5; conflict → WP2.6; the
    freshness CLOCK (now()-relative) → WP2.7; cross-COMMIT in-place edits of REVIEWED claims →
    the reward-hack/git-range gate (WP2.2c family); high_impact recompute → WP2.2a; semantic
    displacement → the WP3.3 refuter.

Schema runs first per claims file. The claim-evidence + prediction registries are required to
resolve references — a missing/unreadable/duplicate-key one → exit 2 (§13 cannot-run). An empty
factbase → 0. Exit codes: 0 / 1 / 2.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling import
import supersession  # noqa: E402
import validate_schema as vs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLAIMS = [REPO_ROOT / "factbase" / "baseline" / "claims.yaml",
                  REPO_ROOT / "factbase" / "live" / "claims.yaml"]
DEFAULT_CEA = REPO_ROOT / "factbase" / "claim_evidence.yaml"
DEFAULT_PREDICTIONS = REPO_ROOT / "factbase" / "predictions.yaml"


def load_claims_union(paths):
    """Return (merged_records, dup_id_findings). Records preserve all entries across files so a
    cross-file duplicate id is detectable (the set of ids alone would hide it)."""
    merged, seen, dup = [], {}, []
    for p in paths:
        data = vs.load_yaml_strict(p) or {}
        for c in (data.get("claims") or []):
            if not isinstance(c, dict):
                continue
            merged.append(c)
            cid = c.get("id")
            if cid in seen:
                dup.append(f"duplicate id {cid!r} (appears in {seen[cid]} and {p.name})")
            else:
                seen[cid] = p.name
    return merged, sorted(dup)


def _ids_from(path, collection, field="id"):
    data = vs.load_yaml_strict(path) or {}
    return {r.get(field) for r in (data.get(collection) or []) if isinstance(r, dict)}


def check_claims_integrity(claims, clm_ids, clm_types, prd_ids, ceas) -> list[str]:
    """Cross-record/cross-file integrity findings for the schema-clean merged claim set."""
    findings = []

    for c in claims:
        cid, et = c.get("id"), c.get("epistemic_type")
        if et == "INFERENCE":
            for pid in (c.get("premise_claim_ids") or []):
                if not (isinstance(pid, str) and pid.startswith("clm-")):
                    findings.append(f"claim {cid!r} premise {pid!r} is not a clm- id")
                elif pid not in clm_ids:
                    findings.append(f"claim {cid!r} premise {pid!r} does not resolve to a known claim")
        if et == "PROJECTION":
            if c.get("projection_kind") == "FALSIFIABLE":
                pred = c.get("prediction_id")
                if pred not in prd_ids:
                    findings.append(f"claim {cid!r} prediction_id {pred!r} does not resolve to a known prediction")
            if c.get("support_status") == "CORROBORATED":
                findings.append(f"claim {cid!r} is a PROJECTION and may not carry fact-grade support_status CORROBORATED")

    # R-CLM-5: an ACTIVE claim-evidence assessment on an ASSUMPTION claim is invalid.
    # `superseded` must be PARTITION-scoped: only a SAME-(claim_id, artifact_id) edge deactivates a
    # cea (a cea chain is per claim-artifact pair, DATA_MODEL §4). A flat global set would let a
    # throwaway cross-pair `supersedes` pointer mask a genuinely-active assessment on an assumption.
    cea_by_id = {a.get("id"): a for a in ceas}
    cea_key = lambda a: (a.get("claim_id"), a.get("artifact_id"))  # noqa: E731
    superseded = {a["supersedes"] for a in ceas
                  if a.get("supersedes") in cea_by_id and cea_key(a) == cea_key(cea_by_id[a["supersedes"]])}
    for a in ceas:
        claim_id = a.get("claim_id")
        if clm_types.get(claim_id) != "ASSUMPTION":
            continue  # not an assumption (or claim_id unresolved -> the claim-evidence gate's finding)
        sr = a.get("semantic_review") if isinstance(a.get("semantic_review"), dict) else {}
        active = a.get("id") not in superseded and sr.get("status") != "REJECTED"
        if active:
            findings.append(f"claim-evidence assessment {a.get('id')!r} is active on ASSUMPTION claim "
                            f"{claim_id!r} — an assumption carries no evidence link (DATA_MODEL §4)")

    # R-CLM-12: claim supersession chain integrity (no partition — a chain is any component)
    findings += supersession.check_supersession(claims, label="claim")
    return sorted(findings)


def validate_claims(claims_paths, cea_path, predictions_path):
    """Return (exit_code, findings). Schema-first per claims file; integrity on the merged set."""
    schema_findings, code = [], 0
    for p in claims_paths:
        c, f = vs.validate_file(p)
        code = max(code, c)
        schema_findings += f
    if code != 0:
        return code, schema_findings  # don't run integrity on malformed records

    try:  # registries required for resolution -> fail closed on any read/parse error (§13)
        prd_ids = _ids_from(predictions_path, "predictions")
        cea_data = vs.load_yaml_strict(cea_path) or {}
        ceas = cea_data.get("claim_evidence_assessments") or []
    except Exception as e:  # noqa: BLE001
        return 2, [f"cannot read a referenced registry for resolution (fail closed): {e}"]

    merged, dup = load_claims_union(claims_paths)
    clm_ids = {c.get("id") for c in merged}
    clm_types = {c.get("id"): c.get("epistemic_type") for c in merged}
    findings = dup + check_claims_integrity(merged, clm_ids, clm_types, prd_ids, ceas)
    return (1 if findings else 0), findings


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP2.4 type-specific claim integrity gate")
    p.add_argument("paths", nargs="*", type=Path, help="claim files (default baseline+live)")
    p.add_argument("--claim-evidence", type=Path, default=DEFAULT_CEA)
    p.add_argument("--predictions", type=Path, default=DEFAULT_PREDICTIONS)
    args = p.parse_args(argv)
    claims_paths = args.paths or DEFAULT_CLAIMS
    code, findings = validate_claims(claims_paths, args.claim_evidence, args.predictions)
    for f in sorted(findings):
        print(f"  [finding] {f}", file=sys.stderr)
    if code == 0:
        print("OK — claim integrity clean. (Coherent bookkeeping, NOT a truth certificate.)")
    return code


if __name__ == "__main__":
    sys.exit(main())

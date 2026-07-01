#!/usr/bin/env python3
"""WP3.1 — context-pack integrity (the draft-mode context control, when a pack is referenced).

A context pack is the deterministic, hash-pinned snapshot of records selected to answer a
question. Integrity checks (beyond the closed schema, WP3.0):

  - every claim/assessment/artifact/observation/prediction ref resolves to a live record AND
    binds that record's current hash (a stale snapshot turns red);
  - pack_hash == record_hash(pack, exclude=pack_hash) (self-consistency);
  - if the citing manifest is supplied, manifest.context_pack_hash == pack.pack_hash (agreement);
  - token_budget > 0 (a non-positive budget is incoherent — deferred from WP3.0);
  - A4-PARTIAL: an `omitted_candidates` entry must, if it resolves to a live claim, match its declared
    reason — STALE / REVIEW_DUE against `freshness_status`, SUPERSEDED against `lifecycle`, and
    INELIGIBLE must not name a REVIEWED+CURRENT (selectable) claim — so a false omission cannot hide a
    current contrary claim. Full topic-completeness of the pack is a Phase-4 concern (disclosed).

Returns (exit_code, findings): 0 clean · 1 a finding in valid input. Schema validation runs FIRST
in the caller; `Live` is resolved only on a clean parse (§13).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import answer_layer as al  # noqa: E402
import validate_schema as vs  # noqa: E402


def validate_context_pack(pack: dict, live: al.Live, manifest_context_pack_hash: str | None = None):
    f = []
    budget = pack.get("token_budget")
    if isinstance(budget, int) and not isinstance(budget, bool) and budget <= 0:
        f.append(f"token_budget must be > 0 (got {budget})")
    f += al.check_ref_list(pack.get("claim_refs"), live.claims, "record_hash",
                           live.record_ref_hash, "claim")
    f += al.check_ref_list(pack.get("assessment_refs"), live.cea, "record_hash",
                           live.record_ref_hash, "assessment")
    f += al.check_ref_list(pack.get("artifact_refs"), live.evidence, "content_hash",
                           live.artifact_ref_hash, "artifact")
    f += al.check_ref_list(pack.get("observation_refs"), live.observations, "record_hash",
                           live.record_ref_hash, "observation")
    if pack.get("prediction_refs") is not None:
        f += al.check_ref_list(pack.get("prediction_refs"), live.predictions, "record_hash",
                               live.record_ref_hash, "prediction")
    if pack.get("pack_hash") != vs.record_hash(pack, exclude=("pack_hash",)):
        f.append("pack_hash is self-inconsistent (record_hash(pack, exclude=pack_hash) differs)")
    if manifest_context_pack_hash is not None and manifest_context_pack_hash != pack.get("pack_hash"):
        f.append(f"manifest context_pack_hash {manifest_context_pack_hash!r} does not match the "
                 f"pack's pack_hash {pack.get('pack_hash')!r}")
    for oc in pack.get("omitted_candidates") or []:
        if not isinstance(oc, dict):
            continue
        claim = live.claims.get(oc.get("id"))
        if claim is None:
            continue  # an omitted id need not resolve to a live record (e.g. TOKEN_BUDGET/REDUNDANT)
        reason, lc, fr = oc.get("reason"), claim.get("lifecycle"), claim.get("freshness_status")
        if reason == "STALE" and fr != "STALE":
            f.append(f"omitted_candidate {oc.get('id')!r}: reason STALE but the live claim's "
                     f"freshness_status is {fr!r} (false-omission)")
        elif reason == "REVIEW_DUE" and fr != "REVIEW_DUE":
            f.append(f"omitted_candidate {oc.get('id')!r}: reason REVIEW_DUE but the live claim's "
                     f"freshness_status is {fr!r} (false-omission)")
        elif reason == "SUPERSEDED" and lc != "SUPERSEDED":
            f.append(f"omitted_candidate {oc.get('id')!r}: reason SUPERSEDED but the live claim's "
                     f"lifecycle is {lc!r} (false-omission)")
        elif reason == "INELIGIBLE" and lc == "REVIEWED" and fr == "CURRENT":
            f.append(f"omitted_candidate {oc.get('id')!r}: reason INELIGIBLE but the live claim is "
                     f"REVIEWED+CURRENT — a selectable claim cannot be hidden as ineligible")
    return (1 if f else 0), sorted(f)

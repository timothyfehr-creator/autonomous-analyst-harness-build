"""Closed per-record schema definitions, registered with validate_schema.

Plain spec dicts (no imports) so validate_schema can load them without a circular import. Each
spec: prefix, required/optional field sets, enums, and types (id | ref:<prefix> | datetime |
number | integer). Unknown fields are rejected by the closed-schema check, so a free-text
reliability `note` on a source entity is prohibited simply by not being an allowed field.

Grows WP-by-WP: WP1.2 sources/groups/assessments; WP1.3 claims; WP1.4 evidence/claim_evidence;
WP1.5 predictions/events; WP1.6 observations/etc.
"""

import re

_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")  # mirrors validate_schema (no import → no cycle)

SOURCE_TYPES = {
    "GOVERNMENT", "MILITARY", "SECURITY_SERVICE", "INTERGOVERNMENTAL", "NEWSWIRE",
    "NEWS_OUTLET", "RESEARCH_INSTITUTE", "NGO", "DATA_PROVIDER", "SOCIAL_ACCOUNT", "OTHER",
}
RELIABILITY = {"A", "B", "C", "D", "E", "F", "UNASSESSED"}

SOURCE_SCHEMA = {
    "prefix": "src-",
    "required": {"id", "title", "source_type"},
    "optional": {"jurisdiction", "aliases", "canonical_home", "active_from", "active_to"},
    "enums": {"source_type": SOURCE_TYPES},
    "types": {"id": "id", "active_from": "datetime", "active_to": "datetime"},
}

GROUP_SCHEMA = {
    "prefix": "grp-",
    "required": {"id", "title", "citable", "member_ids"},
    "optional": set(),
    "enums": {"citable": {False}},  # non-citable groups only
    "types": {"id": "id"},
}

SOURCE_ASSESSMENT_SCHEMA = {
    "prefix": "sas-",
    "required": {"id", "source_id", "scope", "reliability", "sample_definition",
                 "sample_size", "rationale", "assessed_by", "assessed_at", "supersedes"},
    "optional": set(),
    "enums": {"reliability": RELIABILITY},
    "types": {"id": "id", "source_id": "ref:src-", "sample_size": "integer",
              "assessed_at": "datetime", "supersedes": "ref:sas-"},
}

# ---- claims (WP1.3): type-specific variants + multi-axis status + high_impact (V-P0-1 shape) ----
EPISTEMIC_TYPES = {"FACT", "INFERENCE", "ASSUMPTION", "PROJECTION"}
SUPPORT_STATUS = {"UNVERIFIED", "THIN", "SUPPORTED", "CORROBORATED"}
DISPUTE_STATUS = {"UNKNOWN", "UNCONTESTED", "CONTESTED"}
FRESHNESS_STATUS = {"NOT_APPLICABLE", "CURRENT", "REVIEW_DUE", "STALE"}
LIFECYCLE = {"CANDIDATE", "REVIEWED", "SUPERSEDED", "REJECTED"}
STABILITY = {"DURABLE", "APPEND_ONLY_HISTORY", "VOLATILE"}
PROJECTION_KIND = {"FALSIFIABLE", "SCENARIO"}


def _claim_extra(rec):
    """Variant-specific required fields + cross-field rules (Constitution §4–§5). Shape only."""
    f = []
    et = rec.get("epistemic_type")
    if et == "INFERENCE":
        prem = rec.get("premise_claim_ids")
        if not (isinstance(prem, list) and prem):
            f.append("INFERENCE requires a non-empty premise_claim_ids list")
        if not rec.get("reasoning"):
            f.append("INFERENCE requires reasoning")
    elif et == "ASSUMPTION":
        if not rec.get("rationale"):
            f.append("ASSUMPTION requires rationale")
        if "consequence_if_false" not in rec:
            f.append("ASSUMPTION requires consequence_if_false")
        if rec.get("support_status") != "UNVERIFIED":
            f.append("ASSUMPTION support_status must be UNVERIFIED (assumptions carry no evidence)")
    elif et == "PROJECTION":
        pk = rec.get("projection_kind")
        if pk is None:
            f.append("PROJECTION requires projection_kind")
        elif pk == "FALSIFIABLE" and not rec.get("prediction_id"):
            f.append("FALSIFIABLE projection requires prediction_id")
        elif pk == "SCENARIO" and not rec.get("scenario_id"):
            f.append("SCENARIO projection requires scenario_id")
    elif et == "FACT":
        if "temporal" not in rec:
            f.append("FACT requires temporal")
        stab = rec.get("stability")
        if stab == "DURABLE" and not rec.get("review_by"):
            f.append("DURABLE fact requires review_by")
        elif stab == "VOLATILE" and not (rec.get("expires_at") or rec.get("freshness_profile")):
            f.append("VOLATILE fact requires expires_at or a named freshness_profile")
        elif stab == "APPEND_ONLY_HISTORY" and not (
                isinstance(rec.get("temporal"), dict) and rec["temporal"].get("event_time")):
            f.append("APPEND_ONLY_HISTORY fact requires temporal.event_time")
    return sorted(f)


CLAIM_SCHEMA = {
    "prefix": "clm-",
    "required": {"id", "text", "epistemic_type", "support_status", "dispute_status",
                 "freshness_status", "lifecycle", "stability", "topics", "high_impact",
                 "created_at", "supersedes"},
    "optional": {"premise_claim_ids", "reasoning", "rationale", "consequence_if_false",
                 "projection_kind", "prediction_id", "scenario_id", "temporal", "review_by",
                 "expires_at", "freshness_profile"},
    "enums": {"epistemic_type": EPISTEMIC_TYPES, "support_status": SUPPORT_STATUS,
              "dispute_status": DISPUTE_STATUS, "freshness_status": FRESHNESS_STATUS,
              "lifecycle": LIFECYCLE, "stability": STABILITY, "projection_kind": PROJECTION_KIND},
    "types": {"id": "id", "created_at": "datetime", "supersedes": "ref:clm-",
              "high_impact": "boolean", "prediction_id": "ref:prd-"},
    "extra": _claim_extra,
}

# ---- evidence + claim-evidence assessment (WP1.4): + primary_evidence_kind (V-P1-4 shape) ----
ARTIFACT_TYPES = {"ARTICLE", "OFFICIAL_STATEMENT", "REPORT", "DATASET", "POST", "IMAGE",
                  "VIDEO", "AUDIO", "MAP", "DOCUMENT", "OTHER"}
STANCE = {"SUPPORTS", "REFUTES", "MIXED", "CONTEXT_ONLY"}
INFO_CREDIBILITY = {1, 2, 3, 4, 5, 6, "UNASSESSED"}
PRIMARY_EVIDENCE_KIND = {"FIRST_PARTY_ACTION_RECORD", "AUTHORITATIVE_DATASET",
                         "DIRECT_SENSOR_CAPTURE", "OFFICIAL_PRIMARY_DOCUMENT"}
TEMPORAL_SCOPE_KIND = {"TIMELESS", "AT_TIME", "AS_OF", "INTERVAL", "EVENT"}
SEMANTIC_REVIEW_STATUS = {"UNCHECKED", "CHECKED", "REJECTED"}

_SIGNED_URL_RE = re.compile(
    r"[?&](x-amz-signature|x-amz-credential|awsaccesskeyid|signature|expires|sig|token"
    r"|access_token|api_key|apikey|auth_token)=", re.I)


def _evidence_extra(rec):
    """A signed/mutable canonical_locator must be canonicalized or carry a snapshot_ref (§3)."""
    f = []
    loc = rec.get("canonical_locator")
    if isinstance(loc, str) and _SIGNED_URL_RE.search(loc) and not rec.get("snapshot_ref"):
        f.append("signed/mutable canonical_locator requires a snapshot_ref (or strip the auth params)")
    return sorted(f)


EVIDENCE_SCHEMA = {
    "prefix": "evd-",
    "required": {"id", "source_id", "artifact_type", "title", "canonical_locator",
                 "content_hash", "published_at", "retrieved_at"},
    "optional": {"snapshot_ref", "occurred_at", "language"},
    "enums": {"artifact_type": ARTIFACT_TYPES},
    "types": {"id": "id", "source_id": "ref:src-", "content_hash": "hash",
              "published_at": "datetime", "occurred_at": "datetime", "retrieved_at": "datetime"},
    "extra": _evidence_extra,
}


def _cea_extra(rec):
    """Non-empty locator/summary/origin/independence; a CHECKED review binds all three hashes (§6.1-6.2)."""
    f = []
    if not rec.get("support_locator"):
        f.append("assessment requires a non-empty support_locator")
    if not rec.get("support_summary"):
        f.append("assessment requires a non-empty support_summary")
    if not (isinstance(rec.get("origin_chain"), list) and rec.get("origin_chain")):
        f.append("assessment requires a non-empty origin_chain")
    if not rec.get("independence_group"):
        f.append("assessment requires an independence_group")
    ts = rec.get("temporal_scope")
    if not (isinstance(ts, dict) and ts.get("kind") in TEMPORAL_SCOPE_KIND):
        f.append("assessment requires a temporal_scope with a valid kind")
    sr = rec.get("semantic_review")
    if not isinstance(sr, dict):
        f.append("assessment requires a semantic_review block")
    else:
        status = sr.get("status")
        if status not in SEMANTIC_REVIEW_STATUS:
            f.append(f"semantic_review.status {status!r} invalid")
        if status == "CHECKED":
            for h in ("claim_content_hash", "artifact_hash", "relationship_input_hash"):
                if not sr.get(h):
                    f.append(f"CHECKED semantic_review requires {h}")
            for m in ("reviewer", "reviewed_at"):
                if not sr.get(m):
                    f.append(f"CHECKED semantic_review requires {m}")
    return sorted(f)


CLAIM_EVIDENCE_SCHEMA = {
    "prefix": "cea-",
    "required": {"id", "claim_id", "artifact_id", "support_locator", "support_summary",
                 "stance", "information_credibility", "temporal_scope", "origin_chain",
                 "independence_group", "semantic_review", "supersedes"},
    "optional": {"primary_evidence_kind"},
    "enums": {"stance": STANCE, "information_credibility": INFO_CREDIBILITY,
              "primary_evidence_kind": PRIMARY_EVIDENCE_KIND},
    "types": {"id": "id", "claim_id": "ref:clm-", "artifact_id": "ref:evd-",
              "supersedes": "ref:cea-"},
    "extra": _cea_extra,
}

# ---- predictions (WP1.5): ex-ante forecast registry (DATA_MODEL §7) ----
def _prediction_extra(rec):
    """Forecast sanity (shape): probabilities in [0,1]; resolution after the as-of time."""
    f = []
    for fld in ("probability", "benchmark_probability"):
        v = rec.get(fld)
        if isinstance(v, (int, float)) and not isinstance(v, bool) and not (0.0 <= v <= 1.0):
            f.append(f"{fld} must be within [0,1]")
    # Lexical compare is correct for the canonical fixed-width ISO-8601 UTC `Z` datetimes the
    # schema accepts; normalized instant comparison (fractional-second widths, tz) is Phase-2.
    a, r = rec.get("as_of"), rec.get("resolve_by")
    if isinstance(a, str) and isinstance(r, str) and r <= a:
        f.append("resolve_by must be after as_of")
    return sorted(f)


PREDICTION_SCHEMA = {
    "prefix": "prd-",
    "required": {"id", "question", "resolution_criterion", "as_of", "resolve_by", "probability",
                 "resolution_authority", "void_policy", "category", "dependence_cluster",
                 "benchmark_probability", "declared_data_source"},
    "optional": set(),
    "enums": {},
    "types": {"id": "id", "as_of": "datetime", "resolve_by": "datetime",
              "probability": "number", "benchmark_probability": "number",
              "resolution_authority": "ref:src-"},
    "extra": _prediction_extra,
}

# ---- append-only event logs (WP1.5): JSONL, no envelope; shape only (chain is Phase 2) ----
# Concrete event-type tokens specified in DATA_MODEL: LOCK (§7) and PROMOTE (§13). The remaining
# members are the README's per-log vocabularies normalized to imperative verbs to match those two
# anchors; only LOCK / PROMOTE variant *bodies* are documented, so only those are field-enforced.
PREDICTION_EVENT_TYPES = {"LOCK", "RESOLVE", "VOID", "DISPUTE", "CORRECT"}
BASELINE_EVENT_TYPES = {"PROMOTE", "REFRESH", "REJECT", "SUPERSEDE"}


def _prediction_event_extra(rec):
    """LOCK freezes the ex-ante record: it binds record_hash + an external anchor_ref (§7)."""
    f = []
    if rec.get("event_type") == "LOCK":
        for fld in ("record_hash", "anchor_ref"):
            if not rec.get(fld):
                f.append(f"LOCK event requires {fld}")
    return sorted(f)


PREDICTION_EVENT_SCHEMA = {
    "prefix": "evt-",
    "required": {"event_id", "event_type", "prediction_id", "recorded_at",
                 "previous_event_hash", "event_hash"},
    "optional": {"record_hash", "anchor_ref"},
    "enums": {"event_type": PREDICTION_EVENT_TYPES},
    "types": {"event_id": "id", "prediction_id": "ref:prd-", "recorded_at": "datetime",
              "previous_event_hash": "hash", "event_hash": "hash", "record_hash": "hash"},
    "extra": _prediction_event_extra,
}


def _baseline_event_extra(rec):
    """PROMOTE binds before/after record hashes + the supporting assessment/artifact hashes (§13)."""
    f = []
    if rec.get("event_type") == "PROMOTE":
        for fld in ("claim_content_hash", "before_record_hash", "after_record_hash", "review_hash"):
            if not rec.get(fld):
                f.append(f"PROMOTE event requires {fld}")
        for fld in ("assessment_hashes", "artifact_hashes"):
            v = rec.get(fld)
            if not isinstance(v, list):
                f.append(f"PROMOTE event requires {fld} as a list")
            else:
                for h in v:
                    if not (isinstance(h, str) and _HASH_RE.match(h)):
                        f.append(f"{fld} contains a non-hash entry: {h!r}")
    return sorted(f)


BASELINE_EVENT_SCHEMA = {
    "prefix": "evt-",
    "required": {"event_id", "event_type", "claim_id", "recorded_at",
                 "previous_event_hash", "event_hash"},
    "optional": {"claim_content_hash", "before_record_hash", "after_record_hash",
                 "assessment_hashes", "artifact_hashes", "review_hash"},
    "enums": {"event_type": BASELINE_EVENT_TYPES},
    "types": {"event_id": "id", "claim_id": "ref:clm-", "recorded_at": "datetime",
              "previous_event_hash": "hash", "event_hash": "hash", "claim_content_hash": "hash",
              "before_record_hash": "hash", "after_record_hash": "hash", "review_hash": "hash"},
    "extra": _baseline_event_extra,
}

COLLECTIONS = {
    "sources": SOURCE_SCHEMA,
    "groups": GROUP_SCHEMA,
    "source_assessments": SOURCE_ASSESSMENT_SCHEMA,
    "claims": CLAIM_SCHEMA,
    "evidence": EVIDENCE_SCHEMA,
    "claim_evidence_assessments": CLAIM_EVIDENCE_SCHEMA,
    "predictions": PREDICTION_SCHEMA,
}

# JSONL append-only event logs keyed by the log-file stem (substring-matched against filenames).
EVENT_LOGS = {
    "prediction_events": PREDICTION_EVENT_SCHEMA,
    "baseline_events": BASELINE_EVENT_SCHEMA,
}

"""Closed per-record schema definitions, registered with validate_schema.

Plain spec dicts (no imports) so validate_schema can load them without a circular import. Each
spec: prefix, required/optional field sets, enums, and types (id | ref:<prefix> | datetime |
number | integer). Unknown fields are rejected by the closed-schema check, so a free-text
reliability `note` on a source entity is prohibited simply by not being an allowed field.

Grows WP-by-WP: WP1.2 sources/groups/assessments; WP1.3 claims; WP1.4 evidence/claim_evidence;
WP1.5 predictions/events; WP1.6 observations/etc.
"""

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

COLLECTIONS = {
    "sources": SOURCE_SCHEMA,
    "groups": GROUP_SCHEMA,
    "source_assessments": SOURCE_ASSESSMENT_SCHEMA,
    "claims": CLAIM_SCHEMA,
}

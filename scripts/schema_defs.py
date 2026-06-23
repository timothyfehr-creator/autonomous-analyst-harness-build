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

COLLECTIONS = {
    "sources": SOURCE_SCHEMA,
    "groups": GROUP_SCHEMA,
    "source_assessments": SOURCE_ASSESSMENT_SCHEMA,
}

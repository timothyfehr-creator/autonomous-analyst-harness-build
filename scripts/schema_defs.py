"""Closed per-record schema definitions, registered with validate_schema.

Plain spec dicts (no imports) so validate_schema can load them without a circular import. Each
spec: prefix, required/optional field sets, enums, and types (id | ref:<prefix> | datetime |
number | integer). Unknown fields are rejected by the closed-schema check, so a free-text
reliability `note` on a source entity is prohibited simply by not being an allowed field.

Grows WP-by-WP: WP1.2 sources/groups/assessments; WP1.3 claims; WP1.4 evidence/claim_evidence;
WP1.5 predictions/events; WP1.6 observations/etc.
"""

import datetime as _dt
import pathlib
import re

import yaml as _yaml  # for loading the owner-editable unit_vocabulary config

_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")  # mirrors validate_schema (no import → no cycle)
_FRAC_RE = re.compile(r"\.(\d+)")


def iso_instant(s):
    """Parse an ISO-8601 date or UTC datetime to an aware datetime for ORDERING. Robust to the
    formats is_iso_datetime accepts — date-only (→ start-of-day UTC), trailing `Z`, and variable
    fractional-second widths — so a lexical `a < b` string compare (which mis-orders '2026-06-20'
    vs '2026-06-20T..' and '.5Z' vs '.50Z') is never used. Returns None if unparseable."""
    if not isinstance(s, str):
        return None
    t = s.strip().replace("Z", "+00:00")
    m = _FRAC_RE.search(t)
    if m:  # pad/truncate fractional seconds to 6 digits for fromisoformat strictness (<3.11)
        t = t[:m.start()] + "." + (m.group(1) + "000000")[:6] + t[m.end():]
    try:
        if "T" not in t:
            d = _dt.date.fromisoformat(t)
            return _dt.datetime(d.year, d.month, d.day, tzinfo=_dt.timezone.utc)
        dt = _dt.datetime.fromisoformat(t)
        return dt if dt.tzinfo else dt.replace(tzinfo=_dt.timezone.utc)
    except ValueError:
        return None

# ---- owner-editable unit vocabulary (Constitution §6.3, V-P1-5) ----
# Loaded from config/unit_vocabulary.yaml (data, not code). Missing/unreadable → empty, so numeric
# observations fail closed (their unit can't be found) — the safe direction.
DIMENSIONAL_CLASSES = {
    "FLOW_VOLUME_RATE", "MASS_RATE", "MASS", "VOLUME", "LENGTH", "AREA",
    "COUNT_RATE", "COUNT", "DIMENSIONLESS", "DURATION",
}
_UNIT_VOCAB_PATH = pathlib.Path(__file__).resolve().parent.parent / "config" / "unit_vocabulary.yaml"


def _load_unit_vocabulary():
    """unit token -> dimensional class, from the config registry. Empty on any read error."""
    try:
        doc = _yaml.safe_load(_UNIT_VOCAB_PATH.read_text(encoding="utf-8")) or {}
    except OSError:
        return {}
    entries = doc.get("unit_vocabulary", [])
    if not isinstance(entries, list):
        return {}
    return {e["unit"]: e.get("dimensional_class")
            for e in entries if isinstance(e, dict) and "unit" in e}


UNIT_VOCABULARY = _load_unit_vocabulary()

# The config file is itself a self-validating registry (run validate_schema on it):
UNIT_VOCAB_ENTRY_SCHEMA = {
    "prefix": "",  # entries are unit tokens, not prefixed ids
    "required": {"unit", "dimensional_class"},
    "optional": set(),
    "enums": {"dimensional_class": DIMENSIONAL_CLASSES},
    "types": {},
}

# ---- owner-editable high_impact trigger tokens (Constitution §10 / V-P0-1; oracle data per §13) ----
# Same data-not-code pattern as the unit vocabulary. The WP2.2a recompute gate treats an empty /
# unreadable trigger set as CANNOT-RUN (exit 2, §13 empty-rule-set) — never as "no claims trigger".
_HI_TRIGGERS_PATH = pathlib.Path(__file__).resolve().parent.parent / "config" / "high_impact_triggers.yaml"


def _load_high_impact_triggers():
    """Raw trigger token list (canonical tokens + alias spellings). Empty on any read error; the
    gate, not the loader, enforces the §13 empty-rule-set → exit 2 obligation."""
    try:
        doc = _yaml.safe_load(_HI_TRIGGERS_PATH.read_text(encoding="utf-8")) or {}
    except OSError:
        return []
    entries = doc.get("high_impact_triggers", [])
    if not isinstance(entries, list):
        return []
    return [e["token"] for e in entries if isinstance(e, dict) and "token" in e]


HIGH_IMPACT_TRIGGER_TOKENS = _load_high_impact_triggers()

HIGH_IMPACT_TRIGGER_SCHEMA = {
    "prefix": "",  # entries are topic tokens, not prefixed ids
    "required": {"token"},
    "optional": {"alias_of"},
    "enums": {},
    "types": {},
}

SOURCE_TYPES = {
    "GOVERNMENT", "MILITARY", "SECURITY_SERVICE", "INTERGOVERNMENTAL", "NEWSWIRE",
    "NEWS_OUTLET", "RESEARCH_INSTITUTE", "NGO", "DATA_PROVIDER", "SOCIAL_ACCOUNT",
    "REFERENCE", "OTHER",  # REFERENCE = encyclopedia/reference work (e.g. Wikipedia) — tertiary
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
# Reviewer-assigned high-impact CATEGORY (FR-2 / R2-P0-2). The AUTHORITATIVE high-impact signal:
# a non-NONE category forces `high_impact: true` regardless of word-list coverage, and switches on
# the refuter's high-impact contest (§10). The widened trigger word-list is only a CANDIDATE
# detector that forces a reviewer to assign this; it is not relied on for completeness.
IMPACT_CATEGORY = {"CASUALTIES", "ATTRIBUTION", "TERRITORIAL_CONTROL", "MILITARY_CAPABILITY", "NONE"}


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
    # high_impact is the gate-recomputed V-P0-1 boolean — it may not be null/unset (the general
    # "null is a valid unset" rule does not apply; a null would slip the recompute gate, §10).
    if "high_impact" in rec and rec.get("high_impact") is None:
        f.append("high_impact may not be null — it is the gate-recomputed V-P0-1 boolean (§10)")
    if et == "FACT":  # separate `if` (was `elif`): equivalent — a claim has one epistemic_type
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
                 "expires_at", "freshness_profile", "impact_category"},
    "enums": {"epistemic_type": EPISTEMIC_TYPES, "support_status": SUPPORT_STATUS,
              "dispute_status": DISPUTE_STATUS, "freshness_status": FRESHNESS_STATUS,
              "lifecycle": LIFECYCLE, "stability": STABILITY, "projection_kind": PROJECTION_KIND,
              "impact_category": IMPACT_CATEGORY},
    "types": {"id": "id", "created_at": "datetime", "supersedes": "ref:clm-",
              "high_impact": "boolean", "prediction_id": "ref:prd-"},
    "extra": _claim_extra,
}

# ---- claim-CONTENT hash exclusion set (WP3.0, DATA_MODEL §4) ----
# A marker / semantic-review binds the claim's CONTENT hash, not its full record hash, so that
# re-reviewing or superseding a claim (which mutates these fields) does NOT silently break every
# prior answer that cited it. Everything a review / refresh / supersession touches is EXCLUDED;
# the semantic content (text, epistemic_type, topics, high_impact, stability, temporal,
# premise/reasoning/rationale/projection legs, id) stays IN. `high_impact` and `impact_category`
# are deliberately IN: a false→true flip or a re-categorization SHOULD break a binding and force
# re-review (§10, FR-2). claim_content_hash =
# validate_schema.record_hash(claim, exclude=CLAIM_CONTENT_EXCLUDE). Ratified into DATA_MODEL §4
# (2026-06-24, the exact 9-field set below); code-locked by a frozen test.
CLAIM_CONTENT_EXCLUDE = frozenset({
    "lifecycle", "support_status", "dispute_status", "freshness_status",
    "created_at", "supersedes", "review_by", "expires_at", "freshness_profile",
})

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
    "optional": {"primary_evidence_kind", "corroboration_rating_id"},
    "enums": {"stance": STANCE, "information_credibility": INFO_CREDIBILITY,
              "primary_evidence_kind": PRIMARY_EVIDENCE_KIND},
    "types": {"id": "id", "claim_id": "ref:clm-", "artifact_id": "ref:evd-",
              "supersedes": "ref:cea-", "corroboration_rating_id": "ref:sas-"},
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
    a, r = iso_instant(rec.get("as_of")), iso_instant(rec.get("resolve_by"))
    if a is not None and r is not None and r <= a:
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

# ---- structured observations (WP1.6): typed chartable values + V-P1-5 schema half (§6, §6.3) ----
VALUE_TYPES = {"NUMBER", "INTEGER", "CATEGORY", "BOOLEAN", "INTERVAL"}
RECORD_LIFECYCLE = {"ACTIVE", "SUPERSEDED"}  # §6/§12 show ACTIVE + supersession; REJECTED not used here


def _observation_extra(rec):
    """Shape + V-P1-5 schema half. Numeric obs bind source_value/source_unit + a vocabulary unit and
    must DECLARE a transformation for any unit/denominator recast. The transformation's CORRECTNESS
    and the dimensional-class check (the A5 kill) are WP2.8 integrity, not here."""
    f = []
    ceas = rec.get("claim_evidence_assessment_ids")
    if not (isinstance(ceas, list) and ceas):
        f.append("observation requires a non-empty claim_evidence_assessment_ids list")
    elif not all(isinstance(x, str) and x.startswith("cea-") for x in ceas):
        f.append("claim_evidence_assessment_ids must all be cea- ids")
    ex = rec.get("extraction")
    if not isinstance(ex, dict):
        f.append("observation requires an extraction block")
    else:
        for k in ("method", "extractor", "extracted_at", "source_locator_hash"):
            if not ex.get(k):
                f.append(f"extraction requires {k}")
        slh = ex.get("source_locator_hash")
        if slh and not _HASH_RE.match(str(slh)):
            f.append("extraction.source_locator_hash must be sha256:<64 hex>")
    ts = rec.get("temporal_scope")
    if not (isinstance(ts, dict) and ts.get("kind") in TEMPORAL_SCOPE_KIND):
        f.append("observation requires a temporal_scope with a valid kind")
    df = rec.get("derived_from")
    df_list = df if isinstance(df, list) else []
    if not isinstance(df, list):
        f.append("derived_from must be a list (possibly empty)")
    elif not all(isinstance(x, str) and x.startswith("obs-") for x in df):
        f.append("derived_from entries must be obs- ids")
    vt = rec.get("value_type")
    if vt in ("NUMBER", "INTEGER"):
        sv = rec.get("source_value")
        if isinstance(sv, bool) or not isinstance(sv, (int, float)):
            f.append("numeric observation requires a numeric source_value")
        su, un = rec.get("source_unit"), rec.get("unit")
        if su not in UNIT_VOCABULARY:
            f.append(f"source_unit {su!r} not in unit_vocabulary")
        if un not in UNIT_VOCABULARY:
            f.append(f"unit {un!r} not in unit_vocabulary")
        if su in UNIT_VOCABULARY and un in UNIT_VOCABULARY and su != un and not rec.get("transformation"):
            f.append("a unit differing from source_unit requires a declared transformation")
        if rec.get("denominator") is not None and not (rec.get("transformation") and df_list):
            f.append("a denominator (share/rate) requires a transformation and a non-empty derived_from")
        v = rec.get("value")
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            f.append("numeric observation value must be numeric")
    elif vt == "CATEGORY" and rec.get("unit") is not None:
        f.append("CATEGORY observation unit must be null")
    return sorted(f)


OBSERVATION_SCHEMA = {
    "prefix": "obs-",
    "required": {"id", "claim_id", "claim_evidence_assessment_ids", "value_type", "value", "unit",
                 "denominator", "basis", "temporal_scope", "extraction", "derived_from",
                 "transformation", "lifecycle", "supersedes"},
    "optional": {"geography_id", "uncertainty", "source_value", "source_unit"},
    "enums": {"value_type": VALUE_TYPES, "lifecycle": RECORD_LIFECYCLE},
    "types": {"id": "id", "claim_id": "ref:clm-", "supersedes": "ref:obs-",
              "geography_id": "ref:geo-"},
    "extra": _observation_extra,
}

# ---- geography records (WP1.6): real geometry by reference + hash + provenance (§12) ----
# geometry_type = GeoJSON geometries (doc shows POINT); spatial_semantics = §12's enumeration.
GEOMETRY_TYPES = {"POINT", "LINESTRING", "POLYGON", "MULTIPOINT", "MULTILINESTRING",
                  "MULTIPOLYGON", "GEOMETRYCOLLECTION"}
SPATIAL_SEMANTICS = {"EVENT_LOCATION", "STRUCTURE_CENTROID", "ROUTE_CENTERLINE",
                     "ADMIN_BOUNDARY", "CONTROL_AREA", "OTHER"}


def _geography_extra(rec):
    f = []
    ceas = rec.get("claim_evidence_assessment_ids")
    if not (isinstance(ceas, list) and ceas):
        f.append("geography requires a non-empty claim_evidence_assessment_ids list")
    elif not all(isinstance(x, str) and x.startswith("cea-") for x in ceas):
        f.append("claim_evidence_assessment_ids must all be cea- ids")
    crs = rec.get("crs")
    if not (isinstance(crs, str) and crs.startswith("EPSG:")):
        f.append("crs must be an EPSG code (e.g. EPSG:4326)")
    if not rec.get("geometry_ref"):
        f.append("geography requires a geometry_ref")
    return sorted(f)


GEOGRAPHY_SCHEMA = {
    "prefix": "geo-",
    "required": {"id", "title", "geometry_type", "spatial_semantics", "crs", "geometry_ref",
                 "geometry_hash", "geometry_claim_id", "claim_evidence_assessment_ids",
                 "valid_from", "valid_to", "lifecycle", "supersedes"},
    "optional": set(),
    "enums": {"geometry_type": GEOMETRY_TYPES, "spatial_semantics": SPATIAL_SEMANTICS,
              "lifecycle": RECORD_LIFECYCLE},
    "types": {"id": "id", "geometry_hash": "hash", "geometry_claim_id": "ref:clm-",
              "supersedes": "ref:geo-", "valid_from": "datetime", "valid_to": "datetime"},
    "extra": _geography_extra,
}

# ---- answer/output layer (WP1.6): analysis manifest + refuter + visual (§9–§11) ----
# Shape only: hash-bound ref entries, markers, verdict records. The cross-record RESOLUTION
# (refuter set-equality coverage vs manifest, marker↔answer agreement, hash matching) is Phase-3.
ANALYSIS_LIFECYCLE = {"DRAFT", "ANSWER"}
REQUIRED_REFUTER_CLASS = {"HUMAN_OR_DIFFERENT_MODEL"}  # only documented token (§9); expand if specified
REVIEWER_CLASS = {"SAME_MODEL_FRESH_CONTEXT", "DIFFERENT_MODEL", "HUMAN", "MIXED"}  # §-independence
VERDICT = {"SURVIVES", "REVISE", "DOWNGRADE", "REJECT"}  # §10 explicit
CHECK_RESULT = {"PASS", "FAIL", "NOT_APPLICABLE"}        # PASS/NOT_APPLICABLE shown; FAIL is the third
VISUAL_TYPE = {"CHART", "TIMELINE", "MAP", "SCHEMATIC"}  # §11 explicit


def _check_ref_list(value, id_prefix, hash_field, label):
    """A hash-bound reference list: each entry is exactly {id: <prefix>id, <hash_field>: sha256}."""
    if not isinstance(value, list):
        return [f"{label} must be a list"]
    f = []
    for i, e in enumerate(value):
        if not isinstance(e, dict):
            f.append(f"{label}[{i}] must be a mapping with id + {hash_field}"); continue
        eid = e.get("id")
        if not (isinstance(eid, str) and eid.startswith(id_prefix)):
            f.append(f"{label}[{i}].id must be a {id_prefix} id")
        h = e.get(hash_field)
        if not (isinstance(h, str) and _HASH_RE.match(h)):
            f.append(f"{label}[{i}].{hash_field} must be sha256:<64 hex>")
        unexpected = set(e) - {"id", hash_field}
        if unexpected:
            f.append(f"{label}[{i}] has unexpected keys {sorted(unexpected)}")
    return f


def _analysis_extra(rec):
    f = []
    markers = rec.get("claim_markers")
    if not isinstance(markers, dict):
        f.append("claim_markers must be a mapping of marker -> {claim_id, claim_hash}")
    else:
        for mk, mv in sorted(markers.items()):
            if not isinstance(mv, dict):
                f.append(f"claim_marker {mk!r} must be a mapping"); continue
            if not (isinstance(mv.get("claim_id"), str) and mv["claim_id"].startswith("clm-")):
                f.append(f"claim_marker {mk!r}.claim_id must be a clm- id")
            if not (isinstance(mv.get("claim_hash"), str) and _HASH_RE.match(mv.get("claim_hash", ""))):
                f.append(f"claim_marker {mk!r}.claim_hash must be sha256:<64 hex>")
            unexpected = set(mv) - {"claim_id", "claim_hash"}
            if unexpected:
                f.append(f"claim_marker {mk!r} has unexpected keys {sorted(unexpected)}")
    f += _check_ref_list(rec.get("claim_evidence_assessment_refs"), "cea-", "record_hash",
                         "claim_evidence_assessment_refs")
    f += _check_ref_list(rec.get("artifact_refs"), "evd-", "content_hash", "artifact_refs")
    f += _check_ref_list(rec.get("observation_refs"), "obs-", "record_hash", "observation_refs")
    f += _check_ref_list(rec.get("prediction_refs"), "prd-", "record_hash", "prediction_refs")
    f += _check_ref_list(rec.get("visual_refs"), "vis-", "record_hash", "visual_refs")
    # WP3.0: optional hash-pinned allowlist of sentences declared non-load-bearing (the A7
    # answer-mode escape, WP3.2/3.4). Each entry is a sha256 of a normalized sentence; the refuter
    # must echo the exact set (`exemptions_reviewed`), so clearing one costs a review.
    exempt = rec.get("narrative_exemptions")
    if exempt is not None:
        if not isinstance(exempt, list):
            f.append("narrative_exemptions must be a list of sha256 sentence hashes")
        else:
            for i, h in enumerate(exempt):
                if not (isinstance(h, str) and _HASH_RE.match(h)):
                    f.append(f"narrative_exemptions[{i}] must be sha256:<64 hex>")
    # output_path must be a repo-relative path with no traversal — a committed answer lives at a
    # known, reviewable location under outputs/, never an absolute path or one escaping via `..`.
    op = rec.get("output_path")
    if isinstance(op, str) and (op.startswith("/") or op.startswith("~") or ".." in op.split("/")):
        f.append(f"output_path {op!r} must be repo-relative without '..' traversal")
    return sorted(f)


ANALYSIS_SCHEMA = {
    "prefix": "ana-",
    "required": {"id", "lifecycle", "question", "context_pack_id", "context_pack_hash",
                 "output_path", "output_hash", "claim_markers", "claim_evidence_assessment_refs",
                 "artifact_refs", "observation_refs", "prediction_refs", "visual_refs",
                 "required_refuter_class", "manifest_hash"},
    "optional": {"narrative_exemptions"},
    "enums": {"lifecycle": ANALYSIS_LIFECYCLE, "required_refuter_class": REQUIRED_REFUTER_CLASS},
    "types": {"id": "id", "context_pack_id": "ref:ctx-", "context_pack_hash": "hash",
              "output_hash": "hash", "manifest_hash": "hash"},
    "extra": _analysis_extra,
}


def _refuter_extra(rec):
    f = []
    for fld in ("reviewed_claim_ids", "reviewed_assessment_ids",
                "alternative_hypotheses", "disconfirming_searches", "unresolved_gaps"):
        if not isinstance(rec.get(fld), list):
            f.append(f"{fld} must be a list")
    verds = rec.get("verdicts")
    if not (isinstance(verds, list) and verds):
        f.append("refuter requires a non-empty verdicts list")
    else:
        for i, vd in enumerate(verds):
            if not isinstance(vd, dict):
                f.append(f"verdicts[{i}] must be a mapping"); continue
            if not (isinstance(vd.get("claim_id"), str) and vd["claim_id"].startswith("clm-")):
                f.append(f"verdicts[{i}].claim_id must be a clm- id")
            if vd.get("verdict") not in VERDICT:
                f.append(f"verdicts[{i}].verdict {vd.get('verdict')!r} not in {sorted(VERDICT)}")
            for ck in ("displacement_check", "independence_check", "freshness_check",
                       "observation_check", "reasoning_check"):
                if vd.get(ck) not in CHECK_RESULT:
                    f.append(f"verdicts[{i}].{ck} must be PASS/FAIL/NOT_APPLICABLE")
            # WP3.0: optional per-verdict high_impact contest field (V-P0-1 refuter half, §10). If
            # present it must be a real boolean — the WP3.3 gate requires it true when the gate
            # computes the claim high-impact and the stored value is not true.
            if "high_impact" in vd and not isinstance(vd.get("high_impact"), bool):
                f.append(f"verdicts[{i}].high_impact must be a boolean if present")
            unexpected = set(vd) - {"claim_id", "verdict", "displacement_check", "independence_check",
                                    "freshness_check", "observation_check", "reasoning_check",
                                    "high_impact", "notes"}
            if unexpected:
                f.append(f"verdicts[{i}] has unexpected keys {sorted(unexpected)}")
    exr = rec.get("exemptions_reviewed")
    if exr is not None:
        if not isinstance(exr, list):
            f.append("exemptions_reviewed must be a list of sha256 sentence hashes")
        else:
            for i, h in enumerate(exr):
                if not (isinstance(h, str) and _HASH_RE.match(h)):
                    f.append(f"exemptions_reviewed[{i}] must be sha256:<64 hex>")
    return sorted(f)


REFUTER_SCHEMA = {
    "prefix": "ref-",
    "required": {"id", "analysis_id", "manifest_hash", "output_hash", "reviewer_class", "reviewer",
                 "reviewed_at", "reviewed_claim_ids", "reviewed_assessment_ids", "verdicts",
                 "alternative_hypotheses", "disconfirming_searches", "unresolved_gaps"},
    "optional": {"exemptions_reviewed"},
    "enums": {"reviewer_class": REVIEWER_CLASS},
    "types": {"id": "id", "analysis_id": "ref:ana-", "manifest_hash": "hash", "output_hash": "hash",
              "reviewed_at": "datetime"},
    "extra": _refuter_extra,
}


def _visual_extra(rec):
    f = []
    for fld, pref in (("input_claim_refs", "clm-"),
                      ("input_claim_evidence_assessment_refs", "cea-"),
                      ("input_observation_refs", "obs-"),
                      ("input_prediction_refs", "prd-"),
                      ("input_geography_refs", "geo-")):
        f += _check_ref_list(rec.get(fld), pref, "record_hash", fld)
    if not isinstance(rec.get("data_bindings"), dict):
        f.append("data_bindings must be a mapping")
    if not isinstance(rec.get("filters"), list):
        f.append("filters must be a list")
    vt = rec.get("visual_type")
    if vt == "CHART" and not (isinstance(rec.get("input_observation_refs"), list) and rec.get("input_observation_refs")):
        f.append("a CHART requires non-empty input_observation_refs (charts consume observations)")
    if vt == "MAP" and not (isinstance(rec.get("input_geography_refs"), list) and rec.get("input_geography_refs")):
        f.append("a MAP requires non-empty input_geography_refs (maps consume geography ids)")
    return sorted(f)


VISUAL_SCHEMA = {
    "prefix": "vis-",
    "required": {"id", "visual_type", "title", "as_of", "input_claim_refs",
                 "input_claim_evidence_assessment_refs", "input_observation_refs",
                 "input_prediction_refs", "input_geography_refs", "data_bindings", "transformation",
                 "filters", "aggregation", "missing_data_policy", "output_path", "renderer",
                 "renderer_version", "spec_hash"},
    "optional": set(),
    "enums": {"visual_type": VISUAL_TYPE},
    "types": {"id": "id", "as_of": "datetime", "spec_hash": "hash"},
    "extra": _visual_extra,
}

# ---- context pack (WP3.0; DATA_MODEL §8 + EXAMPLE_WORKFLOW §9) ----
# A deterministic snapshot of the records selected to answer a question, hash-pinned. Closed
# `omitted_candidates.reason` enum so "token limits cannot masquerade as consensus" (§8): a dropped
# claim must say WHY in an auditable vocabulary, not free text.
OMITTED_REASON = {"STALE", "SUPERSEDED", "TOKEN_BUDGET", "REDUNDANT", "CONTESTED", "OUT_OF_SCOPE"}


def _context_pack_extra(rec):
    f = []
    if not isinstance(rec.get("topics"), list):
        f.append("topics must be a list")
    for fld in ("query", "generator_version", "selection_policy"):
        if not isinstance(rec.get(fld), str) or not rec.get(fld):
            f.append(f"{fld} must be a non-empty string")
    f += _check_ref_list(rec.get("claim_refs"), "clm-", "record_hash", "claim_refs")
    f += _check_ref_list(rec.get("assessment_refs"), "cea-", "record_hash", "assessment_refs")
    f += _check_ref_list(rec.get("artifact_refs"), "evd-", "content_hash", "artifact_refs")
    f += _check_ref_list(rec.get("observation_refs"), "obs-", "record_hash", "observation_refs")
    if rec.get("prediction_refs") is not None:
        f += _check_ref_list(rec.get("prediction_refs"), "prd-", "record_hash", "prediction_refs")
    omitted = rec.get("omitted_candidates")
    if not isinstance(omitted, list):
        f.append("omitted_candidates must be a list")
    else:
        for i, e in enumerate(omitted):
            if not isinstance(e, dict):
                f.append(f"omitted_candidates[{i}] must be a mapping with id + reason"); continue
            if not isinstance(e.get("id"), str) or not e.get("id"):
                f.append(f"omitted_candidates[{i}].id must be a non-empty string")
            if e.get("reason") not in OMITTED_REASON:
                f.append(f"omitted_candidates[{i}].reason {e.get('reason')!r} not in {sorted(OMITTED_REASON)}")
            if set(e) - {"id", "reason"}:
                f.append(f"omitted_candidates[{i}] has unexpected keys {sorted(set(e) - {'id', 'reason'})}")
    return sorted(f)


CONTEXT_PACK_SCHEMA = {
    "prefix": "ctx-",
    "required": {"id", "query", "topics", "generated_at", "generator_version", "selection_policy",
                 "token_budget", "claim_refs", "assessment_refs", "artifact_refs",
                 "observation_refs", "omitted_candidates", "pack_hash"},
    "optional": {"prediction_refs"},
    "enums": {},
    "types": {"id": "id", "generated_at": "datetime", "token_budget": "integer", "pack_hash": "hash"},
    "extra": _context_pack_extra,
}

COLLECTIONS = {
    "sources": SOURCE_SCHEMA,
    "groups": GROUP_SCHEMA,
    "source_assessments": SOURCE_ASSESSMENT_SCHEMA,
    "claims": CLAIM_SCHEMA,
    "evidence": EVIDENCE_SCHEMA,
    "claim_evidence_assessments": CLAIM_EVIDENCE_SCHEMA,
    "predictions": PREDICTION_SCHEMA,
    "observations": OBSERVATION_SCHEMA,
    "geography": GEOGRAPHY_SCHEMA,
    "unit_vocabulary": UNIT_VOCAB_ENTRY_SCHEMA,
    "context_packs": CONTEXT_PACK_SCHEMA,
    "analyses": ANALYSIS_SCHEMA,
    "refuters": REFUTER_SCHEMA,
    "visuals": VISUAL_SCHEMA,
    "high_impact_triggers": HIGH_IMPACT_TRIGGER_SCHEMA,
}

# JSONL append-only event logs keyed by the log-file stem (substring-matched against filenames).
EVENT_LOGS = {
    "prediction_events": PREDICTION_EVENT_SCHEMA,
    "baseline_events": BASELINE_EVENT_SCHEMA,
}

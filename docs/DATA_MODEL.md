# DATA MODEL — Analyst Harness v2

This document is the normative shape of the records named in the constitution and plan.
The implementation uses closed schemas: unknown fields fail rather than quietly becoming
future archaeology.

IDs are globally unique, lower-case, and prefixed by record type:

| Record | Prefix |
|---|---|
| source entity | `src-` |
| source group | `grp-` |
| source assessment | `sas-` |
| evidence artifact | `evd-` |
| claim | `clm-` |
| claim-evidence assessment | `cea-` |
| observation | `obs-` |
| prediction | `prd-` |
| context pack | `ctx-` |
| analysis | `ana-` |
| refuter artifact | `ref-` |
| geography record | `geo-` |
| visual specification | `vis-` |
| maintenance event | `evt-` |

## Envelope convention

Every YAML registry has one root version and one named collection:

```yaml
schema_version: "2.0"
sources: []
```

Per-record `schema_version` fields are prohibited. A file contains one schema version;
mixed-version repositories are accepted only inside an explicit migration operation.

Dates use ISO 8601. Timestamps use UTC with `Z`. Hashes are `sha256:<hex>`. All enums are
closed. Empty collections are valid seed state; a production gate must still fail closed
when it expected records and found none.

Canonical hashes are calculated from normalized UTF-8 JSON with sorted keys and without
fields explicitly identified as mutable state or computed output. The implementation must
publish the exact canonicalization rules before any hash is relied upon.

> **Hash conventions (§4, ratified 2026-06-24; code-locked by frozen tests since Phase 3).**
> - **Claim-CONTENT hash** (what a manifest marker / semantic-review binds): `record_hash(claim)`
>   with `CLAIM_CONTENT_EXCLUDE` removed, so re-review / refresh / supersession does NOT break a
>   prior binding. The excluded set is exactly: `lifecycle`, `support_status`, `dispute_status`,
>   `freshness_status`, `created_at`, `supersedes`, `review_by`, `expires_at`, `freshness_profile`.
>   Everything else stays IN — including `high_impact` (a false→true flip *should* break a binding
>   and force re-review, §10) and `temporal`.
> - **Record self-hashes** (`pack_hash`, `manifest_hash`, `spec_hash`): `record_hash(record)` with
>   the self-hash field itself excluded.
> - **Output-text hash** (`output_hash`, the analysis/refuter binding to the answer prose): the
>   sha256 of the RAW UTF-8 file bytes, **with NO canonicalization** — answer prose is not a record,
>   and canonicalizing it would normalize away author-meaningful formatting. This is the one
>   deliberate exception to the normalized-JSON rule above.

> **Phase-1 gate fixes (applied 2026-06-22, per the updated Constitution).** The schemas below
> gain these fields when their Phase-1 WP builds them — the binding rule lives in the
> Constitution; this records the field shapes:
> - claim-evidence assessment: `primary_evidence_kind` (closed enum; Constitution §6.1a, V-P1-4).
> - claim: `high_impact` becomes a **computed** field, recomputed on validation (§10, V-P0-1).
> - observation: `unit` drawn from a closed `unit_vocabulary` + `source_value`/`source_unit`
>   and a checkable `transformation`/`derived_from` for any unit/denominator change (§6.3, V-P1-5).
> - support gate: a credibility floor and the Tier-1→`SUPPORTED` cap (§6.1b/§6.6, V-P1-10/F3).

## 1. Source registry

Source entities are neutral identities. Reliability does not live here.

```yaml
schema_version: "2.0"
sources:
  - id: src-example-wire
    title: Example Wire Service
    source_type: NEWSWIRE
    jurisdiction: GLOBAL
    aliases: [ExampleWire]
    canonical_home: https://example.invalid/
    active_from: "2000-01-01"
    active_to: null

groups:
  - id: grp-example-aggregators
    title: Example social aggregators
    citable: false
    member_ids: [src-example-account]
```

Required source fields:

- `id`, `title`, `source_type`;
- optional `jurisdiction`, `aliases`, `canonical_home`, `active_from`, `active_to`.

`source_type` is one of:

```text
GOVERNMENT
MILITARY
SECURITY_SERVICE
INTERGOVERNMENTAL
NEWSWIRE
NEWS_OUTLET
RESEARCH_INSTITUTE
NGO
DATA_PROVIDER
SOCIAL_ACCOUNT
REFERENCE
OTHER
```

Groups are taxonomy only and must have `citable: false`. A group ID cannot appear where a
source entity is required.

## 2. Source-assessment log

Source assessments are append-only, scoped judgments. The current assessment is the
active leaf in a supersession chain; absence means `UNASSESSED`.

```yaml
schema_version: "2.0"
source_assessments:
  - id: sas-example-wire-energy-2026q2
    source_id: src-example-wire
    scope: energy-flow reporting in 2025-2026
    reliability: B
    sample_definition: 20 reports checked against later primary data
    sample_size: 20
    rationale: Strong attribution; two material corrections in sample.
    assessed_by: human:tim
    assessed_at: "2026-06-22"
    supersedes: null
```

Required fields: `id`, `source_id`, `scope`, `reliability`, `sample_definition`,
`sample_size`, `rationale`, `assessed_by`, `assessed_at`, `supersedes`.

`reliability ∈ {A,B,C,D,E,F,UNASSESSED}`. In-place edits and deletions are prohibited once
an assessment is committed; correction creates a superseding record.

## 3. Evidence-artifact registry

An artifact is an exact retrieved object, not a publisher name.

```yaml
schema_version: "2.0"
evidence:
  - id: evd-example-report-20260620
    source_id: src-example-wire
    artifact_type: ARTICLE
    title: Example report title
    canonical_locator: https://example.invalid/report/123
    snapshot_ref: snapshots/evd-example-report-20260620.html
    content_hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
    published_at: "2026-06-20T08:30:00Z"
    occurred_at: null
    retrieved_at: "2026-06-20T10:00:00Z"
    language: en
```

Required fields: `id`, `source_id`, `artifact_type`, `title`, `canonical_locator`,
`content_hash`, `published_at`, `retrieved_at`. `snapshot_ref` is required where the
locator is mutable, access-controlled, signed, or likely to disappear. `occurred_at` is
used when the documented event time differs from publication time. `retrieved_at` must not
precede `published_at` (you cannot retrieve before publication); `occurred_at` is not
ordered (embargo/forward-dating is legitimate). *(Owner-ratified structural check, 2026-06-23.)*

`artifact_type` is one of:

```text
ARTICLE
OFFICIAL_STATEMENT
REPORT
DATASET
POST
IMAGE
VIDEO
AUDIO
MAP
DOCUMENT
OTHER
```

An artifact carries no stance, credibility, or claim verdict. Locator normalization strips
credentials and tracking parameters while preserving a private retrieval pointer where
needed.

## 4. Claim-evidence assessment log

This append-only record says how one artifact bears on one claim.

```yaml
schema_version: "2.0"
claim_evidence_assessments:
  - id: cea-example-report-to-claim
    claim_id: clm-example-crossing-modes
    artifact_id: evd-example-report-20260620
    support_locator:
      kind: PAGE_AND_QUOTE
      page: 14
      quote: The crossing carries both road and rail traffic.
    support_summary: The report directly states that both transport modes use the crossing.
    stance: SUPPORTS
    information_credibility: 2
    temporal_scope:
      kind: TIMELESS
      start: null
      end: null
    origin_chain:
      - source_id: src-example-owner
        artifact_id: evd-example-owner-record
      - source_id: src-example-wire
        artifact_id: evd-example-report-20260620
    independence_group: ind-example-owner-record
    semantic_review:
      status: CHECKED
      reviewer: human:tim
      reviewed_at: "2026-06-22T12:00:00Z"
      claim_content_hash: sha256:1111111111111111111111111111111111111111111111111111111111111111
      artifact_hash: sha256:0000000000000000000000000000000000000000000000000000000000000000
      relationship_input_hash: sha256:2222222222222222222222222222222222222222222222222222222222222222
    supersedes: null
```

Required fields:

- `id`, `claim_id`, `artifact_id`;
- non-empty `support_locator` and `support_summary`;
- `stance ∈ {SUPPORTS, REFUTES, MIXED, CONTEXT_ONLY}`;
- `information_credibility ∈ {1,2,3,4,5,6,UNASSESSED}`;
- `temporal_scope`;
- non-empty `origin_chain` and `independence_group`;
- `semantic_review`;
- `supersedes`.

Optional fields:

- `primary_evidence_kind` (closed enum; Constitution §6.1a, V-P1-4) — declares an authoritative-primary
  evidence kind for the corroboration C2 path.
- `corroboration_rating_id` (`ref:sas-`) — names the scoped source-reliability rating that backs this
  assessment's §6.1c A–C corroboration leg. `validate_support` honors it only when the named rating is
  an active (un-superseded) leaf, reliability ∈ `{A,B,C}`, and owned by a source in this assessment's
  `origin_chain`. It is the explicit, author-declared "in scope" judgment (the free-text `scope` is not
  machine-matched). Absent ⇒ this assessment does not corroborate via the reliable-source leg.

Temporal scope kinds:

```text
TIMELESS
AT_TIME
AS_OF
INTERVAL
EVENT
```

A review status is `UNCHECKED`, `CHECKED`, or `REJECTED`. `CHECKED` requires reviewer,
timestamp, and all three binding hashes. The relationship-input hash covers locator,
summary, stance, credibility, temporal scope, origin chain, and independence group.
Lifecycle/status fields are excluded from the claim-content hash but included in the full
claim-record hash.

One active leaf is allowed for each claim-artifact supersession chain. The same artifact
may have separate, differently-stanced assessments for different claims.

**Origin-chain binding (R2-P0-4, ratified 2026-06-27).** The reviewed `artifact_id` must be bound
into the assessment's own `origin_chain`: at least one origin link must name that `artifact_id` and
attribute it to the `source_id` that actually owns it (the source on the artifact's evidence record).
Any origin link that names an `artifact_id` must likewise attribute it to that artifact's real owning
source. `validate_claim_evidence` rejects an assessment that fails either rule — without the binding,
two assessments over artifacts from one outlet could declare unrelated origins and be miscounted as
independent (Constitution §6.1). The binding is position-independent: it holds for whichever link
names the reviewed artifact, not a fixed end of the chain.

## 5. Claim registry

All claim variants share:

```yaml
id: clm-example
text: One atomic proposition.
epistemic_type: FACT
support_status: UNVERIFIED
dispute_status: UNKNOWN
freshness_status: NOT_APPLICABLE
lifecycle: CANDIDATE
stability: DURABLE
topics: [example]
created_at: "2026-06-22T12:00:00Z"
supersedes: null
```

Computed status fields may be stored for inspection, but the gates recompute and reject a
mismatch.

An optional `impact_category` (closed enum: `CASUALTIES`, `ATTRIBUTION`, `TERRITORIAL_CONTROL`,
`MILITARY_CAPABILITY`, `NONE`) is the **authoritative high-impact signal** (Constitution §10): a
non-NONE category forces `high_impact: true` and switches on the refuter's high-impact contest,
independent of trigger-word coverage. Unlike the review/lifecycle fields in `CLAIM_CONTENT_EXCLUDE`,
`impact_category` is deliberately **included** in the claim-content hash — like `high_impact`, a
re-categorization breaks prior manifest and semantic-review bindings and forces re-review.

### 5.1 Fact

```yaml
- id: clm-example-crossing-modes
  text: The Example Crossing supports both road and rail traffic.
  epistemic_type: FACT
  support_status: CORROBORATED
  dispute_status: UNCONTESTED
  freshness_status: CURRENT
  lifecycle: REVIEWED
  stability: DURABLE
  temporal:
    kind: TIMELESS
    valid_as_of: null
    valid_from: null
    valid_to: null
    event_time: null
  review_by: "2027-06-22"
  expires_at: null
  freshness_profile: null
  topics: [transport, example]
  high_impact: false
  created_at: "2026-06-22T12:00:00Z"
  supersedes: null
```

Facts require explicit temporal semantics. Durable claims require `review_by`; volatile
claims require `expires_at` or a named `freshness_profile`; append-only history requires
an event time. A declared `review_by`/`expires_at` must not precede `created_at` (clock-free
coherence; the now-relative freshness state is separate). *(Owner-ratified, 2026-06-23.)*

### 5.2 Inference

```yaml
- id: clm-example-inference
  text: Damage to both transport modes would create a larger logistics disruption than damage to one mode alone.
  epistemic_type: INFERENCE
  premise_claim_ids:
    - clm-example-crossing-modes
    - clm-example-mode-substitutability
  reasoning: Both modes provide partially substitutable capacity; simultaneous loss removes that substitution.
  support_status: SUPPORTED
  dispute_status: UNKNOWN
  freshness_status: NOT_APPLICABLE
  lifecycle: CANDIDATE
  stability: VOLATILE
  topics: [logistics]
  high_impact: false
  created_at: "2026-06-22T12:00:00Z"
  supersedes: null
```

An inference has premise claims and reasoning. It is not directly “sourced as fact.”

### 5.3 Assumption

```yaml
- id: clm-example-assumption
  text: Repair resources remain available during the modeled period.
  epistemic_type: ASSUMPTION
  rationale: The scenario does not model simultaneous repair-yard disruption.
  consequence_if_false: Recovery time would be materially longer.
  support_status: UNVERIFIED
  dispute_status: UNKNOWN
  freshness_status: NOT_APPLICABLE
  lifecycle: CANDIDATE
  stability: VOLATILE
  topics: [scenario]
  high_impact: false
  created_at: "2026-06-22T12:00:00Z"
  supersedes: null
```

Active claim-evidence assessments on assumptions are invalid.

### 5.4 Projection

```yaml
- id: clm-example-projection
  text: The crossing will resume limited road operation before 2026-08-01.
  epistemic_type: PROJECTION
  projection_kind: FALSIFIABLE
  prediction_id: prd-example-reopen
  scenario_id: null
  support_status: UNVERIFIED
  dispute_status: UNKNOWN
  freshness_status: NOT_APPLICABLE
  lifecycle: REVIEWED
  stability: VOLATILE
  topics: [forecast]
  high_impact: false
  created_at: "2026-06-22T12:00:00Z"
  supersedes: null
```

A falsifiable projection requires `prediction_id`; a scenario branch requires
`scenario_id`. Neither may be assigned fact support status.

## 6. Structured observation registry

Observations are typed values for charts and calculations. They are not a second prose
claim system.

```yaml
schema_version: "2.0"
observations:
  - id: obs-example-crossing-road
    claim_id: clm-example-crossing-modes
    claim_evidence_assessment_ids:
      - cea-example-owner-to-crossing-modes
    value_type: CATEGORY
    value: ROAD
    unit: null
    denominator: null
    basis: transport mode supported by crossing
    temporal_scope:
      kind: TIMELESS
      start: null
      end: null
    geography_id: geo-example-crossing
    uncertainty: null
    extraction:
      method: HUMAN
      extractor: human:tim
      extracted_at: "2026-06-22T12:10:00Z"
      source_locator_hash: sha256:3333333333333333333333333333333333333333333333333333333333333333
    derived_from: []
    transformation: null
    lifecycle: ACTIVE
    supersedes: null
```

Required fields:

- `id`, `claim_id`, non-empty `claim_evidence_assessment_ids`;
- `value_type ∈ {NUMBER, INTEGER, CATEGORY, BOOLEAN, INTERVAL}`;
- `value`, `unit`, `denominator`, `basis`, `temporal_scope`;
- optional `geography_id`, `uncertainty`;
- immutable extraction metadata;
- `derived_from`, `transformation`, `lifecycle`, `supersedes`.

Rates, shares, and percentages require a denominator or explicit basis. Derived
observations require exact parent IDs and a deterministic transformation. Values may not
be silently changed; correction creates a superseding observation.

## 7. Prediction registry and event log

```yaml
schema_version: "2.0"
predictions:
  - id: prd-example-reopen
    question: Will limited road operation resume before 2026-08-01?
    resolution_criterion: TRUE if the declared resolution authority documents sustained public or military road transit before the deadline.
    as_of: "2026-06-22T12:00:00Z"
    resolve_by: "2026-08-01T23:59:59Z"
    probability: 0.65
    resolution_authority: src-example-owner
    void_policy: Void if the crossing is permanently decommissioned or the authority ceases publishing before resolution.
    category: infrastructure-recovery
    dependence_cluster: example-crossing-recovery
    benchmark_probability: 0.50
    declared_data_source: null
```

Every ex-ante field is frozen by a `LOCK` event in `prediction_events.jsonl`:

```json
{"event_id":"evt-prd-example-lock","event_type":"LOCK","prediction_id":"prd-example-reopen","record_hash":"sha256:...","previous_event_hash":null,"event_hash":"sha256:...","recorded_at":"2026-06-22T12:05:00Z","anchor_ref":"local-anchor:..."}
```

Resolution, void, dispute, and correction are later append-only events. The chain head is
anchored outside repository Git history.

## 8. Context pack

A context pack is a deterministic, bounded retrieval result.

```yaml
schema_version: "2.0"
context_packs:
  - id: ctx-example-crossing
    query: What transport modes use the Example Crossing?
    topics: [transport, example]
    generated_at: "2026-06-22T12:20:00Z"
    generator_version: fact-query/1.0
    selection_policy: reviewed-current-first
    token_budget: 4000
    claim_refs:
      - id: clm-example-crossing-modes
        record_hash: sha256:...
    assessment_refs:
      - id: cea-example-owner-to-crossing-modes
        record_hash: sha256:...
    artifact_refs:
      - id: evd-example-owner-record
        content_hash: sha256:...
    observation_refs:
      - id: obs-example-crossing-road
        record_hash: sha256:...
    omitted_candidates:
      - id: clm-example-outdated
        reason: STALE
    pack_hash: sha256:...
```

Contested evidence is retained rather than collapsed. Omitted candidates and reasons are
recorded so token limits do not masquerade as consensus.

> **Context-pack schema (`ctx-`, ratified 2026-06-24; code-locked since Phase 3 / WP3.0).** A
> closed record: `claim_refs`/`assessment_refs`/`observation_refs` bind `record_hash`,
> `artifact_refs` bind the evidence `content_hash`, and `pack_hash = record_hash(pack,
> exclude=pack_hash)`. Each `omitted_candidates` entry is `{id, reason}` with `reason` from the
> **closed enum** `{STALE, SUPERSEDED, TOKEN_BUDGET, REDUNDANT, CONTESTED, OUT_OF_SCOPE, REVIEW_DUE,
> INELIGIBLE}` — a free-text reason cannot launder a dropped current claim. `REVIEW_DUE` = a reviewed
> claim whose review clock lapsed; `INELIGIBLE` = a topic match that is not a REVIEWED+CURRENT fact
> (not-yet-reviewed / REJECTED, or a reviewed non-FACT). The builder records **every** topic-matching
> claim that is not selected, so an omission is never silent. `token_budget` must be a positive
> integer. (Draft/answer additionally recompute the `STALE`, `SUPERSEDED`, `REVIEW_DUE`, and
> `INELIGIBLE` omissions against the live records — a false omission that hides a current claim fails;
> full topic-completeness is Phase 4.)

## 9. Analysis manifest

```yaml
schema_version: "2.0"
analyses:
  - id: ana-example
    lifecycle: ANSWER
    question: What transport modes use the Example Crossing?
    context_pack_id: ctx-example-crossing
    context_pack_hash: sha256:...
    output_path: outputs/ana-example.md
    output_hash: sha256:...
    claim_markers:
      c1:
        claim_id: clm-example-crossing-modes
        claim_hash: sha256:...
    claim_evidence_assessment_refs:
      - id: cea-example-owner-to-crossing-modes
        record_hash: sha256:...
    artifact_refs:
      - id: evd-example-owner-record
        content_hash: sha256:...
    observation_refs: []
    prediction_refs: []
    visual_refs: []
    required_refuter_class: HUMAN_OR_DIFFERENT_MODEL
    manifest_hash: sha256:...
```

The answer uses lightweight markers such as `[[c1]]`; the validator checks that markers,
manifest sets, hashes, and status presentation agree.

## 10. Refuter artifact

```yaml
schema_version: "2.0"
refuters:
  - id: ref-example
    analysis_id: ana-example
    manifest_hash: sha256:...
    output_hash: sha256:...
    reviewer_class: HUMAN
    reviewer: human:tim
    reviewed_at: "2026-06-22T13:00:00Z"
    reviewed_claim_ids: [clm-example-crossing-modes]
    reviewed_assessment_ids: [cea-example-owner-to-crossing-modes]
    verdicts:
      - claim_id: clm-example-crossing-modes
        verdict: SURVIVES
        displacement_check: PASS
        independence_check: PASS
        freshness_check: PASS
        observation_check: NOT_APPLICABLE
        reasoning_check: NOT_APPLICABLE
        notes: Exact owner record and reference report agree.
    alternative_hypotheses: []
    disconfirming_searches:
      - query: Example Crossing only road no rail
        result: no credible contrary artifact found
    unresolved_gaps: []
```

Coverage is set equality against manifest-required IDs. A boolean attestation is not a
substitute. Verdicts are `SURVIVES`, `REVISE`, `DOWNGRADE`, or `REJECT`.

## 11. Visual specification

```yaml
schema_version: "2.0"
visuals:
  - id: vis-example-modes
    visual_type: SCHEMATIC
    title: Transport modes using the Example Crossing
    as_of: "2026-06-22"
    input_claim_refs:
      - id: clm-example-crossing-modes
        record_hash: sha256:...
    input_claim_evidence_assessment_refs:
      - id: cea-example-owner-to-crossing-modes
        record_hash: sha256:...
    input_observation_refs:
      - id: obs-example-crossing-road
        record_hash: sha256:...
      - id: obs-example-crossing-rail
        record_hash: sha256:...
    input_prediction_refs: []
    input_geography_refs: []
    data_bindings:
      road_node: obs-example-crossing-road
      rail_node: obs-example-crossing-rail
    transformation: identity
    filters: []
    aggregation: none
    missing_data_policy: error
    output_path: outputs/vis-example-modes.svg
    renderer: graphviz
    renderer_version: planned
    spec_hash: sha256:...
```

`visual_type ∈ {CHART, TIMELINE, MAP, SCHEMATIC}`. Charts use observations. Maps use
geography IDs. Schematics do not accept raw coordinates. Every render produces:

- the visual file;
- metadata YAML with input/output hashes and renderer details;
- normalized data/geometry sidecar;
- inspection result.

## 12. Geography record

```yaml
schema_version: "2.0"
geography:
  - id: geo-example-crossing
    title: Example Crossing location
    geometry_type: POINT
    spatial_semantics: STRUCTURE_CENTROID
    crs: EPSG:4326
    geometry_ref: geodata/geo-example-crossing.geojson
    geometry_hash: sha256:...
    geometry_claim_id: clm-example-location
    claim_evidence_assessment_ids:
      - cea-example-map-to-location
    valid_from: null
    valid_to: null
    lifecycle: ACTIVE
    supersedes: null
```

`spatial_semantics` distinguishes event location, structure centroid, route centerline,
administrative boundary, control area, and other geometry. A renderer may not silently
substitute one for another.

## 13. Baseline promotion and maintenance event

`baseline_events.jsonl` records promotion, refresh, rejection, and supersession:

```json
{"event_id":"evt-clm-example-promote","event_type":"PROMOTE","claim_id":"clm-example-crossing-modes","claim_content_hash":"sha256:...","before_record_hash":"sha256:...","after_record_hash":"sha256:...","assessment_hashes":["sha256:..."],"artifact_hashes":["sha256:..."],"review_hash":"sha256:...","recorded_at":"2026-06-22T13:10:00Z","previous_event_hash":null,"event_hash":"sha256:..."}
```

Promotion changes only `lifecycle: CANDIDATE` to `REVIEWED`. Substantive changes after
promotion require a replacement claim and `SUPERSEDE` event.

## 14. State and immutability rules

- Identity registries may gain aliases or lifecycle dates through governed migration;
  assessments remain append-only.
- Artifacts are immutable by content hash. A changed object is a new artifact.
- Claim-evidence assessments, observations, prediction events, and maintenance events are
  append-only with supersession or correction records.
- Candidate claim text may change before review. Promotion binds the final content hash.
- Reviewed claim content never changes in place.
- Context packs, manifests, and visual specs are immutable snapshots; regenerate rather
  than edit after use.
- Computed status may be cached, but gates recompute it and reject drift.

# EXAMPLE WORKFLOW — From question to reusable fact and visual

This synthetic example shows how the pieces fit. It contains no real-world claim.

> **What is built today vs. illustrative.** This walkthrough shows the *full intended* workflow.
> Built and runnable now: `fact.py query` (step 1), authoring a checked fact (step 8 is done today
> with **`fact.py add`**, which fuses candidate→assess→promote and fails closed), append-only
> correction (`fact.py supersede`), staleness (`fact.py review-due`), and `verify.py --mode
> records|draft|answer`. **Not yet built** (the steps are kept to show the architecture): the
> context-pack *builder* `fact.py context` (step 9 — context packs are hand-authored for now) and
> the visual generator `scripts/visual.py` (step 11 — Phase 5). Lines invoking those commands will
> not run yet; they mark planned tooling.

## Question

> Which transport modes use the Example Crossing, and can you show it simply?

The useful answer is small. The workflow is explicit because the point is to reuse it
later without trusting memory.

## 1. Query before researching

```bash
.venv/bin/python scripts/fact.py query \
  --topic example-crossing \
  --format yaml
```

Assume the result is empty. That is a valid query result, not permission to upgrade model
memory into fact.

## 2. State one atomic candidate claim

```yaml
schema_version: "2.0"
claims:
  - id: clm-example-crossing-modes
    text: The Example Crossing supports both road and rail traffic.
    epistemic_type: FACT
    support_status: UNVERIFIED
    dispute_status: UNKNOWN
    freshness_status: NOT_APPLICABLE
    lifecycle: CANDIDATE
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
    topics: [example-crossing, transport]
    high_impact: false
    created_at: "2026-06-22T08:00:00Z"
    supersedes: null
```

The claim contains one proposition. It does not also assert length, capacity, location,
or current operating status.

## 3. Register exact source entities

```yaml
schema_version: "2.0"
sources:
  - id: src-example-owner
    title: Example Crossing Authority
    source_type: GOVERNMENT
    jurisdiction: EX
    aliases: []
    canonical_home: https://authority.example.invalid/
    active_from: null
    active_to: null

  - id: src-example-reference
    title: Example Transport Reference Institute
    source_type: RESEARCH_INSTITUTE
    jurisdiction: EX
    aliases: []
    canonical_home: https://reference.example.invalid/
    active_from: null
    active_to: null

groups: []
```

These records identify publishers. They do not support the claim by themselves.

## 4. Capture exact artifacts

```yaml
schema_version: "2.0"
evidence:
  - id: evd-example-owner-record
    source_id: src-example-owner
    artifact_type: DOCUMENT
    title: Example Crossing technical record
    canonical_locator: https://authority.example.invalid/crossing/technical-record
    snapshot_ref: snapshots/evd-example-owner-record.pdf
    content_hash: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
    published_at: "2025-01-15T00:00:00Z"
    occurred_at: null
    retrieved_at: "2026-06-22T08:15:00Z"
    language: en

  - id: evd-example-reference-report
    source_id: src-example-reference
    artifact_type: REPORT
    title: Example regional transport infrastructure
    canonical_locator: https://reference.example.invalid/reports/infrastructure
    snapshot_ref: snapshots/evd-example-reference-report.pdf
    content_hash: sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
    published_at: "2025-09-01T00:00:00Z"
    occurred_at: null
    retrieved_at: "2026-06-22T08:20:00Z"
    language: en
```

The snapshots and hashes preserve what was reviewed.

## 5. Assess each artifact against this claim

```yaml
schema_version: "2.0"
claim_evidence_assessments:
  - id: cea-example-owner-to-crossing-modes
    claim_id: clm-example-crossing-modes
    artifact_id: evd-example-owner-record
    support_locator:
      kind: PAGE_AND_QUOTE
      page: 4
      quote: The crossing consists of parallel road and rail links.
    support_summary: The owner record directly identifies road and rail components.
    stance: SUPPORTS
    information_credibility: 1
    temporal_scope:
      kind: TIMELESS
      start: null
      end: null
    origin_chain:
      - source_id: src-example-owner
        artifact_id: evd-example-owner-record
    independence_group: ind-example-owner-record
    semantic_review:
      status: CHECKED
      reviewer: human:tim
      reviewed_at: "2026-06-22T08:45:00Z"
      claim_content_hash: sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
      artifact_hash: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
      relationship_input_hash: sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd
    supersedes: null

  - id: cea-example-reference-to-crossing-modes
    claim_id: clm-example-crossing-modes
    artifact_id: evd-example-reference-report
    support_locator:
      kind: PAGE_AND_QUOTE
      page: 14
      quote: The Example Crossing carries road vehicles and rail traffic.
    support_summary: The independent reference report confirms both modes.
    stance: SUPPORTS
    information_credibility: 2
    temporal_scope:
      kind: TIMELESS
      start: null
      end: null
    origin_chain:
      - source_id: src-example-reference
        artifact_id: evd-example-reference-report
    independence_group: ind-example-reference-report
    semantic_review:
      status: CHECKED
      reviewer: model:different-family/example-review
      reviewed_at: "2026-06-22T08:50:00Z"
      claim_content_hash: sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc
      artifact_hash: sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
      relationship_input_hash: sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    supersedes: null
```

The two assessments have different terminal origins. They can therefore support
`CORROBORATED`; two news pages repeating the owner record could not.

## 6. Extract typed observations for visual use

The answer could stop at prose. Because a schematic is requested, create reusable
categorical observations rather than parse “road and rail” from claim text at render time.

```yaml
schema_version: "2.0"
observations:
  - id: obs-example-crossing-road
    claim_id: clm-example-crossing-modes
    claim_evidence_assessment_ids:
      - cea-example-owner-to-crossing-modes
      - cea-example-reference-to-crossing-modes
    value_type: CATEGORY
    value: ROAD
    unit: null
    denominator: null
    basis: transport mode supported by the crossing
    temporal_scope:
      kind: TIMELESS
      start: null
      end: null
    geography_id: null
    uncertainty: null
    extraction:
      method: HUMAN
      extractor: human:tim
      extracted_at: "2026-06-22T09:00:00Z"
      source_locator_hash: sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
    derived_from: []
    transformation: null
    lifecycle: ACTIVE
    supersedes: null

  - id: obs-example-crossing-rail
    claim_id: clm-example-crossing-modes
    claim_evidence_assessment_ids:
      - cea-example-owner-to-crossing-modes
      - cea-example-reference-to-crossing-modes
    value_type: CATEGORY
    value: RAIL
    unit: null
    denominator: null
    basis: transport mode supported by the crossing
    temporal_scope:
      kind: TIMELESS
      start: null
      end: null
    geography_id: null
    uncertainty: null
    extraction:
      method: HUMAN
      extractor: human:tim
      extracted_at: "2026-06-22T09:00:00Z"
      source_locator_hash: sha256:9999999999999999999999999999999999999999999999999999999999999999
    derived_from: []
    transformation: null
    lifecycle: ACTIVE
    supersedes: null
```

The claim remains the proposition. The observations are typed render/calculation inputs.

## 7. Run record validation and compute status

```bash
.venv/bin/python scripts/verify.py --mode records
```

The support gate recomputes:

```yaml
support_status: CORROBORATED
dispute_status: UNCONTESTED
freshness_status: CURRENT
```

A stored mismatch fails. The model cannot declare `CORROBORATED` and hope nobody checks
the graph.

## 8. Review and promote to baseline

The candidate is durable and has two checked independent chains. A qualifying review
checks atomicity, exact support, independence, and repository compartment.

Synthetic review packet:

```yaml
schema_version: "2.0"
refuters:
  - id: ref-example-baseline-review
    analysis_id: ana-example-baseline-review
    manifest_hash: sha256:1212121212121212121212121212121212121212121212121212121212121212
    output_hash: sha256:1313131313131313131313131313131313131313131313131313131313131313
    reviewer_class: HUMAN
    reviewer: human:tim
    reviewed_at: "2026-06-22T09:15:00Z"
    reviewed_claim_ids: [clm-example-crossing-modes]
    reviewed_assessment_ids:
      - cea-example-owner-to-crossing-modes
      - cea-example-reference-to-crossing-modes
    verdicts:
      - claim_id: clm-example-crossing-modes
        verdict: SURVIVES
        displacement_check: PASS
        independence_check: PASS
        freshness_check: PASS
        observation_check: PASS
        reasoning_check: NOT_APPLICABLE
        notes: Both exact locators directly support the atomic durable claim.
    alternative_hypotheses: []
    disconfirming_searches:
      - query: Example Crossing rail-only road-only
        result: no credible contrary artifact found
    unresolved_gaps: []
```

Promote:

```bash
.venv/bin/python scripts/fact.py promote \
  --claim clm-example-crossing-modes \
  --review ref-example-baseline-review
```

> **Today:** there is no separate `promote` step. **`fact.py add`** builds the checked fact and
> promotes it in one fail-closed operation (it composes the records through the integrity gates and
> persists only on a clean pass), writing `lifecycle: REVIEWED` directly. A separate
> candidate→promote lifecycle (the snippet above) is planned but not built; to *correct* an existing
> fact use **`fact.py supersede`** (append-only).

## 9. Build a context pack for a later answer

Weeks later, the same question arrives. Query finds the reviewed claim and avoids a fresh
research round.

```bash
.venv/bin/python scripts/fact.py context \
  --topic example-crossing \
  --output contexts/ctx-example-crossing.yaml
```

> **Not yet built.** The deterministic context-pack *builder* (`fact.py context`) is the remaining
> Phase-4 gap. A context pack is validated by `validate_context_pack.py` and resolved by
> `verify.py --mode draft|answer`, but for now the pack YAML (below) is authored by hand.

Synthetic pack:

```yaml
schema_version: "2.0"
context_packs:
  - id: ctx-example-crossing
    query: Which transport modes use the Example Crossing?
    topics: [example-crossing, transport]
    generated_at: "2026-07-10T10:00:00Z"
    generator_version: fact-query/1.0
    selection_policy: reviewed-current-first
    token_budget: 2000
    claim_refs:
      - id: clm-example-crossing-modes
        record_hash: sha256:1414141414141414141414141414141414141414141414141414141414141414
    assessment_refs:
      - id: cea-example-owner-to-crossing-modes
        record_hash: sha256:1515151515151515151515151515151515151515151515151515151515151515
      - id: cea-example-reference-to-crossing-modes
        record_hash: sha256:1616161616161616161616161616161616161616161616161616161616161616
    artifact_refs:
      - id: evd-example-owner-record
        content_hash: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
      - id: evd-example-reference-report
        content_hash: sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
    observation_refs:
      - id: obs-example-crossing-road
        record_hash: sha256:1717171717171717171717171717171717171717171717171717171717171717
      - id: obs-example-crossing-rail
        record_hash: sha256:1818181818181818181818181818181818181818181818181818181818181818
    omitted_candidates: []
    pack_hash: sha256:1919191919191919191919191919191919191919191919191919191919191919
```

## 10. Draft and bind the answer

Answer text:

```text
The Example Crossing supports both road and rail traffic. [[c1]]
```

Manifest:

```yaml
schema_version: "2.0"
analyses:
  - id: ana-example
    lifecycle: ANSWER
    question: Which transport modes use the Example Crossing?
    context_pack_id: ctx-example-crossing
    context_pack_hash: sha256:1919191919191919191919191919191919191919191919191919191919191919
    output_path: outputs/ana-example.md
    output_hash: sha256:2020202020202020202020202020202020202020202020202020202020202020
    claim_markers:
      c1:
        claim_id: clm-example-crossing-modes
        claim_hash: sha256:1414141414141414141414141414141414141414141414141414141414141414
    claim_evidence_assessment_refs:
      - id: cea-example-owner-to-crossing-modes
        record_hash: sha256:1515151515151515151515151515151515151515151515151515151515151515
      - id: cea-example-reference-to-crossing-modes
        record_hash: sha256:1616161616161616161616161616161616161616161616161616161616161616
    artifact_refs:
      - id: evd-example-owner-record
        content_hash: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
      - id: evd-example-reference-report
        content_hash: sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
    observation_refs:
      - id: obs-example-crossing-road
        record_hash: sha256:1717171717171717171717171717171717171717171717171717171717171717
      - id: obs-example-crossing-rail
        record_hash: sha256:1818181818181818181818181818181818181818181818181818181818181818
    prediction_refs: []
    visual_refs: []
    required_refuter_class: HUMAN_OR_DIFFERENT_MODEL
    manifest_hash: sha256:2121212121212121212121212121212121212121212121212121212121212121
```

## 11. Create a schematic, not a fake map

The question is conceptual: it needs no geographic placement. Use a schematic.

```yaml
schema_version: "2.0"
visuals:
  - id: vis-example-crossing-modes
    visual_type: SCHEMATIC
    title: Transport modes using the Example Crossing
    as_of: "2026-07-10"
    input_claim_refs:
      - id: clm-example-crossing-modes
        record_hash: sha256:1414141414141414141414141414141414141414141414141414141414141414
    input_claim_evidence_assessment_refs:
      - id: cea-example-owner-to-crossing-modes
        record_hash: sha256:1515151515151515151515151515151515151515151515151515151515151515
      - id: cea-example-reference-to-crossing-modes
        record_hash: sha256:1616161616161616161616161616161616161616161616161616161616161616
    input_observation_refs:
      - id: obs-example-crossing-road
        record_hash: sha256:1717171717171717171717171717171717171717171717171717171717171717
      - id: obs-example-crossing-rail
        record_hash: sha256:1818181818181818181818181818181818181818181818181818181818181818
    input_prediction_refs: []
    input_geography_refs: []
    data_bindings:
      road_node: obs-example-crossing-road
      rail_node: obs-example-crossing-rail
    transformation: identity
    filters: []
    aggregation: none
    missing_data_policy: error
    output_path: outputs/vis-example-crossing-modes.svg
    renderer: graphviz
    renderer_version: planned
    spec_hash: sha256:2222222222222222222222222222222222222222222222222222222222222222
```

```bash
.venv/bin/python scripts/visual.py validate \
  visuals/specs/vis-example-crossing-modes.yaml
.venv/bin/python scripts/visual.py render \
  visuals/specs/vis-example-crossing-modes.yaml
.venv/bin/python scripts/visual.py inspect \
  visuals/specs/vis-example-crossing-modes.yaml
```

> **Not yet built (Phase 5).** `scripts/visual.py` does not exist; no renderer is wired. The visual
> *schema* is enforced and a spec with `renderer_version: planned` is an allowed SKIP (never a PASS)
> when bound into an answer manifest — so the answer loop tolerates a planned visual, but no chart or
> map can actually be produced yet.

After rendering, add the final visual ID/hash to the manifest and recompute manifest/output
hashes.

## 12. Refute the exact answer and visual

The final refuter binds the updated manifest and output hash, reviews the exact claim and
assessment sets, and checks that the visual nodes match the observation values. Any text or
visual edit after review invalidates the hash.

```bash
.venv/bin/python scripts/verify.py --mode answer --analysis ana-example
```

## Failure variants the tests should pin

1. Replace the independent report with a page copying the owner record but keep a second
   independence group → fail.
2. Point the locator to a nearby passage mentioning only road → semantic review should be
   rejected; hash consistency alone is not enough.
3. Set the rail observation value to `ROAD` while keeping correct claim IDs → observation
   or refuter check fails.
4. Edit reviewed claim text to add a capacity number → full claim hash changes and
   promotion/manifest bindings fail.
5. Render the schematic from prose without observation IDs → visual validation fails.
6. Change an observation after visual validation → sidecar/output/answer hashes fail.
7. Omit a contradictory reviewed claim from a constrained context pack without recording
   the omission → context validation fails.

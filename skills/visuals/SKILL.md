---
name: visuals
status: design-spec-until-WP5.6
purpose: Create useful charts, timelines, maps, and schematics from validated records.
---

# Visuals Skill

Use this skill when a visual will make an answer easier to understand or reason about.
This is a private tool: optimize for accuracy and usefulness, not publication ceremony.

## Core rule

**A visual is a view of records, never a new source of facts.**

- Values come from structured observations.
- Maps use real geography records and CRS-aware geometry.
- Schematics use explicit nodes and edges.
- Every render has a validated spec, data/geometry sidecar, metadata sidecar, and
  post-render inspection.

## 1. Choose the simplest useful visual

Use:

- **table** when exact values matter more than shape;
- **timeline** for dated event sequences;
- **bar/line chart** for comparisons or trends;
- **map** when spatial position or route genuinely matters;
- **schematic/network** for logistics flows, dependencies, campaign structure, or layered
  systems where geographic precision is unnecessary.

Do not build a map because the word “Crimea” appeared. A schematic is often more useful
and less brittle.

## 2. Inspect available records

Before designing, identify:

- claim IDs and hashes;
- active checked claim-evidence assessment IDs and hashes;
- artifact IDs/hashes;
- observation IDs/hashes, including units, denominators, time scope, geography, and
  uncertainty;
- geography IDs and spatial semantics;
- prediction IDs for forecast visuals;
- contested, stale, or missing inputs.

If a needed value exists only in prose, create and validate an observation first. Never
parse it during rendering.

## 3. Select visual type

### Chart or timeline

Requires observation or historical-event IDs. Declare:

- data bindings by observation ID;
- units and denominator/basis;
- date filters;
- aggregation and transformation;
- missing-data policy;
- uncertainty representation where available.

### Geographic map

Requires geography IDs with:

- geometry type;
- spatial semantics;
- CRS;
- geometry hash;
- supporting claim and checked assessment IDs;
- validity dates for dynamic boundaries.

Never guess coordinates from memory. Missing geography yields an error or a schematic
fallback.

### Schematic

Requires explicit nodes and edges. Causal edges require inference claims. A visual layout
may imply direction or grouping but may not create a factual relationship absent from the
records.

## 4. Write the visual spec

A minimal spec includes:

```yaml
schema_version: "2.0"
visuals:
  - id: vis-example
    visual_type: CHART
    title: Example comparison
    as_of: "2026-06-22"
    input_claim_refs:
      - id: clm-example
        record_hash: sha256:...
    input_claim_evidence_assessment_refs:
      - id: cea-example
        record_hash: sha256:...
    input_observation_refs:
      - id: obs-example-a
        record_hash: sha256:...
    input_prediction_refs: []
    input_geography_refs: []
    data_bindings:
      series_a: obs-example-a
    transformation: identity
    filters: []
    aggregation: none
    missing_data_policy: error
    output_path: outputs/vis-example.png
    renderer: matplotlib
    renderer_version: planned
    spec_hash: sha256:...
```

Validate before rendering:

```bash
.venv/bin/python scripts/visual.py validate visuals/specs/vis-example.yaml
```

## 5. Render with the correct tool

### Matplotlib

Use for deterministic charts, timelines, and static maps. Keep transformations in the
spec or normalized data preparation step, not hidden inside plotting calls.

### Folium/Leaflet

Use for interactive maps. Basemap/provider configuration must be explicit and cached where
practical. Tests use offline fixtures.

### GeoPandas, Shapely, PyProj

Use for geometry loading, validation, joins, and CRS transformation. Verify longitude/
latitude order, geometry validity, and spatial semantics.

### Mermaid or Graphviz

Use for schematics after WP5.4 selects the reliable renderer. Nodes and edges come from
explicit records.

Render:

```bash
.venv/bin/python scripts/visual.py render visuals/specs/vis-example.yaml
```

## 6. Required sidecars

Every render emits:

1. visual file;
2. metadata YAML containing claim, assessment, artifact, observation, prediction, and
   geography IDs/hashes; renderer/version; filters; transforms; aggregation; missing-data
   policy; spec and output hashes;
3. normalized observation table or geometry dataset used by the renderer;
4. inspection result.

The sidecar is the audit trail. It also makes debugging much less mystical.

## 7. Inspect after rendering

```bash
.venv/bin/python scripts/visual.py inspect visuals/specs/vis-example.yaml
```

The inspector checks:

- output and metadata hashes;
- normalized values/geometry against renderer layer/artist data;
- declared labels and annotations;
- map bounds and crop policy;
- units and denominators;
- longitude/latitude order and CRS;
- no stale/superseded substitution after validation;
- renderer and basemap/cache identifiers.

It does not judge aesthetics or prove that the chosen framing is neutral.

## 8. Bind to the answer

Add visual ID and hash to the analysis manifest. Re-run:

```bash
.venv/bin/python scripts/verify.py --mode answer --analysis ana-id
```

Any post-validation data or render change invalidates the answer manifest until
regenerated and reviewed.

## 9. Status and uncertainty

Because the output is private, presentation can stay restrained. Accuracy rules remain:

- contested inputs cannot be silently omitted from a comparison;
- uncertainty intervals are shown when represented in observations;
- stale inputs cannot appear as current;
- schematics are identified as schematics in metadata;
- missing data is explicit rather than imputed without a declared method.

## 10. Failure rules

Stop rather than:

- invent coordinates;
- parse values from claim prose;
- convert a percentage without denominator;
- hide a transformation in plotting code;
- use a centroid as an event point;
- draw a causal arrow without an inference;
- render a current map from expired geometry;
- add an unsupported factual annotation;
- substitute a different observation after validation.

## Completion checklist

- [ ] Simplest useful visual chosen.
- [ ] Claim, assessment, observation, prediction, and geography inputs resolve.
- [ ] Units, denominators, scope, uncertainty, transformations, and missing data declared.
- [ ] Map geometry is real and CRS-valid, or visual is explicitly schematic.
- [ ] Spec validates.
- [ ] Render completed.
- [ ] Metadata and normalized data/geometry sidecars exist.
- [ ] Post-render inspection passes.
- [ ] Visual ID/hash is bound into the answer manifest.
- [ ] Answer mode passes.

## Evaluation scenarios for WP5.6

1. Correct chart spec with typed observations passes.
2. Same claim/assessment IDs bound to the wrong extracted value fails observation or
   inspection checks.
3. Percentage uses wrong denominator and fails.
4. Longitude/latitude are swapped and fail.
5. Structure centroid is rendered as strike location and fails spatial-semantics check.
6. Factual annotation not declared in spec fails inspection.
7. Missing coordinates trigger schematic fallback, not invented placement.
8. Observation is changed after validation; old visual hash fails answer mode.
9. Contested counter-series is omitted without declared filter; validation fails.

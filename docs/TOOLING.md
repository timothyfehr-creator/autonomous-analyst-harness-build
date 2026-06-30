# TOOLING POLICY

The tool stack is staged. Dependencies arrive only when a work package needs them; the
repository does not become a dependency museum before it can answer a question.

## 1. Runtime baseline

- Python 3.11+
- PyYAML for parsing
- pytest for tests
- standard-library `argparse`, `dataclasses`, `hashlib`, `json`, `pathlib`, `datetime`,
  and `subprocess` where practical

Canonical environment:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

All runtime commands use `.venv/bin/python`.

## 2. Fact repository tools

Built CLI (file-backed YAML; fail-closed):

```bash
.venv/bin/python scripts/fact.py add <seed-spec> --as-of <ts>   # checked fact -> records gates -> persist
.venv/bin/python scripts/fact.py query ...                      # list/search baseline facts
.venv/bin/python scripts/fact.py source ...                     # source identity + scoped reliability ratings
.venv/bin/python scripts/fact.py supersede ...                  # append-only correction of a claim/assessment
.venv/bin/python scripts/fact.py review-due                     # facts whose review/expiry date has passed
.venv/bin/python scripts/fact.py context ... --as-of <ts>       # deterministic hash-pinned context pack
```

There is no separate `candidate`/`assess`/`refresh`/`promote` step: `add` creates a CHECKED
fact directly (honesty guard: the quote must be a verbatim substring of the retrieved
artifact) and `supersede` corrects it append-only.

The implementation is file-backed YAML. Do not add a database until a fixed query benchmark
shows file-backed retrieval is inadequate.

## 2a. Answer-authoring tools

Built CLI (the Tier-2 answer layer; reuses the gates' own hashing; fail-closed):

```bash
.venv/bin/python scripts/answer_build.py fill                   # fill answer-layer binding hashes from live records
.venv/bin/python scripts/answer_build.py manifest ...           # scaffold an ANSWER manifest from a pack + author prose
.venv/bin/python scripts/answer_build.py refuter ...            # scaffold a gate-scoped, UNSIGNED (blocking) refuter
```

## 3. Prediction tools

Planned (Phase 6 — `scripts/prediction.py` does not exist yet):

```bash
.venv/bin/python scripts/prediction.py lock <prediction-id>
.venv/bin/python scripts/prediction.py resolve <prediction-id> ...
.venv/bin/python scripts/prediction.py score
```

Locking requires an external local anchor outside mutable Git history. The anchor format
must support atomic write, chain-head verification, and backup. A remote timestamp or
notary is deferred.

## 4. Visual stack

### Charts and timelines

- **Matplotlib** first: deterministic, mature, and sufficient for the planned chart set.
- Add **pandas** only if deterministic transformation code becomes materially simpler.
  Data still enters through observation records and normalized sidecars.

### Geographic maps

- **Folium/Leaflet** for interactive HTML maps.
- **GeoPandas + Shapely + PyProj** for geometry validation, CRS transformation, and static
  maps with Matplotlib.
- Cached explicit basemap providers for production; offline synthetic tiles/geometries in
  tests.

### Schematics

- **Mermaid or Graphviz**, selected in WP5.4 after checking installation,
  reproducibility, export quality, and headless operation in the target environment.
- Schematics use explicit nodes/edges. They do not accept a paragraph and hallucinate a
  network from vibes.

Planned commands:

```bash
.venv/bin/python scripts/visual.py validate visuals/specs/vis-id.yaml
.venv/bin/python scripts/visual.py render visuals/specs/vis-id.yaml
.venv/bin/python scripts/visual.py inspect visuals/specs/vis-id.yaml
```

Every visual produces:

1. render file;
2. metadata YAML;
3. normalized data or geometry sidecar;
4. inspection result.

Metadata includes claim and active assessment IDs/hashes, artifact IDs/hashes, observation
IDs/hashes, transformations, filters, aggregation, missing-data policy, geography IDs,
renderer/version, basemap/cache identifiers, spec hash, and output hash.

## 5. Web retrieval

The current plan permits human/model-assisted research during WP4.5 but does not build an
autonomous retrieval orchestrator. Retrieval must produce exact artifacts and snapshots.
Tests never access the network.

A future retrieval layer must separate:

- query generation;
- result selection;
- artifact capture;
- claim-evidence assessment;
- semantic review.

It may not collapse “search result found” into “claim supported.”

## 6. Hashing and canonicalization

Use SHA-256. Before relying on hashes, publish deterministic canonicalization fixtures for:

- YAML to normalized JSON;
- excluded mutable/computed fields;
- Unicode normalization;
- date/time normalization;
- list ordering rules;
- null versus absent values;
- line-ending normalization for artifacts and output.

Changing canonicalization is a schema migration, not a refactor.

## 7. Dependency policy

Every new dependency requires:

- named WP and use case;
- pinned compatible range;
- license and maintenance check;
- clear fail-closed message if missing;
- deterministic/offline test strategy;
- removal plan if the dependency proves unnecessary.

Prefer boring tools. The conflict is exciting enough.

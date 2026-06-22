# IMPLEMENTATION PLAN — Analyst Harness v2

The canonical ordered backlog. Build the evidence chain before the research corpus, the
research corpus before the visual layer, and the visual layer before polish. Work one
package at a time under [AGENTS.md](AGENTS.md).

The redesign addresses the adversarial review before code is built:

- claims connect to exact artifacts through claim-specific evidence assessments, never
  through source identities;
- source type, source reliability, artifact identity, and claim-specific information
  credibility are separate;
- claim type, support, dispute, freshness, lifecycle, and stability are separate axes;
- chartable values live in structured observations bound to claims and checked support;
- analyses are bound to output hashes and claim markers;
- refuter coverage is computed against a manifest;
- prediction locks use an append-only hash chain plus an external anchor;
- the baseline fact repository is seeded only after its gates exist;
- visuals are deterministic views of records and use real geographic data.

## Tiered rigor (v3 — read this before the phases)

The heavy chain below is **opt-in**, not the price of every answer (Constitution §1). Three
tiers; the default is Tier 0:

- **Tier 0 — Conversational (default, most questions):** honest epistemic labels in prose
  (fact / inference / assumption / projection + a coarse confidence), speculation encouraged
  and badged, a one-line self-refute. **No records, no manifest, no refuter, no code path.**
  Delivers value on **day zero**, before WP0.1. Governed by the labeling contract (WP0.3),
  not by a gate.
- **Tier 1 — Recorded:** a candidate claim + ≥1 artifact + assessment; passes `records`
  mode. Credibility scoring and full semantic-review hashing are **optional here** (§6.6).
- **Tier 2 — Committed answer:** the full manifest + refuter + `answer` mode below.

The phases build the machinery for Tiers 1–2. **Tier 0 is usable immediately and is where
most daily value lives** — the plan exists so that *when you choose to commit a claim*, the
rigor is there, not so that committing is mandatory. Every WP that produces an answer mode
must preserve Tier 0 as a first-class, lighter path, never silently force Tier 2.

## Rule-to-control map

| Constitution obligation | Primary controls |
|---|---|
| §1 evidence chain | WP1.2–1.6, WP2.1–2.8, WP3.2 |
| §2 source/artifact/assessment separation | WP1.2–1.4, WP2.1–2.3 |
| §3 type-specific claims | WP1.3, WP2.4 |
| §4 multi-axis status | WP1.3, WP2.5–2.7 |
| §5 support, observations, conflict, freshness | WP1.4, WP1.6, WP2.3, WP2.5–2.8 |
| §6 baseline fact repository | WP4.1–4.6 |
| §7 output binding/completeness | WP3.2, WP3.4, WP7.1 |
| §8 refuter | WP3.3–3.4 |
| §9 forecasts/calibration | WP1.5, WP6.1–6.4 |
| §10 visuals | WP1.6, WP2.8, WP5.1–5.6 |
| §11 fail-closed/anti-gaming | every WP; especially WP0.0, WP2.2, WP5.1, WP6.1 |
| §12 migration/governance | WP0.0, WP1.1, WP1.7 |

## Sequencing and definition of done

**Pre-build review gate.** Before WP0.0 is implemented, run `docs/REVIEW_PROMPT.md` cold,
adjudicate every new P0/P1, and set `docs/REVIEW_ADJUDICATION.md` to
`external_review_complete: true`, `open_p0_p1: 0`, and `governance_status: READY`.
This is a governance action, not a code work package.

Do not start a WP until the previous one is green, reviewed, recorded in
`docs/PROGRESS.md`, and committed. Each applicable WP ships:

- one valid fixture;
- one invalid or adversarial fixture;
- a regression test proving the intended exit code and finding;
- exact acceptance commands;
- a self-review and separate scope/oracle review;
- any schema migration and documentation updates caused by the change.

Canonical commands use `.venv/bin/python`; local and CI instructions must not disagree.
Tests never hit the network or depend on wall-clock time. Research WPs may retrieve live
sources, but tests use frozen synthetic artifacts.

Exit codes:

- `0` — clean;
- `1` — findings in valid inputs;
- `2` — usage error or the gate could not genuinely run.

## Utility milestones and stop points

The work is ordered by user value, not conceptual tidiness:

- **Milestone 0 — Day zero (WP0.3, no code):** the Tier-0 conversational contract is in
  place, so honestly-labeled, interesting answers are available *immediately* — before any
  schema or gate exists. This is the mode you will use most; everything below is what lets
  you *commit* a claim when one earns it.
- **Milestone A — Phase 3:** exact evidence, answer binding, and refutation work end to
  end. This is the minimum trustworthy *committed*-answer loop.
- **Milestone B — Phase 4:** the durable fact repository and context-pack tools begin
  amortizing research. This is the first genuinely useful daily release.
- **Milestone C — Phase 5:** charts, timelines, sourced maps, and schematics are available
  on request. Visuals precede calibration because they provide immediate utility;
  forecast skill takes time to observe.
- **Milestone D — Phase 6:** predictions are externally locked, benchmarked, and scored;
  calibration views become meaningful as resolutions accumulate.
- **Phase 7 is optional:** build semantic/retrieval assistance only after actual usage
  demonstrates a bottleneck.

The user may stop after any milestone without leaving a half-valid mode behind.

## Explicit non-goals until named

- autonomous web-research orchestration;
- public-release workflow;
- automated truth scoring;
- large-model entailment as a gatekeeper;
- vector databases or knowledge graphs before simple fact query proves inadequate;
- automated front-line extraction from imagery;
- Centaur wargaming integration;
- publication-grade cartography.

---

# Phase 0 — Governance and scaffold

## WP0.0 — Review-adjudication gate

Implement `scripts/check_review_adjudication.py` against
`docs/REVIEW_ADJUDICATION.md`. Require:

- `external_review_complete: true`;
- `open_p0_p1: 0`;
- `governance_status: READY`;
- every P0/P1 finding has a unique ID, disposition, governing-file change, implementation
  WP, and verification test;
- no `BLOCKING` disposition remains.

The check also confirms that the constitution, plan, data model, example workflow,
conversation (Tier-0) contract, merge notes, knowledge and tooling policies, AGENTS,
CLAUDE, README, PROGRESS, both review prompts, all seed registries, and both skills exist.

**Acceptance**

```bash
.venv/bin/python scripts/check_review_adjudication.py
pytest tests/test_review_adjudication.py
```

Fixtures:

- complete adjudication → `0`;
- missing fatal/P0/P1 finding → `2`;
- finding marked `BLOCKING` → `2`;
- duplicate finding ID → `1`.

## WP0.1 — Repository scaffold and unified verifier

Create the runtime skeleton: `scripts/`, `tests/fixtures/`, `schemas/`, `analyses/`,
`visuals/specs/`, `outputs/`, `requirements-dev.txt`, and `scripts/verify.py`.

Modes:

- `conversational` — reports that Tier 0 needs no verification run (exit `0` with a notice
  pointing to the WP0.3 labeling contract); present so the tier ladder is discoverable from
  the CLI and no one mistakes "no gate" for "not supported";
- `scaffold` — required files, directories, adjudication, Python/dependency availability;
- `records` — reserved until Phase 2 and reports unavailable (`2`);
- `draft` — unavailable (`2`);
- `answer` — unavailable (`2`);
- unknown mode — `2`;
- no mode — defaults to `scaffold`.

**Acceptance**

```bash
.venv/bin/python scripts/verify.py --mode scaffold
.venv/bin/python scripts/verify.py --mode records   # exit 2, explicitly unavailable
.venv/bin/python scripts/verify.py --mode bogus     # exit 2
pytest
```

## WP0.2 — Sensitive-locator and secret hygiene

Keep a narrow defense-in-depth scanner because evidence records can contain signed URLs,
private document IDs, API tokens, and source/method notes. Scan tracked files and reject:

- credential-shaped strings;
- URLs with common signature/auth query parameters;
- private-network URLs unless stored only in ignored `private/` overlays;
- unredacted `file://` paths outside the repository;
- assessment records containing fields reserved for the private overlay.

Mask findings. Fail closed on no Git repository or zero tracked files. Synthetic fixtures
are scanned by explicit test path and excluded from the default repository scan.

**Acceptance**

```bash
.venv/bin/python scripts/sensitive_scan.py
pytest tests/test_sensitive_scan.py
```

## WP0.3 — Tier-0 conversational labeling contract (the lightweight default)

The one piece of the lightweight default that ships as governance up front, because Tier 0
is the most-used mode and must be specified, not assumed. Author `docs/CONVERSATION.md`: the
labeling rules (every load-bearing statement tagged fact / inference / assumption /
projection + a coarse confidence; speculation encouraged and explicitly badged; one-line
self-refute), worked good/bad examples drawn from real exploratory questions, and the
**escalation triggers** — the signals that a Tier-0 claim should be promoted to a Tier-1
record (you'll reuse it, chart it, or depend on it) or a Tier-2 answer (you'll treat it as
settled or publish it to yourself). State plainly that Tier 0 is a discipline, not a gate
(§15.8), and that its purpose is to keep answers interesting.

This is **not** code. Its "acceptance" is a usability check, not a CI run:

**Acceptance**

- `docs/CONVERSATION.md` exists, defines the four labels + confidence vocabulary + the
  self-refute convention, and lists the Tier-1/Tier-2 escalation triggers;
- it contains ≥2 worked examples showing an interesting, speculative answer that stays
  useful while honestly labeled (not a sourced-encyclopedia answer);
- `verify.py --mode conversational` returns the notice pointing here.

---

# Phase 1 — Closed schemas and migration

## WP1.1 — Envelope validator and schema registry

Implement `scripts/validate_schema.py` with PyYAML `safe_load` and closed schemas.
Version appears once at file root. Known versions begin with `2.0`; unknown versions exit
`2`. Invalid records exit `1`. Empty default scans exit `2`.

Implement global ID format and uniqueness helpers, exact date/time parsing, enum checking,
unknown-field rejection, duplicate-key rejection, and deterministic finding order.
Publish canonical hash serialization before any downstream hash is accepted.

**Acceptance**

```bash
.venv/bin/python scripts/validate_schema.py tests/fixtures/envelope_valid.yaml
.venv/bin/python scripts/validate_schema.py tests/fixtures/envelope_unknown_version.yaml
pytest tests/test_schema_core.py
```

Pin duplicate YAML keys, per-record versions, bool-as-number, invalid timestamps, unknown
fields, and zero-input failure.

## WP1.2 — Source entities, groups, and assessments

Implement schemas from `docs/DATA_MODEL.md` for:

- source registry;
- non-citable source groups;
- append-only source-assessment log.

Validate the shipped `factbase/sources.yaml` and empty assessment log. Free-text
reliability `note` fields are prohibited in source entities. Reliability rationale lives
only in assessment records or ignored private overlays.

**Acceptance**

- exact source entity → valid;
- group marked citable → invalid;
- group referenced where an entity is required → invalid;
- in-place assessment edit or broken `supersedes` chain → invalid;
- root-only versioning passes; per-record version fails.

```bash
.venv/bin/python scripts/validate_schema.py factbase/sources.yaml
.venv/bin/python scripts/validate_schema.py factbase/source_assessments.yaml
pytest tests/test_source_schema.py
```

## WP1.3 — Type-specific claim schema

Implement claim variants:

- `FACT` with explicit temporal/stability semantics;
- `INFERENCE` with premises and reasoning;
- `ASSUMPTION` with rationale and consequence if false;
- `PROJECTION` with prediction or scenario link.

Implement independent support, dispute, freshness, lifecycle, and stability fields. This
WP validates shape only; cross-file support resolution arrives in Phase 2.

**Acceptance**

- valid mixed-type fixture → `0`;
- inference without premises → `1`;
- assumption with non-`UNVERIFIED` support → `1`;
- falsifiable projection without prediction → `1`;
- durable claim without `review_by` → `1`;
- volatile claim without expiry/profile → `1`;
- per-record version or unknown field → `1`.

## WP1.4 — Evidence artifact and claim-evidence assessment schemas

Implement two closed schemas:

1. **Evidence artifact** — exact retrieved object, source entity, locator, dates, immutable
   hash/snapshot. It carries no universal stance or credibility score.
2. **Claim-evidence assessment** — append-only relationship between one claim and one
   artifact, with support locator/summary, temporal scope, stance, credibility, origin
   chain, independence group, semantic-review block, and supersession.

Semantic review binds the current claim-content hash, artifact hash, and canonical hash of
relationship inputs. Lifecycle/status fields are excluded from claim-content hash but
included in full claim-record hash.

**Acceptance**

- complete artifact plus structurally valid unreviewed relationship → `0`;
- signed URL without canonicalization/snapshot → `1`;
- artifact whose `source_id` is a group → `1`;
- relationship with empty locator/summary or malformed ID → `1`;
- one artifact linked `SUPPORTS` to claim A and `REFUTES` to claim B → `0`;
- reviewed relationship missing a binding hash → `1`;
- unknown field → `1`.

## WP1.5 — Prediction and append-only event schemas

Implement prediction, lock, resolution, void, dispute, and correction event schemas.
Freeze all ex-ante fields: question, criterion, probability, dates, resolution authority,
void policy, category, cluster, benchmark, and declared data source.

**Acceptance**

- valid prediction and lock event → `0`;
- bool probability, missing criterion, or invalid resolve date → `1`;
- lock hash not matching canonical prediction → `1`;
- resolution event attempting to mutate ex-ante fields → `1`;
- broken previous-event hash → `1`.

## WP1.6 — Observation, analysis, refuter, geography, baseline-event, and visual schemas

Implement schemas for:

- structured observations used by charts/calculations;
- context packs;
- analysis manifests;
- refuter artifacts;
- geography records whose geometry resolves to supporting claims;
- baseline promotion/maintenance events;
- visual specifications.

Coverage booleans are forbidden. Refuter coverage uses explicit manifest and reviewed-ID
sets. Map specs require geography IDs; schematic specs do not accept geographic
coordinates.

**Acceptance**

- observation bound to claim/assessment with explicit unit/scope → `0`;
- observation with mismatched assessment, missing unit, or missing rate denominator → `1`;
- complete manifest/refuter pair → structural `0`;
- refuter with boolean-only coverage → `1`;
- map with raw coordinates embedded in spec rather than geography IDs → `1`;
- geography record missing CRS or spatial semantics → `1`;
- context pack with mismatched claim/assessment/artifact/observation hash → `1`;
- promotion event with mismatched claim/review hashes → `1`;
- visual with no record inputs → `1`.

## WP1.7 — Migration framework

Implement `scripts/migrate.py` with `--from`, `--to`, `--dry-run`, `--backup-dir`, and
`--check-only`. Ship a golden migration from v1 source/claim shapes to v2 where possible;
records that cannot be safely migrated become explicit `CANDIDATE`/`UNVERIFIED`
quarantine records with a report rather than invented data.

Document mixed-version policy: runtime gates accept one version per file and reject mixed
repositories except during explicit migration.

**Acceptance**

- golden v1 source registry → deterministic v2 output;
- grouped sources become non-citable groups;
- old claim source IDs do not become fake artifacts; claims enter quarantine;
- dry-run makes no changes;
- backup and rollback restore byte-identical inputs.

---

# Phase 2 — Source, artifact, assessment, claim, and observation integrity

## WP2.1 — Source registry integrity

Implement `scripts/validate_sources.py`:

- unique IDs across entities/groups;
- valid aliases and lifecycle dates;
- no group/entity identity collision;
- no citable groups;
- source entities referenced by evidence exist and are active or explicitly historic.

Fail closed on missing, unreadable, or empty registry when evidence is being validated.

## WP2.2 — Source-assessment governance

Implement append-only assessment validation and Git-diff policy:

- no deletions or in-place rating changes;
- valid supersession chain;
- rationale, sample definition, assessor, and date required;
- a new/changed assessment cannot benefit a claim introduced or upgraded in the same
  commit unless an adjudication record names that exact exception.

The scope/oracle review reports assessment changes separately from code changes.

**Adversarial fixture:** upgrade a social source in the same commit as a claim that now
passes. The gate must fail.

## WP2.3 — Artifact integrity and claim-evidence governance

Implement `scripts/validate_evidence.py` and
`scripts/validate_claim_evidence.py`.

Artifact checks:

- source resolution;
- canonical locator and snapshot/hash rules;
- publication/occurrence and retrieval dates;
- duplicate artifact detection;
- no claim-specific stance, credibility, or semantic verdict on artifacts.

Assessment checks:

- claim and artifact resolution;
- exact locator, non-empty summary, and valid temporal scope;
- stance and information credibility;
- non-empty origin chain and independence group;
- one active leaf per claim-artifact supersession chain;
- semantic review bound to current hashes;
- no in-place edits/deletions;
- shared terminal origin cannot use multiple independence groups without adjudication.

Two outlets reproducing the same wire or official statement remain one independence group.
The validator checks declared consistency; it does not pretend to infer provenance from
prose.

## WP2.4 — Type-specific claim integrity

Implement `scripts/validate_claims.py` to resolve active assessments, premise, prediction,
scenario, and supersession references and enforce §3.

This gate does not require evidence for assumptions; it rejects active assessments on
them. Candidate facts may be unsourced but cannot become reviewed or support answers until
support gates pass.

Pin candidate revision rules: before first review, claim text may change; after promotion,
substantive change requires replacement and supersession.

## WP2.5 — Support and corroboration gate

Implement `scripts/validate_support.py`:

- `SUPPORTED` requires at least one active `SUPPORTS` assessment with semantic review
  `CHECKED`;
- `CORROBORATED` requires at least two checked supporting assessments from two
  independence groups;
- origin chains cannot collapse to one underlying origin;
- at least one chain is authoritative primary evidence or uses a source assessed `A`–`C`
  in scope at review time;
- `THIN` and `UNVERIFIED` are allowed but cannot be mislabeled as stronger;
- quantitative claims require exact numeric support locator, including spelled-out
  quantities detected by the declared tokenizer;
- artifact count never substitutes for independent-assessment count.

Pin the central exploit: a low-reliability official statement plus any URL cannot produce
`CORROBORATED`.

## WP2.6 — Conflict and stance gate

Implement `scripts/validate_conflict.py`:

- `CONTESTED` requires independent checked `SUPPORTS` and `REFUTES` or material `MIXED`
  assessments;
- mixed credible stances on `UNCONTESTED` fail;
- same independence group cannot satisfy both sides;
- answer rendering preserves date and credibility metadata for conflict.

## WP2.7 — Freshness and supersession gate

Implement `scripts/validate_freshness.py`:

- current freshness derives from checked assessment temporal scopes;
- `valid_as_of` cannot post-date newest qualifying evidence endpoint merely because review
  happened later;
- expired volatile claims cannot be used as current;
- durable claims become `REVIEW_DUE` at `review_by`;
- superseded/rejected claims are excluded by default;
- time is injectable in tests.

No single 14-day default. Each volatile claim declares `expires_at` or a named profile in
versioned configuration.

## WP2.8 — Structured observation integrity

Implement `scripts/validate_observations.py`:

- every observation resolves to one quantitative/categorical `FACT` and one or more active
  checked supporting assessments;
- value, unit, denominator, temporal scope, geography, and uncertainty are explicit and
  compatible with claim and support locator;
- rates/shares/percentages cannot omit denominator or basis;
- derived observations list exact parents and deterministic transformation;
- superseded observations are excluded by default;
- charts/calculations may consume only observation IDs, never values parsed from prose.

Adversarial fixtures pin:

- correct claim and assessment attached to the wrong extracted number;
- percent with wrong denominator;
- tonnes/day used as tonnes/year;
- old observation substituted into an already-hashed context pack;
- derived value with undeclared parents.

**Phase 2 composition acceptance**

Activate `verify.py --mode records` and compose source, assessment, artifact,
claim-evidence, claim, support, conflict, freshness, and observation gates in dependency
order. A dependency failure propagates exit `2`, not a misleading downstream finding.

```bash
.venv/bin/python scripts/verify.py --mode records
pytest
```

---

# Phase 3 — Analysis binding and refutation

## WP3.1 — Draft composition

Activate `verify.py --mode draft`. Compose `records` plus:

- prediction-link integrity for projections;
- context-pack validation when present;
- analysis-manifest structural validation;
- clear active/not-yet-active gate reporting.

Print a permanent `STRUCTURAL + REVIEWABLE, NOT TRUE` banner. `SKIP` is visually distinct
from `PASS`, never counted as pass, and permitted only for a control whose phase has not
landed. Any skipped control required by the selected mode exits `2`.

## WP3.2 — Analysis manifest and output markers

Implement manifest generation and `scripts/validate_output.py`.

- The manifest pins exact claim, assessment, artifact, observation, prediction, context,
  and visual IDs/hashes.
- Load-bearing prose uses lightweight markers such as `[[c1]]`.
- Output hash binds the reviewed text.
- Markers for `UNVERIFIED`, `THIN`, `CONTESTED`, `STALE`, assumptions, inferences, and
  projections must preserve visible status.
- Unresolved markers, extra manifest claims never used, changed output hash, or visual
  hash mismatch fail.

The tool warns about assertion-like unmarked sentences but does not claim completeness.

## WP3.3 — Refuter artifact and support audit

Implement `scripts/validate_refuter.py` and `docs/REFUTER.md`.

A refuter artifact must:

- bind exact manifest and output hashes;
- cover the required claim and assessment sets by set equality;
- record reviewer independence class;
- perform displacement, origin/independence, freshness, inference, observation, and
  alternative-hypothesis checks as applicable;
- record verdicts and unresolved gaps.

Baseline/high-impact claims require `HUMAN`, `DIFFERENT_MODEL`, or `MIXED`. Same-model
fresh-context review is labeled honestly and does not qualify.

## WP3.4 — Answer mode

Activate:

```bash
.venv/bin/python scripts/verify.py --mode answer --analysis ana-example
```

`answer` composes:

1. `draft`;
2. exact output/manifest binding;
3. required refuter artifact and reviewer class;
4. visual existence/hash/inspection where referenced;
5. no stale, superseded, rejected, or unreviewed required input.

A missing refuter, changed output, incomplete set, invalid visual, or unavailable gate
fails. There is no `release` euphemism: `answer` is a verified private answer, not a
publication certificate.

**Milestone A acceptance:** ship one fully synthetic question→evidence→claim→answer→refuter
example whose answer mode passes, plus passing-bad adversarial fixtures for every prior
exploit that now fail.

---

# Phase 4 — Baseline fact repository and context tools

## WP4.1 — Knowledge taxonomy and baseline gate

Implement `docs/KNOWLEDGE.md` as policy and `scripts/validate_baseline.py` as gate.

- `DURABLE` claims must pass the one-year inclusion test, declare `review_by`, be
  reviewed, and use qualifying checked evidence.
- `APPEND_ONLY_HISTORY` requires dated event semantics and event log entry.
- `VOLATILE` claims are prohibited under `factbase/baseline/` and belong in
  `factbase/live/`.
- casualty estimates, force counts, control lines, outages, and similar revisable metrics
  are denied baseline status unless represented as dated claims, not frozen totals.

The gate cannot infer truth but can reject obvious compartment mistakes and missing
promotion history.

## WP4.2 — Fact query tool

Implement:

```bash
.venv/bin/python scripts/fact.py query --topic <topic>
```

Support filters for text/topic, epistemic type, stability, lifecycle, support, dispute,
freshness, geography, and date. Default results:

- reviewed;
- not superseded/rejected;
- current or explicitly historical;
- with active checked support.

Output human table, YAML, or JSON. Each row includes status, review dates, active
assessment IDs, artifact IDs, observation IDs, and record hashes. Query failure or no
valid registry exits `2`; zero matches is a valid `0` with explicit empty result.

## WP4.3 — Context-pack builder

Implement:

```bash
.venv/bin/python scripts/fact.py context --topic <topic> --output <path>
```

The pack freezes exact claim, assessment, artifact, observation, and optional prediction
IDs/hashes. Selection policy is deterministic and recorded. A token budget prevents
context bloat. Omitted candidates and reasons are recorded. Contradictory/contested claims
are retained as a pair rather than truncated into apparent agreement.

The builder prefers durable baseline facts, then valid live facts, then explicit gaps. It
never fills a gap from model memory.

## WP4.4 — Candidate and promotion workflow

Implement:

```bash
.venv/bin/python scripts/fact.py candidate ...
.venv/bin/python scripts/fact.py assess --claim clm-id --evidence evd-id
.venv/bin/python scripts/fact.py review-due
.venv/bin/python scripts/fact.py refresh --claim clm-id
.venv/bin/python scripts/fact.py promote --claim clm-id --review ref-id
.venv/bin/python scripts/fact.py supersede --claim clm-old --replacement clm-new
```

`review-due` lists overdue durable and expiring live records without mutating them.
`refresh` creates candidate artifact/assessment records; it cannot move a date by typing
today. Promotion atomically changes only lifecycle `CANDIDATE`→`REVIEWED` and appends an
event containing unchanged claim-content hash, before/after record hashes, and exact
assessment/artifact/review hashes. After promotion, substantive change requires a
replacement claim and supersession event.

## WP4.5 — Seed the durable spine

Only now perform real research. Seed a deliberately small corpus:

- 10–15 durable geography/infrastructure claims, prioritizing Crimea/Black Sea logistics
  and recurring transport chokepoints;
- 10–15 dated historical events forming a minimal war chronology;
- 5–10 recurring definitions or measurement conventions for logistics,
  energy/refining, and military concepts.

Each claim must have exact artifacts, checked assessments, any reusable chartable values
represented as observations, a promotion event, and passing `answer` mode in a small
demonstration analysis. No claim is accepted merely because the model “knows” it.

Acceptance is two-layered:

1. all mechanical gates pass;
2. a review packet lists every candidate, artifact locator, support summary, assessment
   ID, independence judgment, reviewer verdict, and rejected candidate.

## WP4.6 — Fact-repository skill

Install and evaluate `skills/fact-repository/SKILL.md`. A fresh agent receives a
missing-fact scenario and must:

1. query first;
2. avoid expired/superseded records;
3. create a candidate rather than assert memory;
4. retrieve exact artifacts and create claim-specific assessments;
5. create observations only for typed values likely to be reused;
6. request correct reviewer level;
7. promote only after gates and review;
8. build a bounded context pack for the answer.

Evaluation uses a scripted rubric over generated files, not self-reported compliance.

**Milestone B acceptance:** use the repository to answer a recurring question without
re-researching durable claims, while refreshing only expired live claims.

---

# Phase 5 — Visual specifications and renderers

## WP5.1 — Visual-spec validation

Implement `scripts/visual.py validate`:

- all claim, assessment, observation, artifact, prediction, and geography input IDs
  resolve and hashes match;
- output paths stay under `outputs/`;
- chart values resolve only from observations; units, denominators, date filters,
  aggregation, transformations, and missing-data handling are explicit;
- map specs use geography IDs whose support resolves through checked assessments, never
  naked model-generated coordinates;
- visual specs cannot upgrade status, hide contested inputs, or silently switch a factual
  map to a schematic.

## WP5.2 — Charts and timelines

Implement deterministic Matplotlib renderers consuming structured observations for:

- time series;
- categorical comparisons;
- event timelines;
- uncertainty intervals where represented.

Every render emits metadata YAML plus exact normalized observation data. Renderers never
parse numeric values from claim prose. Tests compare data/metadata exactly and image
structure tolerantly rather than brittle pixel identity.

Phase-select dependencies: start with Matplotlib and standard library. Add pandas only if
it materially simplifies deterministic transformations; justify and pin it.

## WP5.3 — Geographic maps

Implement:

- interactive maps with Folium/Leaflet;
- static maps with GeoPandas + Matplotlib;
- CRS validation and explicit transformations;
- geometry-claim and active-support validation;
- spatial-semantics checks so centroids, event points, routes, and control areas cannot be
  interchanged;
- longitude/latitude and geometry-validity checks;
- offline test basemaps/fixtures.

Production rendering may fetch a basemap only through explicit cached provider
configuration. Dynamic boundaries require dated geometry. Missing coordinates yield a
clear error or schematic suggestion, never guessed placement.

## WP5.4 — Schematics and network diagrams

Implement conceptual visuals for logistics flows, dependency chains, campaign structure,
and air-defense layering. Use Mermaid or Graphviz from explicit nodes/edges after checking
which tool is reliably installed in the target environment. A schematic is labeled as
such in metadata and cannot masquerade as a map. Causal arrows require inference claims;
decorative layout creates no relationship.

## WP5.5 — Post-render inspection and regression harness

Implement `scripts/visual.py inspect` to compare rendered artifact with validated spec and
sidecars:

- output and metadata hashes match;
- normalized values/geometry and rendered layer/artist data agree;
- every factual label/annotation maps to a declared record ID;
- map bounds contain all declared features unless explicit crop is documented;
- no stale/superseded extract was substituted after validation;
- renderer version and basemap/cache identifiers are recorded.

Pin passing-but-wrong cases: swapped longitude/latitude, wrong denominator, centroid
rendered as event point, undeclared annotation, and cropped contradictory feature. The
inspector reduces renderer bugs; it does not automate visual judgment.

## WP5.6 — Visual skill and answer integration

Install and evaluate `skills/visuals/SKILL.md`. An agent given a visual request must:

1. choose the simplest useful visual;
2. build/validate a visual spec from record IDs/hashes;
3. use observations for values and real geography for maps;
4. render, inspect, and verify sidecars;
5. bind visual ID/hash into analysis manifest;
6. state gaps rather than invent data.

Ship a demonstration gallery: one timeline from append-only history, one chart, one
sourced map or documented schematic fallback, and their metadata. `answer` mode verifies
referenced visual hashes and input validity.

**Milestone C acceptance:** produce one chart and one map/schematic from a context pack,
then mutate a source observation and prove the old visual can no longer pass answer mode.

---

# Phase 6 — Forecast integrity and calibration

## WP6.1 — Prediction lock and external anchor

Implement `scripts/prediction.py lock`:

- canonicalize every ex-ante field;
- append a lock event to the hash chain;
- write/update chain head in a user-local anchor outside repository history, with optional
  remote/signed anchor later;
- fail closed when anchor unavailable;
- never trust Git history alone.

Tests cover amended/rebased commits, editing before first commit, changed criterion,
clock skew, replayed lock events, and anchor rollback.

## WP6.2 — Projection coverage and resolution governance

Every falsifiable `PROJECTION` requires a prediction. Report:

- projection count;
- linked prediction count;
- overdue unresolved predictions;
- void/ambiguous outcomes;
- dependence clusters;
- missing benchmark probabilities.

Past-due predictions require adjudicated resolution, void, or disputed status; they cannot
disappear.

## WP6.3 — Brier and benchmark scoring

Implement per-prediction and aggregate Brier, benchmark Brier, Brier skill, resolution
rate, and logging coverage. Score only from append-only resolution events. Separate
reporting from any claim of skill.

## WP6.4 — Calibration diagnostics and views with sample warnings

Add reliability diagrams, Brier trend, benchmark comparison, resolution-rate view, and
Murphy decomposition after deterministic scoring exists. Reports display raw N,
effective/clustered N, confidence intervals or bootstrap ranges, and prominent low-power
status. A configurable predeclared power plan governs when the tool may say “demonstrated
skill.”

No gate requires a good score; the point is measurement, not grading the analyst into
forecasting only easy questions. Calibration renderers use Phase 5 specs, sidecars,
inspection, and answer binding.

**Milestone D acceptance:** lock and resolve a synthetic ledger, prove history rewrite
fails, and produce a low-N calibration report that explicitly refuses to claim skill.

---

# Phase 7 — Coverage and semantic assistance

## WP7.1 — Claim-extraction helper

Build a deliberately lossy helper that proposes atomic markers from answer prose and
reports unmarked assertion-like sentences. It does not create reviewed claims or make
completeness claims. Evaluate precision/recall on a small annotated fixture set.

## WP7.2 — Semantic-support assistant

Optionally add model-assisted comparison between claim text and support locator, returning
`ENTAILS`, `PARTIAL`, `CONTRADICTS`, or `NOT_FOUND` with rationale. It creates candidate or
superseding assessments; it never mutates artifacts and cannot self-certify `CHECKED` for
high-impact/baseline claims. Store model/version plus claim, artifact, and relationship
hashes.

## WP7.3 — Retrieval and search upgrades

Only after corpus size justifies it, consider full-text indexing, embeddings, or a vector
store. Acceptance is measured retrieval improvement on a fixed query set, not “we now
have a vector database.”

---

# Deferred backlog

- Public/redacted export mode.
- Automated source-performance sampling and reliability suggestions.
- Remote timestamp/notary anchor for prediction locks.
- Automated evidence snapshotting subject to copyright/access rules.
- Geospatial change detection and front-line extraction.
- Centaur integration for analyses requiring adversary simulation.
- Multi-user review and access control.

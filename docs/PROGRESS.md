# PROGRESS

Durable build state. Read this and `IMPLEMENTATION_PLAN.md` before touching code. Update
after every work package.

## Entry format

```text
### WPx.y — name [DONE | IN PROGRESS | BLOCKED]
- Shipped:
- Acceptance:
- Assumptions / deferred:
- Oracle-data changes:
- Migration impact:
- Commit:
- Next:
```

## Current state

**Pre-WP0.0 — v3 merged design package complete; no code exists.**

v3 merges two v2 designs (see `MERGE_NOTES.md`): it keeps the rigorous evidence-chain /
multi-axis data model and adds the **three-tier rigor model** (Constitution §1) so the
heavy chain is opt-in and **Tier 0 — conversational** is the lightweight default. New since
the GPT v2 base: the tier framing in the constitution and plan, **WP0.3** (the Tier-0
`docs/CONVERSATION.md` contract) + **Milestone 0** (day-zero value), §6.6 solo right-sizing,
`MERGE_NOTES.md`, and tier annotations in README/CLAUDE.

**Governance is BLOCKED:** v3 is a *new merge* and has not been externally reviewed. Merging
two reviewed-or-unreviewed designs does not transfer any review to the merged artifact — run
a cold external review of v3 and adjudicate new P0/P1s before WP0.0. The day-zero **Tier-0**
mode is usable now regardless, since it is a discipline, not a gated build step.

### Governance [BLOCKED]

- Shipped: v2 governance/design package; structured review adjudication; neutral source
  registry; empty append-only source-assessment, evidence, claim-evidence, observation,
  claim, prediction, geography, baseline-event, and prediction-event stores; fact-
  repository and visual skills; worked end-to-end example.
- Acceptance: YAML parse, link, work-package-reference, and bundle consistency checks run
  locally; cold external review not yet run.
- Assumptions / deferred: semantic truth remains review-based; public release and
  autonomous monitoring remain out of scope.
- Oracle-data changes: source identity/type separated from append-only reliability
  assessments; source groups made non-citable; ISW represented as `RESEARCH_INSTITUTE`;
  no seeded reliability grades asserted without a scoped review sample.
- Migration impact: v1 source/claim data requires WP1.7 quarantine-aware migration; no
  old source ID is converted into fake evidence.
- Commit: n/a
- Next: run `docs/REVIEW_PROMPT.md` cold, adjudicate all new P0/P1 findings, then begin
  WP0.0.

## Phase checklist

### Phase 0 — Governance and scaffold

- [ ] WP0.0 Review-adjudication gate — **BLOCKED pending cold review**
- [ ] WP0.1 Repository scaffold and unified verifier
- [ ] WP0.2 Sensitive-locator and secret hygiene

### Phase 1 — Closed schemas and migration

- [ ] WP1.1 Envelope validator and schema registry
- [ ] WP1.2 Source entities, groups, and assessments
- [ ] WP1.3 Type-specific claim schema
- [ ] WP1.4 Evidence artifact and claim-evidence assessment schemas
- [ ] WP1.5 Prediction and append-only event schemas
- [ ] WP1.6 Observation, analysis, refuter, geography, baseline-event, and visual schemas
- [ ] WP1.7 Migration framework

### Phase 2 — Source, artifact, assessment, claim, and observation integrity

- [ ] WP2.1 Source registry integrity
- [ ] WP2.2 Source-assessment governance
- [ ] WP2.3 Artifact integrity and claim-evidence governance
- [ ] WP2.4 Type-specific claim integrity
- [ ] WP2.5 Support and corroboration gate
- [ ] WP2.6 Conflict and stance gate
- [ ] WP2.7 Freshness and supersession gate
- [ ] WP2.8 Structured observation integrity
- [ ] Phase 2 `records` composition acceptance

### Phase 3 — Analysis binding and refutation

- [ ] WP3.1 Draft composition
- [ ] WP3.2 Analysis manifest and output markers
- [ ] WP3.3 Refuter artifact and support audit
- [ ] WP3.4 Answer mode

### Phase 4 — Baseline fact repository and context tools

- [ ] WP4.1 Knowledge taxonomy and baseline gate
- [ ] WP4.2 Fact query tool
- [ ] WP4.3 Context-pack builder
- [ ] WP4.4 Candidate and promotion workflow
- [ ] WP4.5 Seed the durable spine
- [ ] WP4.6 Fact-repository skill

### Phase 5 — Visual specifications and renderers

- [ ] WP5.1 Visual-spec validation
- [ ] WP5.2 Charts and timelines
- [ ] WP5.3 Geographic maps
- [ ] WP5.4 Schematics and network diagrams
- [ ] WP5.5 Post-render inspection and regression harness
- [ ] WP5.6 Visual skill and answer integration

### Phase 6 — Forecast integrity and calibration

- [ ] WP6.1 Prediction lock and external anchor
- [ ] WP6.2 Projection coverage and resolution governance
- [ ] WP6.3 Brier and benchmark scoring
- [ ] WP6.4 Calibration diagnostics and views with sample warnings

### Phase 7 — Coverage and semantic assistance

- [ ] WP7.1 Claim-extraction helper
- [ ] WP7.2 Semantic-support assistant
- [ ] WP7.3 Retrieval and search upgrades

## Open blockers

1. **Cold external review of v2 has not run.** No implementation WP may start.
2. `docs/REVIEW_ADJUDICATION.md` remains `governance_status: BLOCKED` until that review
   is complete and every new P0/P1 is dispositioned.

## Candidate backlog

- Public/redacted export mode with a separate threat model.
- Automated source-performance sampling and assessment suggestions.
- Remote timestamp/notary anchor for prediction locks.
- Automated evidence snapshotting subject to copyright/access rules.
- Geospatial change detection and front-line extraction.
- Centaur integration for questions requiring adversary simulation.

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

**Phase 0 authorized — v3 cold review complete + adjudicated; governance READY (ACCEPTED_WITH_LIMITS, 2026-06-22). WP0.0 may begin. No code exists yet.**

v3 merges two v2 designs (see `MERGE_NOTES.md`): it keeps the rigorous evidence-chain /
multi-axis data model and adds the **three-tier rigor model** (Constitution §1) so the
heavy chain is opt-in and **Tier 0 — conversational** is the lightweight default. New since
the GPT v2 base: the tier framing in the constitution and plan, **WP0.3** (the Tier-0
`docs/CONVERSATION.md` contract) + **Milestone 0** (day-zero value), §6.6 solo right-sizing,
`MERGE_NOTES.md`, and tier annotations in README/CLAUDE.

**Governance is READY (ACCEPTED_WITH_LIMITS, 2026-06-22):** v3's cold review ran
(`docs/REVIEW_V3_COLD_claude-opus-4-8.md`, 74/100; 1 P0 + ~11 P1; all nine A1–A9 exploits
slipped past the planned gates) and every P0/P1 is adjudicated in
`docs/REVIEW_ADJUDICATION.md`. The review was a **non-independent Claude pass**, accepted with
limits to unblock **Phase 0 only**; a genuinely independent cross-vendor/human pass on the P0 +
top P1s is a **binding gate before Phase 1**. The day-zero **Tier-0** mode remains usable
regardless, since it is a discipline, not a gated build step.

### Governance [DONE — READY w/ limits]

- Shipped: v2 governance/design package; structured review adjudication; neutral source
  registry; empty append-only source-assessment, evidence, claim-evidence, observation,
  claim, prediction, geography, baseline-event, and prediction-event stores; fact-
  repository and visual skills; worked end-to-end example.
- Acceptance: cold review run + adjudicated (`REVIEW_ADJUDICATION.md` READY, `open_p0_p1: 0`,
  no BLOCKING); YAML/link/bundle checks pass locally.
- Assumptions / deferred: semantic truth remains review-based; public release and
  autonomous monitoring remain out of scope.
- Oracle-data changes: source identity/type separated from append-only reliability
  assessments; source groups made non-citable; ISW represented as `RESEARCH_INSTITUTE`;
  no seeded reliability grades asserted without a scoped review sample.
- Migration impact: v1 source/claim data requires WP1.7 quarantine-aware migration; no
  old source ID is converted into fake evidence.
- Commit: see git log (governance-unblock commit, 2026-06-22)
- Next: WP0.0 (review-adjudication gate). **Binding gate before Phase 1:** independent
  cross-vendor/human pass on P0 + top P1s, plus doc-incorporation of V-P0-1/V-P1-4/5/10.

### WP0.0 — Review-adjudication gate [DONE]

- Shipped: `scripts/check_review_adjudication.py` (frontmatter READY checks; finding-row
  parsing with unique-ID, allowed-disposition-enum, no-`BLOCKING`, and P0/P1 full-field checks;
  required-documents existence check; fail-closed). `tests/test_review_adjudication.py` (9 tests)
  + 6 fixtures. `requirements-dev.txt` (PyYAML, pytest). `.venv`.
- Acceptance: `.venv/bin/python scripts/check_review_adjudication.py` → exit 0 on the real
  ledger (34 findings, 29/29 docs present); `pytest tests/` → 9 passed; fixtures map
  complete→0, missing-field / blocking / blocked-status→2, duplicate-id / out-of-enum→1.
- Assumptions / deferred: the disposition enum is hardcoded in the gate (authoritative, so the
  ledger can't widen its own set); the required-files list is the WP0.0 set; semantic
  correctness of dispositions is out of scope.
- Oracle-data changes: F1–F6 finding rows normalized to the 5-column shape (separate commit;
  no finding content changed).
- Migration impact: none.
- Commit: see git log (WP0.0).
- Next: WP0.1 (repository scaffold + unified verifier). NOTE: the Phase-1 gate (independent
  cross-vendor/human pass) still applies before any WP1.x.

## Phase checklist

### Phase 0 — Governance and scaffold

- [x] WP0.0 Review-adjudication gate — **DONE**
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

1. **Phase 1 gate:** a genuinely independent cross-vendor (GPT-5.5-Pro/Gemini)/human pass on
   the P0 + top P1s, plus doc-incorporation of V-P0-1 / V-P1-4 / V-P1-5 / V-P1-10, must complete
   before any WP1.x begins. (Phase 0 is authorized.)
2. Several v3 findings are `PLANNED_FIX` — adjudicated, not yet implemented — tracked in their
   named WPs in `docs/REVIEW_ADJUDICATION.md`.

## Candidate backlog

- Public/redacted export mode with a separate threat model.
- Automated source-performance sampling and assessment suggestions.
- Remote timestamp/notary anchor for prediction locks.
- Automated evidence snapshotting subject to copyright/access rules.
- Geospatial change detection and front-line extraction.
- Centaur integration for questions requiring adversary simulation.

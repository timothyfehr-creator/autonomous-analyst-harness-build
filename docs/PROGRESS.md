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

### WP0.1 — Repository scaffold + unified verifier [DONE]

- Shipped: `scripts/verify.py` (modes: `conversational` [loud "unverified by design" notice,
  never prints `PASS` — F4], `scaffold` [reuses the WP0.0 gate for docs + adjudication, plus
  runtime-dir and dependency checks], `records`/`draft`/`answer` → exit 2 unavailable, unknown
  → 2, no-mode → scaffold); `tests/test_verify.py` (10 tests); runtime dirs `analyses/`,
  `visuals/specs/`.
- Acceptance: `verify.py --mode scaffold`→0, `--mode records`→2, `--mode bogus`→2,
  `--mode conversational`→0 (notice present, token `PASS` absent); `pytest`→19 passed.
- Discharged findings: F4 (conversational unverified-by-design, never `PASS` — mutation-tested
  by the separate reviewer); N11 (commands use `.venv/bin/python`; no bare-python shell-out).
- Assumptions / deferred: `records`/`draft`/`answer` are exit-2 placeholders until their phases.
- Oracle-data changes: none.
- Migration impact: none.
- Separate review: PASS (fresh-context reviewer re-ran the suite + mutation-tested the F4 test).
- Commit: see git log (WP0.1).
- Next: WP0.2 (sensitive-locator + secret hygiene).

### WP0.2 — Sensitive-locator + secret hygiene [DONE]

- Shipped: `scripts/sensitive_scan.py` (detectors: credential-shaped strings [AWS key,
  private-key block, key-name secret assignments], signed/auth-param URLs, private-network URLs,
  `file://` locators-with-path, private-overlay reserved fields, committed-geodata path rule).
  Scans tracked content; excludes `tests/` (synthetic adversarial fixtures) + the scanner's own
  ruleset file. Fails closed (exit 2) on no-git / zero-tracked. `tests/test_sensitive_scan.py`
  (20 tests).
- Acceptance: `sensitive_scan.py`→0 on the real repo; `pytest`→39 passed; adversarial fixtures
  (signed URL / AKIA / private-net / file:// / `private_notes` field / geodata path) each flag;
  near-miss controls (canonical URL / sha256 hash / public URL / `rationale` field / `private/`
  geodata) stay clean; no-git + zero-tracked → 2.
- Discharged findings: N10 (signed/private locators + prohibited private-overlay fields fail —
  reviewer-probed live); V-P1-3 (geodata path rule + named-person assessments in scope; private
  overlay = git-ignored `private/`; the named sources' neutral identity stays clean).
- Detector precision: credential detection is key-name/prefix-contextual (NOT entropy), so
  sha256 hashes never trip; FILE_URI requires a path (a path-less prose `file://` is not a
  locator — reviewer-verified to hide no real secret).
- Assumptions / deferred: source-code secret scanning beyond the content layer is out of WP0.2
  scope.
- Oracle-data changes: none.
- Migration impact: none.
- Separate review: PASS (fresh-context reviewer git-grepped all tracked files for real secrets,
  mutation-probed every detector, and specifically cleared the FILE_URI tightening + exclusions).
- Commit: see git log (WP0.2).
- Next: WP0.3 (confirm Tier-0 conversational contract).

### WP0.3 — Tier-0 conversational contract [DONE]

- Shipped: confirmed `docs/CONVERSATION.md` (pre-existing) meets the WP0.3 acceptance; added
  `tests/test_conversation_contract.py` (8 tests) turning the acceptance bullets into a green
  structural invariant. No change to the contract doc itself.
- Acceptance: the doc defines the four labels, confidence vocabulary, self-refute convention,
  the objective escalation triggers (F1 hardening: deliverable / number-you'd-act-on /
  future-cite / contradiction / forecast-feed / high_impact / 3+-recurrence), the `high_impact`
  + `load-bearing` definitions (F2 doc-level fix), and 2 worked examples; `verify.py --mode
  conversational` points here and never prints `PASS`. pytest → 47 passed.
- Discharged findings: doc-level F1/F2 incorporation (objective triggers + `high_impact` /
  `load-bearing` definitions present). NOTE: the ENFORCEMENT parts — the recurrence backstop
  (F1 / V-P1-1) and gate-computed `high_impact` (F2 / V-P0-1) — are code, deferred to Segment 2.
- Oracle-data changes: none. Migration impact: none.
- Separate review: PASS (fresh-context reviewer confirmed every asserted element is genuinely
  in the doc, the assertions have teeth, and the diff is the single test file).
- Commit: see git log (WP0.3).
- Next: **PHASE 0 COMPLETE → STOP at the Phase-1 gate** (independent cross-vendor/human review
  + the four doc-fixes V-P0-1 / V-P1-4 / V-P1-5 / F3 before any WP1.x).

### Phase-1 gate [CLEARED — 2026-06-22]

- Shipped (gate infrastructure, not a numbered WP): `scripts/preflight_phase1.py` +
  `tests/test_preflight_phase1.py` (7 tests) — machine guard that BLOCKS any WP1.x until the
  five doc-fix anchors (V-P0-1, V-P1-4, V-P1-5, V-P1-10, F3) are present in
  `docs/CONSTITUTION.md` + `docs/DATA_MODEL.md` AND `independent_review_complete: true` is set in
  `docs/REVIEW_ADJUDICATION.md`; fails closed (exit 2). `docs/PHASE1_DOC_FIXES_DRAFT.md` — the
  five draft doc-fixes (PROPOSAL, not applied) + a focused cross-vendor review prompt.
- Live state: **CLEARED** — the five fixes are incorporated into CONSTITUTION (§6.1a/6.1b/6.3/
  6.6/§10) + noted in DATA_MODEL; the independent review is logged as a HUMAN review by the owner
  (`independent_review_complete: true`); `preflight_phase1.py` exits 0. Segment 2 may proceed.
- Separate review: PASS (fresh-context reviewer confirmed no governing-doc edits, the guard
  fails closed, it reads only the governing docs not the draft, and no fix loosens a rule; it
  flagged that the binding condition names V-P1-10 where the gate had F3 — now reconciled, both
  enforced).
- **TO CLEAR THE GATE:** (1) run the independent cross-vendor/human review (focused prompt in
  the draft); (2) reconcile + apply the five fixes to the governing docs, keeping each anchor
  token; (3) set `independent_review_complete: true`. Then `preflight_phase1.py` → exit 0 and
  Segment 2 (Phases 1–3 → Milestone A, minus WP1.7) may resume.
- Commit: see git log.

### WP1.1 — Schema-core framework + golden canonicalization vector [DONE]

- Shipped: `scripts/validate_schema.py` — `canonicalize`/`record_hash` (frozen serialization),
  strict YAML load (duplicate-key rejection), envelope validation (root version `2.0`, unknown
  → 2, per-record version → 1), `validate_record` primitives (id / datetime / enum /
  number-not-bool / unknown-field), and a `register_schema` hook for WP1.2–1.6.
  `tests/test_schema_core.py` (17 tests incl. the hand-verified golden vector) + envelope fixtures.
- Acceptance: envelope_valid → 0, unknown_version → 2, per_record_version → 1, dup_key → 1,
  missing-version / no-input → 2; `pytest` → 72 passed.
- Discharged: **V-P1-7** (golden canonicalization vector; reviewer mutation-tested it — non-circular,
  catches sort/NFC/exclude drift → the R1 tripwire is live, re-asserted by every later WP).
- **Watch-items for later WPs** (reviewer): (1) `exclude` is top-level only — a WP needing nested
  mutable-field exclusion must extend it (with a migration); (2) line-ending normalization is NOT
  in the record hash — close it at **WP1.4** when artifact-content hashing lands (date/time
  normalization lives in `datetime` validation).
- Oracle-data changes: none. Migration impact: none.
- Separate review: PASS (mutation-tested the golden vector; confirmed framework-only scope).
- Commit: see git log. Next: WP1.2 (source schemas).

## Phase checklist

### Phase 0 — Governance and scaffold

- [x] WP0.0 Review-adjudication gate — **DONE**
- [x] WP0.1 Repository scaffold and unified verifier — **DONE**
- [x] WP0.2 Sensitive-locator and secret hygiene — **DONE**
- [x] WP0.3 Tier-0 conversational labeling contract — **DONE** (Phase 0 complete)

### Phase 1 — Closed schemas and migration *(gate cleared 2026-06-22; WP1.7 deferred)*

- [x] WP1.1 Envelope validator and schema registry — **DONE**
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
- Make the canonical private-overlay reserved-field list live in the data model (DATA_MODEL),
  not solely in `sensitive_scan.py`'s regex (reviewer note, WP0.2).

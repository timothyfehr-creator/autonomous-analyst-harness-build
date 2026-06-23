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

### WP1.2 — Source / group / assessment schemas (shape) [DONE]

- Shipped: `scripts/schema_defs.py` (SOURCE / GROUP / SOURCE_ASSESSMENT specs + `COLLECTIONS`).
  `validate_schema.py` changes: **multi-collection envelope** (a file may hold >1 collection,
  e.g. `sources.yaml` = sources + groups), a **`ref:<prefix>` field type** (a `grp-` where a
  `src-` is required fails), **null-skip** in type checks (null = valid unset; enum still catches
  null-in-enum), and a graceful `schema_defs` auto-load. `tests/test_source_schema.py` (10 tests).
- Acceptance: real `factbase/sources.yaml` (29 `src-` + 2 non-citable `grp-`) + empty
  `source_assessments.yaml` → 0; citable-true group / grp-as-source_id / per-record version /
  missing field / bad enum / free-text reliability note → 1; `pytest` → 82 passed (R1 golden
  vector intact).
- Discharged: shape source/group/assessment validation; `citable` must be `false` (non-citable
  groups); free-text reliability note on a source entity rejected (closed-schema unknown-field).
- Deferred to WP2.1/2.2 (cross-record integrity — honestly noted, not silently dropped):
  supersession-chain validation, append-only/in-place-edit enforcement, `member_ids` resolution.
  Watch-items (reviewer): an unregistered extra list-collection passes shape-only (WP2.x may
  reject unknown collection names); `id: null` passes shape (value-presence is WP2.x).
- Oracle-data changes: none. Migration impact: none. Separate review: PASS (probed the envelope
  generalization is a safe broadening, not a weakening).
- Commit: see git log. Next: WP1.3 (claim schemas + `high_impact` field).

### WP1.3 — Type-specific claim schemas + high_impact (shape) [DONE]

- Shipped: `validate_schema.py` (added a `boolean` type + an `extra` per-record validator hook).
  `schema_defs.py` `CLAIM_SCHEMA` + `_claim_extra` variant rules (INFERENCE → premises + reasoning;
  ASSUMPTION → rationale + consequence + support `UNVERIFIED`; PROJECTION FALSIFIABLE →
  `prediction_id` / SCENARIO → `scenario_id`; FACT → `temporal` + DURABLE → `review_by` / VOLATILE
  → expiry / HISTORY → `event_time`, **FACT-scoped**) + multi-axis status enums + `high_impact`
  required boolean (V-P0-1 **shape** half; the gate-recompute is WP2.2). `tests/test_claim_schema.py`
  (11 tests).
- Acceptance: valid mixed-type → 0; inference-no-premises / assumption-supported / falsifiable-no-
  prediction / durable-no-review_by / volatile-no-expiry / bad-enum / high_impact-not-bool /
  unknown-field → 1 (each fails for its named reason); empty baseline+live claims.yaml → 0;
  `pytest` → 93 passed (R1/R2 intact).
- Discharged: V-P0-1 schema half; §4 type-specific contracts; §5 multi-axis status.
- Oracle-data changes: none. Migration impact: none. Separate review: PASS (FACT-scoping probed;
  every fixture fails for the right reason; no recompute/gate logic leaked).
- Commit: see git log. Next: WP1.4 (evidence + claim-evidence + `primary_evidence_kind`; close the
  WP1.1 line-ending watch-item for artifact-content hashing).

### WP1.4 — Evidence + claim-evidence schemas + primary_evidence_kind (shape) [DONE]

- Shipped: `validate_schema.py` (added a `hash` type `sha256:<64hex>` + a **bool-enum guard** so a
  bool can't satisfy an int enum, e.g. `information_credibility: true` is rejected — reviewer-found
  hardening). `schema_defs.py` EVIDENCE_SCHEMA (+ `_evidence_extra`: a signed/mutable
  `canonical_locator` needs a `snapshot_ref` or stripped params) and CLAIM_EVIDENCE_SCHEMA (+
  `_cea_extra`: non-empty locator/summary/origin/independence; valid `temporal_scope.kind`; a
  CHECKED `semantic_review` binds all three hashes) + `primary_evidence_kind` enum (V-P1-4 **shape**,
  optional). `tests/test_evidence_schema.py` (12 tests).
- Acceptance: complete artifact + unreviewed assessment → 0; one artifact SUPPORTS A / REFUTES B → 0;
  signed-URL-no-snapshot / source-is-group / empty-summary / reviewed-missing-hash / unknown-field /
  bad-hash / bad-primary-kind / bool-credibility → 1; empty evidence + claim_evidence logs → 0;
  `pytest` → 105 passed (R1/R2 intact).
- Discharged: V-P1-4 schema half; §3 artifact-not-evidence; §4 assessment shape; §6.1–6.2
  CHECKED-binds-hashes (shape).
- Line-ending watch-item (from WP1.1): `content_hash` is **recorded** here, not computed — artifact
  content line-ending normalization belongs to a future capture/snapshot tool, not a schema WP.
- Oracle-data changes: none. Migration impact: none. Separate review: PASS (schemas exact to §3/§4;
  every cross-field rule probed; the bool-enum quirk hardened + tested).
- Commit: see git log. Next: WP1.5 (prediction + append-only event schemas).

### WP1.5 — Prediction registry + append-only event-log schemas (shape) [DONE]

- Shipped: `schema_defs.py` PREDICTION_SCHEMA (prd-: `resolution_authority`→src-, datetimes,
  `_prediction_extra` = probability∈[0,1] + `resolve_by` after `as_of`) registered as the
  `predictions` collection; PREDICTION_EVENT_SCHEMA + BASELINE_EVENT_SCHEMA (both evt-, with
  `event_type` enums; LOCK binds `record_hash`+`anchor_ref` per §7, PROMOTE binds before/after
  record hashes + `assessment_hashes`/`artifact_hashes` (list-of-hash) + `review_hash` per §13);
  `EVENT_LOGS` map. `validate_schema.py` gains a JSONL path: `EVENT_SCHEMAS`, `_json_no_dup`
  (JSON duplicate-key rejection mirroring the strict YAML loader), `validate_jsonl_file()`, and a
  `.jsonl` dispatch in `validate_file()`. `tests/test_prediction_event_schema.py` (18 tests).
- Scope discipline: **shape + per-record cross-field only.** The cross-LINE append-only chain
  (`previous_event_hash` continuity, `event_hash` recomputation, external anchoring) is Phase-2
  integrity and is NOT implemented here — `previous_event_hash`/`event_hash` are shape-checked
  (hash format) only. Empty event log → exit 0 (logs start empty). Unrecognized `.jsonl` →
  exit 2 (fail closed). Suffix-gated dispatch (YAML never reaches the jsonl path or vice-versa).
- Epistemic note: only `LOCK` (§7) and `PROMOTE` (§13) have field bodies SPECIFIED in DATA_MODEL,
  so only those variant bodies are field-enforced. The other `event_type` enum members
  (RESOLVE/VOID/DISPUTE/CORRECT · REFRESH/REJECT/SUPERSEDE) are the README per-log vocabularies
  normalized to imperative verbs to match those two anchors; their bodies stay at the common
  shape until DATA_MODEL specifies them (a real such event currently fails closed on unknown
  fields — the safe direction). No invented required fields; no documented field dropped.
- Acceptance: valid prediction + valid LOCK + valid PROMOTE + empty seeds → 0; prob-out-of-range
  / resolve-before-as-of / authority-not-source / unknown-field / LOCK-missing-record_hash /
  bad-event_type / bad-event_hash / dup-JSON-key / PROMOTE-missing-hash / PROMOTE-bad-hashlist →
  1; unrecognized `.jsonl` → 2. Full suite 123 passed (R1 golden vector + R2 conformance intact).
- Oracle-data changes: none. Factbase seeding: none (seeds stay empty). Separate review: PASS
  (8/8 new detectors mutation-proven load-bearing; every invalid fixture fails for its named
  reason; no scope creep; fields faithful to §7/§13; diff additive & confined; oracle untouched).
- Commit: see git log. Next: WP1.6 (observation `unit_vocabulary` + analysis/refuter/geography/
  baseline/visual schemas — fattest WP, sub-commits allowed; SURFACE `unit_vocabulary` to owner).

### WP1.6 — Observation + geography + analysis/refuter/visual; Phase-1 freeze [DONE]

- 1.6a (5ba5ab8): `config/unit_vocabulary.yaml` (owner-editable unit→dimensional-class registry,
  self-validating; the one domain call surfaced at the freeze checkpoint). OBSERVATION_SCHEMA
  (obs-, V-P1-5 schema half: numeric obs bind `source_value`/`source_unit` + a vocabulary `unit`
  and must DECLARE a transformation for any unit/denominator recast — correctness + the dimensional
  A5 kill stay WP2.8). GEOGRAPHY_SCHEMA (geo-: geometry by ref+hash, EPSG crs, GeoJSON type,
  spatial_semantics). 20 tests.
- 1.6b (f570977): ANALYSIS_SCHEMA (ana-), REFUTER_SCHEMA (ref-), VISUAL_SCHEMA (vis-) + a shared
  `_check_ref_list` enforcing CLOSED hash-bound ref entries. Shape only — refuter set-equality
  coverage, marker↔answer agreement, cross-record hash resolution stay Phase 3. 15 tests
  (+ the review-found CATEGORY-unit-null coverage fixture).
- Phase-1 exit gate (a5f75b1): `scripts/gate_phase1_exit.py` — three fail-closed witnesses (R1
  golden vector second copy · R5 skeleton composes through every schema · seeds clean), exit 0/2,
  mutation-proven load-bearing. Milestone-A synthetic skeleton `tests/fixtures/skeleton/` (13
  files, one referentially-consistent chain; synthetic/fixtures-only, format-valid placeholder
  hashes — real record_hash at the Phase-2 hash gate) + `test_milestone_a_skeleton.py` (validates,
  pins oracle completeness, checks internal coherence).
- Epistemic notes: enums normalized from prose (geometry_type GeoJSON set, spatial_semantics §12,
  CHECK_RESULT's FAIL, ANALYSIS_LIFECYCLE {DRAFT,ANSWER}) are doc-grounded; `REQUIRED_REFUTER_CLASS`
  is the single documented token `{HUMAN_OR_DIFFERENT_MODEL}` — a Phase-3 WATCH-ITEM to widen if a
  weaker tiered required-class token is ever introduced (inline `expand if specified` flag).
- Separate review (WP1.6, both sub-commits): PASS — 15/15 new detectors mutation-proven load-bearing
  (one coverage gap found + fixed: CATEGORY-unit-null); fields faithful to §6/§9/§10/§11/§12; no
  scope creep (dimensional/coverage/resolution all deferred); unit_vocabulary fail-closed + self-
  validating; oracle/factbase untouched. Full suite 160; gate PASS. Next: Phase 2 (WP2.1 →).

### WP2.1 — Source registry integrity gate [DONE]

- Shipped: `scripts/validate_sources.py` — the first Phase-2 integrity gate (DAG root). Schema first
  (`vs.validate_file`: unparseable→2, shape-broken→1 without integrity), then cross-record integrity
  on a clean parse: global ID uniqueness across sources+groups (one namespace), group `member_ids`
  resolve to a known `src-` (not `grp-`), active-window coherence. Read-only. `tests/test_source_
  integrity.py` (8 tests) + `src_*` fixtures.
- Scope: the "group ID may not stand where a source is required" rule is deferred to the CONSUMING
  gates (WP2.2–2.3); WP2.1 keeps the registry itself coherent. `citable:false` stays at the schema.
- Acceptance: valid registry + **real `factbase/sources.yaml` (29 sources, 2 groups)** → 0;
  dup-id / unresolved-member / member-is-group / inverted-window → 1; schema-broken → 1 (schema
  layer, integrity not run); unparseable → 2. Full suite 168.
- Separate review: PASS — gate confirmed READ-ONLY (factbase byte-unchanged), layering correct,
  exit-2 never downgraded, no scope creep. Review found two non-load-bearing tests (a backstopping
  rule masked the named one); FIXED — added a dup-only fixture + assert the specific finding message
  (tamper-evidence verified: neutering the prefix branch now fails its test).
- Oracle/factbase changes: none. Commit: see git log. Next: WP2.2 (assessment governance +
  `high_impact` gate-recompute V-P0-1 + the same-change reward-hack gate across a commit range).

### WP2.2 — Assessment governance + high_impact recompute (P0) + reward-hack gate [DONE]

Three gates under one WP number (kept as separate scripts, each independently green); designed via
a multi-agent design workflow, then adversarially reviewed by a worktree-isolated multi-agent
review (verdict FIX_REQUIRED → all confirmed findings fixed-forward, re-reviewed green).

- 2.2a (0a12634) — **the P0 fix.** `scripts/validate_high_impact.py` recomputes `high_impact` and
  raises a stored false/null that should be true: T1 (topics ∩ trigger tokens, exact-token
  NFC+casefold) OR T2-pred (FALSIFIABLE projection feeds a prediction). Trigger tokens = owner-
  editable oracle config `config/high_impact_triggers.yaml` (alias resolves §10 `territorial-control`
  vs the binding adjudication-row `control`). Only false→true enforced (lower bound); stored true
  accepted with a printed [deferred] notice (manifest/visual = WP3.2/Ph5, contradiction = WP2.6, are
  not computable at records scope); refuter-contest is WP3.3. Empty trigger config → exit 2 (§13).
- 2.2b (8cb9132) — `scripts/validate_assessment_governance.py`: structural single-file supersession
  integrity (no self-supersede / orphan / cycle; one active leaf per chain) + non-empty provenance.
- 2.2c (196872b) — `scripts/check_reward_hack.py`: cross-commit (base..head) reward-hack gate
  (V-P1-7). R-RH (oracle + factbase record M/D), R-EDIT (in-place committed-assessment edit, by
  record_hash), R-DELETE, R-HI (claim high_impact true→false or §10 trigger-input change), R-COLLUDE
  (assessment + benefiting claim/claim-evidence change). DATA = `factbase/**` only (tests/config/
  scripts = ORACLE, so normal TDD doesn't false-positive). Carve-outs: anchored Reviewed-separately
  trailer on every commit clears R-RH/R-COLLUDE (not R-EDIT/R-DELETE/R-HI); net-new data doesn't
  trip. `--base` required, fail-closed exit 2. Pure `evaluate()` + git wrapper.
- Hardening (58c838f) — the adversarial review found evasions in untested paths (all reproduced):
  M1 `high_impact: null` bypassed both layers → gate `stored is not True` + schema forbids null;
  M2 a `git mv` hid a renamed+edited claim → `--no-renames` + global-by-id reconciliation;
  M3 R-COLLUDE ignored the claim-evidence benefit layer → now diffs cea stance/credibility;
  S1 R-EDIT only watched reliability → record_hash catches any in-place edit; S2 blank-provenance
  bypass (null/non-string/zero-width) closed; S3 R-HI trigger inputs completed (epistemic_type/
  projection_kind). +11 regression tests.
- Acceptance: full suite **221 green**; Phase-1 exit gate PASS; the gate is clean on the real WP2.2
  range (no false positive). Oracle/governing-doc changes: none. Factbase seeding: none.
- Discharged: **V-P0-1** (gate-computed high_impact — the #1 cold-review finding, gate half; refuter
  half is WP3.3), **V-P1-7** (commit-range reward-hack), assessment append-only governance
  (DATA_MODEL §2/§14, IMPLEMENTATION_PLAN WP2.2 incl. the social-source-upgrade fixture).
- Next: WP2.3 (artifact integrity + claim-evidence governance).

### WP2.3 — Evidence-artifact integrity + claim-evidence governance [DONE]

Designed via a design workflow (critic APPROVE), built solo, then adversarially reviewed by a
worktree-isolated multi-agent review (verdict **PASS**, no must-fix; 2 should-fix + watch items
closed under boil-the-lake). Five commits.

- 2.3b-0 (d569544) — extracted `scripts/supersession.py` (one-active-leaf union-find), made it
  partition-aware, repointed WP2.2b at it (behavior-preserving).
- 2.3a (279857e) — `scripts/validate_evidence.py`: artifact id uniqueness; `source_id` RESOLVES to
  a known `src-` (cross-file vs sources.yaml — WP2.1 deferred this here); content-hash uniqueness
  (two artifacts sharing a hash = one artifact); date coherence; group-as-source defensive (the
  schema's `ref:src-` already rejects `grp-` here — reachable case is origin_chain in 2.3b).
- 2.3b (8544a89) — `scripts/validate_claim_evidence.py`: cea id uniqueness; claim_id/artifact_id
  resolution; origin_chain source resolution + the REACHABLE group-as-source; one active leaf per
  `(claim_id, artifact_id)` chain + no cross-pair supersede edge; CHECKED `artifact_hash` ==
  resolved evidence `content_hash`. Cross-file fail-closed (any missing registry → exit 2).
- Hardening (f25a8a7) — `schema_defs.iso_instant` replaces the lexical date compare in R-EVD-5 AND
  `_prediction_extra` (the lexical compare false-positived on date-only-vs-datetime + fractional
  widths, rejecting legal input); `superseded` set made partition-aware (sounds the shared helper);
  +6 coverage/regression tests (dup-id, origin artifact resolution, baseline+live claims union,
  date no-false-positive).
- DEFERRED (explicit): cea-on-ASSUMPTION → WP2.4; `claim_content_hash`/`relationship_input_hash`
  equality (verified not reproducible from `record_hash` — would false-fail); terminal-origin
  independence-group multi-group → WP2.5/2.6; stance/credibility VALUES → WP2.5; conflict → WP2.6;
  cross-commit evidence immutability → a future WP2.2c-family gap (tracked in the gate docstring).
- Acceptance: full suite **253 green**; Phase-1 gate PASS; gates dogfood the empty factbase +
  the Milestone-A skeleton (CHECKED artifact_hash matches) at exit 0. Oracle/factbase changes: none.
- Next: WP2.4 (type-specific claim integrity — also owns the deferred cea-on-ASSUMPTION rule).

### WP2.4 — Type-specific claim integrity [DONE]

Designed via a design workflow (critic REVISE — its findings folded in: fixed the canonical
fixture, deferred the un-oracled rules), built solo, adversarially reviewed (verdict **PASS**;
1 real should-fix bug + 2 coverage gaps fixed-forward). Two commits (2a88f33 + 53e0d6f hardening).

- `scripts/validate_claims.py` (CONSTITUTION §4/§5, DATA_MODEL §5/§14): R-CLM-1 claim id uniqueness
  across the baseline+live UNION; R-CLM-2 INFERENCE premise resolution; R-CLM-5 active cea on an
  ASSUMPTION (DATA_MODEL §4 — **WP2.4 owns it, resolving the WP2.3b deferral**; active = un-superseded
  leaf, partition-scoped to `(claim_id, artifact_id)`, & not REJECTED); R-CLM-6 FALSIFIABLE
  prediction_id resolution; R-CLM-8 PROJECTION ≠ CORROBORATED; R-CLM-12 claim supersession via the
  shared helper. Schema-first; cea + prediction registries required (unreadable → exit 2); empty → 0.
- Review-found bug (fixed): R-CLM-5's `superseded` set was global → a cross-pair supersedes edge
  masked an active assumption cea; now partition-scoped (same class as the WP2.3 fix). +5 tests.
- **DEFERRED for owner ratification (surfaced, NOT shipped — §13 gate-rules-live-in-the-oracle):**
  premise **acyclicity**, and `review_by`/`expires_at` ≥ `created_at` **ordering**. Zero-false-
  positive structural invariants recommended for Constitution §4/§6.5; off until ratified. (The
  WP2.3 `retrieved_at ≥ published_at` ASSUMED check is in the same ratification basket.)
- Deferred by charter: support VALUE → WP2.5; conflict → WP2.6; freshness CLOCK → WP2.7;
  cross-commit in-place claim edits → WP2.2c family; high_impact recompute → WP2.2a; `scenario_id`
  has no registry (not invented).
- Acceptance: full suite **271 green**; Phase-1 gate PASS; empty factbase + skeleton dogfood at 0.
  Oracle/factbase changes: none. Next: **WP2.5** (hardest — support + corroboration: primary_evidence
  _kind + credibility floor + Tier-1 cap; kills the A1 exploit).

## Phase checklist

### Phase 0 — Governance and scaffold

- [x] WP0.0 Review-adjudication gate — **DONE**
- [x] WP0.1 Repository scaffold and unified verifier — **DONE**
- [x] WP0.2 Sensitive-locator and secret hygiene — **DONE**
- [x] WP0.3 Tier-0 conversational labeling contract — **DONE** (Phase 0 complete)

### Phase 1 — Closed schemas and migration *(gate cleared 2026-06-22; WP1.7 deferred)*

- [x] WP1.1 Envelope validator and schema registry — **DONE**
- [x] WP1.2 Source entities, groups, and assessments — **DONE**
- [x] WP1.3 Type-specific claim schema — **DONE**
- [x] WP1.4 Evidence artifact and claim-evidence assessment schemas — **DONE**
- [x] WP1.5 Prediction and append-only event schemas — **DONE** (baseline-event folded in here)
- [x] WP1.6 Observation, analysis, refuter, geography, and visual schemas — **DONE** (1.6a + 1.6b)
- [x] Phase-1 exit gate + Milestone-A skeleton oracle — **DONE** (gate PASS)
- [ ] WP1.7 Migration framework — **DEFERRED** (no v1 data; out of Segment-2 scope)
- **PHASE 1 COMPLETE — schema layer frozen 2026-06-22.** 160 tests; `gate_phase1_exit.py` PASS.

### Phase 2 — Source, artifact, assessment, claim, and observation integrity

- [x] WP2.1 Source registry integrity — **DONE**
- [x] WP2.2 Source-assessment governance + high_impact recompute + reward-hack gate — **DONE**
- [x] WP2.3 Artifact integrity and claim-evidence governance — **DONE**
- [x] WP2.4 Type-specific claim integrity — **DONE**
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

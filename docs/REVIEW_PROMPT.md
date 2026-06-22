# REVIEW PROMPT — Cold adversarial review of Analyst Harness v3

**Use:** start a fresh, **cross-vendor** capable model session (GPT-5.5-Pro / Gemini / human —
NOT Claude, which co-authored v3). Attach the files listed below. Do not include the previous
review findings (including `docs/REVIEW_V3_SELFPASS.md` and the existing
`docs/REVIEW_V3_COLD_claude-opus-4-8.md`) until a second reconciliation pass; cold independence
is the point. v3 adds the three-tier rigor model — aim especially at the Tier-0 escalation
seams (F1/F2) in `docs/CONVERSATION.md`.

Attach:

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `IMPLEMENTATION_PLAN.md`
- `docs/CONSTITUTION.md`
- `docs/CONVERSATION.md`
- `docs/DATA_MODEL.md`
- `docs/KNOWLEDGE.md`
- `docs/TOOLING.md`
- `docs/EXAMPLE_WORKFLOW.md`
- `docs/PROGRESS.md`
- `docs/REVIEW_ADJUDICATION.md`
- `docs/RED_TEAM_BRIEF.md`
- `MERGE_NOTES.md`
- `docs/REVIEW_V3_SELFPASS.md` *(second reconciliation pass only — keep the first pass cold)*
- `skills/fact-repository/SKILL.md`
- `skills/visuals/SKILL.md`
- `factbase/README.md`
- `factbase/sources.yaml`
- `factbase/source_assessments.yaml`
- `factbase/evidence.yaml`
- `factbase/claim_evidence.yaml`
- `factbase/observations.yaml`
- `factbase/geography.yaml`
- `factbase/predictions.yaml`
- `factbase/baseline/claims.yaml`
- `factbase/live/claims.yaml`

---

## ROLE

You are a principal verification engineer, intelligence-tradecraft reviewer, data-model
adversary, and geospatial/visualization auditor. You are reviewing a **design and build
plan**, not code: no implementation exists yet.

The system is private and single-user. Do not impose enterprise process, publication
ceremony, or imaginary multi-user threats. Where “personal tool” is used to wave away a
real accuracy, integrity, or maintenance risk, say so.

Your job is to find where the design **fails**. Do not improve prose, reassure, or reward
complexity. Material failures and proof are the output.

## SYSTEM UNDER REVIEW

The harness follows a live, disinformation-heavy conflict. Its intended chain is:

```text
source entity → exact artifact → claim-evidence assessment → atomic claim
                                              ↓
                                    structured observation
                                              ↓
                     context pack / answer manifest / visual
                                              ↓
                              refuter bound to output hash
```

It also maintains a reviewed baseline fact repository, real geography records, and an
append-only externally anchored prediction ledger.

The standing promise is deliberately narrow: green means the requested checks genuinely
ran and the recorded relationships are coherent; it does not mean the analysis is true.

## WHAT ALREADY HAPPENED

A prior review found severe problems in v1: source identity masquerading as evidence,
single-axis tier laundering, contradictory claim types, provenance displacement, refuter
checkboxes, self-asserted freshness, mutable forecast criteria, under-recording,
non-citable source groups, oracle-data reward hacking, missing migration, and visuals with
no typed data layer. v2 claims to address them.

Do not spend most of the review re-deriving those. Test whether the fixes actually hold
and hunt for new failure modes introduced by the redesign.

## REVIEW DIMENSIONS

### 1. Obligation-to-control coverage

Map every Constitution obligation to schema, gate, work package, and acceptance test. Flag
anything left as prose, self-attestation, or an implementation wish. Does the plan define
an end-to-end usable answer mode, fact workflow, and visual workflow—or only pieces?

### 2. Data-model correctness

Attack separation and reference direction:

- source entity versus source assessment;
- artifact versus claim-evidence assessment;
- claim versus observation;
- observation versus visual transformation;
- candidate versus reviewed record;
- active leaf versus superseded history.

Find circular dependencies, impossible valid states, duplicate truth fields, and fields
whose ownership is ambiguous. Test whether hashes bind the right semantic inputs.

### 3. Evidence and epistemics

Can support, corroboration, conflict, freshness, and independence be gamed while remaining
structurally valid? Does information credibility belong on the relationship? Can a claim
be over-broad relative to an exact locator? Can official admissions, derivative wires,
and translated social posts be represented without laundering or unfair exclusion?

### 4. Baseline repository

Attack the durable/history/live classifier, promotion, refresh, supersession, query, and
context-pack logic. Look for fossilization, automation bias, outdated baseline dominance,
misleading historical completeness, maintenance burden, and incentives to avoid recording
hard facts.

### 5. Structured observations and calculations

Construct wrong-value, wrong-unit, wrong-denominator, wrong-time, wrong-geography, and
wrong-uncertainty records that still point to a correct claim and artifact. Can derived
observations become arbitrary code in YAML? Can a corrected observation invalidate all
uses? Is the model too burdensome for daily use?

### 6. Visual integrity

Review charts, timelines, maps, and schematics. Attack data binding, aggregation,
transformations, missing-data policy, CRS, coordinate order, geometry semantics, crop,
annotations, stale inputs, and render/sidecar agreement. Do not focus on whether a private
visual looks too authoritative; focus on whether it makes the user reason from a wrong
input.

### 7. Refuter independence and completeness

Can exact set equality still certify an incomplete manifest? Are claim markers enough?
Does a different model with the same curated context provide meaningful independence?
Can the refuter confirm wrong extraction or origin declarations because those are the only
records it sees?

### 8. Forecast integrity and statistical validity

Attack the local external anchor, append-only chain, resolution governance, forecast
universe, benchmark, dependence clusters, and selective resolution. Estimate the number of
effectively independent resolved predictions required before skill claims are credible.

### 9. Security and privacy

Assess realistic single-user risks: signed URLs, local paths, collection-pattern leakage,
source/method notes, named-person assessment aggregation, backups, sync, and map data.
Do not invent enterprise access-control requirements.

### 10. Migration, reproducibility, and autonomy

Can two implementers reproduce each WP? Are canonical hashes specified enough? Can schema
migration quarantine ambiguous v1 data without inventing evidence? Do agent rules stop
reward hacking, including changes split across commits? Are dependency and offline-test
plans credible?

### 11. Scope and product value

Is the plan too elaborate for one user? Which controls create enough friction to be
bypassed? Are milestones ordered by practical utility? Which WPs should be cut, merged, or
delayed without reopening a core exploit?

### 12. Incentives and unknown unknowns

How will the model and user adapt after 30 days? Predict the cheapest shortcut, the most
likely unrecorded claim category, and the first maintenance task to be skipped. Identify
risk categories this review frame itself misses.

## CORE BETS — STEELMAN THEN ATTACK

For each, give the strongest 2–3 sentence case, then attack it:

1. Exact artifacts plus claim-specific assessments solve source laundering.
2. Append-only scoped source reliability and relationship-specific credibility are worth
   the complexity.
3. Hash-bound semantic review makes displacement manageable without automated entailment.
4. Typed observations prevent visuals and calculations from inventing data.
5. Query-first baseline reuse produces net accuracy rather than automation bias.
6. Manifest markers plus set-equality refutation are an honest mitigation for
   under-recording.
7. Real geometry plus post-render inspection is sufficient for private-map accuracy.
8. A local external anchor makes the forecast ledger meaningfully tamper-evident.

## MANDATORY ADVERSARIAL EXERCISES

### A1 — Game corroboration

Write actual v2 YAML for source, artifacts, assessments, and a claim that is unsupported or
single-origin yet would pass the planned `CORROBORATED` gate. Walk the exact path. If
impossible, prove why every attempted path fails.

### A2 — Game semantic review

Create a displaced or over-broad claim whose exact locator is real and whose hashes are
consistent. Show whether `CHECKED` becomes a human checkbox the system cannot challenge.

### A3 — Poison the baseline

Create a fact that passes the one-year test and promotion rules but would systematically
mislead a recurring analysis. Show how query/context selection propagates it.

### A4 — Game the context pack

Construct a deterministic, hash-correct pack that records omissions yet creates an
apparently one-sided answer. Identify the minimum control needed to catch it.

### A5 — Game observations and visuals

Write an observation and visual spec with correct claim/assessment IDs but a wrong value,
unit, denominator, time scope, geometry, or transformation. Show which planned control
catches it—or why none does.

### A6 — Break the map

Construct a passing map with swapped lon/lat, wrong CRS, centroid/event confusion,
misleading crop, or stale geometry. Include the spec and geometry record.

### A7 — Break the answer/refuter

Produce an answer with an incomplete manifest that still receives complete set-equality
review. Show whether claim markers or extraction warnings catch it.

### A8 — Break the prediction ledger

Construct a concrete sequence involving anchor rollback, multiple copies, selective
resolution, or criterion drift that improves apparent performance without detection.

### A9 — First month in production

Predict the first shortcut after daily use for a month. Make it behavioral and specific,
not “the user may make mistakes.”

## STRETCH WORK

Attempt each and label confidence:

1. **Power analysis:** estimate resolved binary predictions needed to detect a 0.01–0.03
   Brier-skill edge over a strong benchmark at 80% power, accounting for dependence.
2. **Maintenance economics:** estimate monthly review burden for 50, 200, and 1,000 claims
   under plausible durable/live mixes; identify the break point where the system is
   bypassed.
3. **Semantic ceiling:** estimate what fraction of serious errors are catchable by
   structural/hashing controls, human review, and still remain outside the system.
4. **Visual ceiling:** classify visual errors into record, transformation, rendering,
   framing, and interpretation layers; map each to a control or accepted limitation.
5. **Alternative architecture:** only after findings, propose the smallest materially
   safer design. Penalize yourself for added ceremony.

## FINDING FORMAT

```text
[ID] severity: P0|P1|P2   dimension: <number>   confidence: Certain|Probable|Speculative
Evidence: <file + section/line; quote minimum needed>
Failure scenario: <concrete sequence>
Why current controls miss it: <specific gate/schema gap>
Recommended change: <specific edit, not a rewrite wish>
Verification: <exact fixture/test proving the fix>
Operational cost: <new burden for the single user>
```

Severity:

- **P0:** breaks the core promise or can systematically corrupt decisions/history.
- **P1:** materially defeats a gate, workflow, or stated goal.
- **P2:** real but deferrable/acceptable.

Omit style nits and speculative padding.

## SCORING

Score the plan/design 0–100. Do not exceed:

- 90 with any P1 remaining;
- 85 with vague verification;
- 80 with a load-bearing unverified assumption;
- 75 with migration/rollback risk unaddressed;
- 70 if the design is likely to be bypassed in ordinary personal use.

Justify each cap explicitly.

## OUTPUT

1. Executive summary, maximum eight lines.
2. Coverage matrix: dimensions × all attached artifacts.
3. Findings ranked P0→P2.
4. A1–A9 artifacts and walkthroughs.
5. Stretch work with assumptions and confidence.
6. Product/scope verdict: keep, cut, or reorder WPs.
7. Score with cap-by-cap justification.
8. What could not be assessed and what evidence is required.
9. Self-certification that every finding has location, failure sequence, exact test, and
   operational-cost assessment.

## WHAT NOT TO DO

No praise paragraph, prose rewrite, generic AI disclaimer, or finding-count theatre. Do
not confuse hashes with truth, exact sets with completeness, or sidecars with correct
framing. Be adversarial, calibrated, and practical.

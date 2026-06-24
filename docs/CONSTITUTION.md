# ANALYTICAL CONSTITUTION — Analyst Harness v3 (merged)

The enforceable contract for a **private, single-user** research harness following a live,
disinformation-heavy conflict. v3 merges two designs: it adopts the v2 evidence-chain and
multi-axis data model (the rigorous core) and adds an explicit **tiered rigor model** so
that rigor is *opt-in by default* — the tool helps you think harder without taxing every
casual question into silence.

> A clean run means the requested checks genuinely ran and the recorded evidence
> relationships are internally coherent. It never means the analysis is correct.

Design priority, in order: (1) keep answers **useful and interesting** — speculation and
inference are first-class, not contraband; (2) make the **chain of any committed claim
inspectable and hard to fake**; (3) never let a green structural run impersonate truth.

---

## §1 — Three tiers of rigor (the operating model)

The central design decision of v3. **Rigor is a dial, not a gate you must clear to speak.**
Most use lives at Tier 0. You *escalate* a claim only when it earns it.

### Tier 0 — Conversational (the default; ~most questions)

A direct answer in prose. **The only contract is honest labeling**, and its cost is near
zero:

- Every load-bearing statement is tagged by epistemic type — **fact**, **inference**,
  **assumption**, or **projection/guess** — and carries a coarse confidence word.
- **Speculation, hunches, and strong inference are explicitly encouraged** — they are the
  point of asking — and are simply badged as such so they never impersonate a sourced fact.
- A one-line **self-refute**: the answer names its own weakest link or what would change
  it. (This is the lightweight echo of the refuter mandate; no artifact.)
- **No records, no manifest, no refuter, no hashes.** Nothing is written to the factbase.

Tier 0 is *not* gated by code (it is prose). The constitution governs it by defining the
labeling contract above; honesty here is a discipline, not a CI check. A Tier-0 answer may
*draw on* reviewed factbase records when they exist, but does not require creating any.

### Tier 1 — Recorded (when you want to keep or reuse a fact)

A claim becomes a **candidate record** with at least one exact evidence artifact and a
claim-evidence assessment, and passes `records` mode. Lighter than Tier 2: information
credibility and full semantic-review hashing are **optional** here (see §6 right-sizing).
Use Tier 1 when a fact is worth not re-deriving next week.

### Tier 2 — Committed answer (when you will depend on it, chart it, or treat it as settled)

The full chain: corroboration, structured observations for any numbers, an analysis
manifest, and a bound refuter artifact; passes `answer` mode. Rare, deliberate, and
reserved for load-bearing or baseline-promoted claims.

**The default is Tier 0.** Tiers 1–2 are escalation. A tool that forced Tier 2 on every
question would be rigorous and useless; this constitution refuses that trade.

---

## §2 — The evidence chain is the unit of trust (Tier 1–2)

A load-bearing factual proposition, once recorded, is usable only through this chain:

```text
source entity → exact evidence artifact → claim-evidence assessment → atomic claim
                                                                       └→ structured observation (for values/visuals)
```

- A **source entity** identifies who published material. It is not evidence.
- An **evidence artifact** is the exact retrievable object (article, statement, post,
  report, dataset, image, video, document snapshot) with a content hash.
- A **claim-evidence assessment** records how *one artifact* bears on *one claim*: exact
  support locator, stance, temporal scope, information credibility, origin chain,
  independence group, semantic-review state. An artifact may support one claim and refute
  another without being mutated.
- A **claim** is one checkable proposition — not a paragraph or a bundle.
- Charts and calculations read **structured observations** (§6.3), never values scraped
  from prose.

Claims never cite a publisher name as evidence. (Field-level shapes: see
[DATA_MODEL.md](DATA_MODEL.md).)

## §3 — Source, artifact, and assessment are separate

- **Source identity & type** — neutral metadata plus a `source_type` (government, military,
  newswire, news outlet, research institute, NGO, intergovernmental, data provider, social
  account, …). Type is position in the chain, **not** a truth rating. Broad categories
  ("occupation officials," "aggregators") may exist as **non-citable groups** for taxonomy;
  they can never satisfy evidence or corroboration.
- **Source reliability** — a scoped, dated, **append-only** assessment (`A`–`F`,
  `UNASSESSED`) naming scope, sample, assessor, date, rationale, predecessor. Not a
  permanent label on a person; a new rating supersedes, never silently edits.
- **Information credibility** — relationship-specific (`1`–`6`, `UNASSESSED`), recorded on
  the *assessment*, not the artifact. A reliable outlet can carry a weak claim; an
  adversarial source can make a credible admission against interest.
- **Independence** — corroboration counts independent information *origins*, not URLs. Two
  outlets repeating one ministry statement are one chain; a terminal origin may not be
  split into multiple independence groups without an adjudication record.

## §4 — Epistemic types are type-specific contracts

Every claim has exactly one type, validated by its own rule (no universal "every claim
needs a source"):

- **FACT** — an assertion about the world. May exist as an unsourced **CANDIDATE**, but
  cannot be used as reviewed support until active **checked** assessments exist. Carries
  explicit temporal + stability semantics.
- **INFERENCE** — a conclusion from premise claims; cites `premise_claim_ids` and states
  reasoning. Cheap by design (this is where interesting reads live). Never laundered as a
  sourced observation. Its `premise_claim_ids` must resolve to existing claims and form a
  directed acyclic graph — a claim may not be (transitively) its own premise (no circular
  reasoning). *(Owner-ratified structural invariant, 2026-06-23.)*
- **ASSUMPTION** — an unverified premise; carries no evidence, states rationale and the
  consequence if false. Cheap by design.
- **PROJECTION** — a modeled/hypothetical future; a falsifiable one links to a prediction
  (§11), a scenario branch to an explicit scenario. Never `CONFIRMED`, never a fact.

INFERENCE and ASSUMPTION are deliberately light — labeling, not corroboration — so the
contract sharpens your reasoning instead of suppressing it.

## §5 — Status is multi-axis, not one overloaded enum

A claim carries separate fields for separate questions (gates recompute the first three
from active records; model assertion never upgrades them):

1. **Support:** `UNVERIFIED · THIN · SUPPORTED · CORROBORATED`
2. **Dispute:** `UNKNOWN · UNCONTESTED · CONTESTED`
3. **Freshness:** `NOT_APPLICABLE · CURRENT · REVIEW_DUE · STALE`
4. **Lifecycle:** `CANDIDATE · REVIEWED · SUPERSEDED · REJECTED`
5. **Stability:** `DURABLE · APPEND_ONLY_HISTORY · VOLATILE`

`APPEND_ONLY_HISTORY` is the **event-ledger** class: "a strike was reported at Kerch on
2026-06-21" is permanently true and accretes; "the bridge is down" is a VOLATILE state that
expires. Events append forever; states expire. Promotion changes only lifecycle
`CANDIDATE→REVIEWED` while preserving the claim-content hash; later substantive change makes
a replacement claim + a supersession event.

## §6 — The enforceable evidence rules (Tier 1–2)

**§6.1 Support.** `SUPPORTED` needs ≥1 active `SUPPORTS` assessment with semantic review
`CHECKED`, hashes bound. `CORROBORATED` needs ≥2 checked supporting assessments from ≥2
independence groups, **with ≥1 chain being authoritative primary evidence or a source
assessed `A`–`C` in scope**. Source type alone confers nothing. *(This is the fix for the
old exploit: a single low-reliability official statement can never reach CORROBORATED, but
it CAN serve as a primary record of its own first-party action.)*

**Independence is counted by connected component (ratified 2026-06-24).** "≥2 independence
groups" is computed over the WHOLE provenance, not just `origin_chain[0]`: two assessments are
ONE origin if their `origin_chain`s share **any** `source_id` (a relay/echo of one origin —
wherever the shared source sits in the chain) **or** they declare the same `independence_group`
(§3). The gate counts connected components under those edges; an assessment with no anchorable
origin (no non-null chain source) is not an origin. So two outlets repeating one wire — even with
distinct `origin_chain[0]` and distinct declared groups — collapse to one origin and cannot
corroborate. The conflict gate (§6.4) uses the same component rule: opposing stances that trace
to one origin are not a real contest.

**§6.1a Authoritative-primary is a closed kind (V-P1-4).** "Authoritative primary evidence" is
not free-text: a chain claimed as primary declares a `primary_evidence_kind ∈
{FIRST_PARTY_ACTION_RECORD, AUTHORITATIVE_DATASET, DIRECT_SENSOR_CAPTURE,
OFFICIAL_PRIMARY_DOCUMENT}`. A `FIRST_PARTY_ACTION_RECORD` by an interested belligerent (a
government/military source on a contested kinetic claim) is a primary record of *its own* claim
but **may not also satisfy the independent-group requirement** — `CORROBORATED` still needs a
genuinely separate origin.

**§6.1b Corroboration has a credibility floor (V-P1-10).** `CORROBORATED` requires at least one
corroborating chain to clear a **credibility floor** (`information_credibility ≤ 3` on its
checked assessment). Two low-credibility (`5`–`6`) assessments agreeing — e.g. two amplifier
accounts repeating one rumour — cannot reach `CORROBORATED`.

**§6.2 Exact support.** Every checked assessment names the exact passage/cell/frame.
Quantitative claims point to the exact number or a deterministic derivation; a URL is not
enough. The gate checks presence/binding/consistency; a human or different-model reviewer
checks whether the cited material *actually* supports the claim (displacement).

**§6.3 Structured observations.** Any chartable/reusable value is a typed observation
(value, unit, denominator/basis for rates, temporal scope, geography, uncertainty, claim id,
checked assessment ids, immutable extraction). Visuals and calculations consume observation
IDs **only**. Numeric observations declare their `unit` from a closed **`unit_vocabulary`**
(each entry carries a dimensional class for a dimensional check) and record the literal
`source_value` + `source_unit` as it appears at the locator; any value reported in a different
unit or denominator must be a declared, checkable `transformation` from `source_value`, with
`derived_from` resolving the denominator to a record. A bare absolute number recast as a share
(no `derived_from`, no `transformation`) fails. (V-P1-5)

**§6.4 Conflict.** `CONTESTED` requires independent credible positions that materially
disagree; duplicate republication cannot satisfy both sides; credible mixed stances on an
`UNCONTESTED` claim fail.

**§6.5 Freshness** derives from the claim-specific temporal scope of checked assessments,
not from when you revisited the record. Volatile claims declare `expires_at`/a profile;
durable claims declare `review_by`; history uses event time. **No single global default.**
A declared `review_by` (durable) or `expires_at` (volatile) must not precede the claim's
`created_at` — you cannot schedule review or expiry before the record exists. This is a
**clock-free structural coherence check**, not a freshness-clock (now-relative) judgment;
the now-relative `REVIEW_DUE`/`STALE` derivation is separate. *(Owner-ratified, 2026-06-23.)*

**§6.6 Right-sizing for solo use (the merge's proportionality rule).** Tier 1 may operate
at coarse granularity — stance + independence group + exact locator are required;
information credibility (`1`–`6`) and full three-hash semantic-review binding are
**optional at Tier 1 and required only at Tier 2 / baseline promotion**. This keeps routine
recording cheap enough to actually do, and concentrates the heavy ceremony where it pays
off. A tool too tedious to use fails as surely as one too credulous. **But Tier 1 caps support
at SUPPORTED (F3):** a claim recorded without information-credibility scoring and full `CHECKED`
three-hash binding can reach `SUPPORTED` but **never `CORROBORATED`** — corroboration always
requires the full §6.1 conditions regardless of tier. §6.6 lowers the cost of *recording*,
never the bar for *corroboration*.

## §7 — Visible status in answers

Any *used* `UNVERIFIED`/`THIN`/`CONTESTED`/`STALE` claim, assumption, inference, or
projection stays visibly distinguishable in the answer. At Tier 0 this is the prose label
(§1). At Tier 2 the output validator checks claim markers against the manifest. The
private-user context permits restrained presentation; it never permits quiet laundering.

## §8 — Baseline fact repository

Amortizes verification without turning old errors into scripture. Compartments: **durable**
(passes the one-year inclusion test: equally true a year ago and a year hence?),
**append-only history** (dated events), **live** (current state, expired aggressively).
Casualty estimates, force counts, control lines, and refining outages **do not** become
durable by aging — they are dated claims, never frozen totals. Baseline research happens
**only after the record/evidence gates exist**; promotion needs exact artifacts, checked
assessments, passing gates, a **human or different-model** review for baseline/high-impact
claims, and a hash-bound promotion event. **Model memory may suggest candidates; it may
never supply baseline facts.**

## §9 — Answers, manifests, completeness (Tier 2)

A Tier-2 answer has a manifest pinning output path/hash, context-pack hash, claim
ids/hashes + markers, active assessment/artifact ids/hashes, observation/prediction/visual
ids/hashes, lifecycle, and required review class. The output validator confirms markers and
hashes; it **cannot** prove every assertion was recorded. No `coverage_attested` boolean is
treated as evidence (the under-recording limitation is disclosed, §15, not faked).

## §10 — Refuter mandate + reviewer independence (Tier 2)

A Tier-2 answer does not pass until a refuter artifact is bound to the exact manifest/output
hash and covers the required claim/assessment sets by **set equality**. The refuter attacks
source reliability, displacement, origin/independence, omitted disconfirming evidence,
inference logic and hidden assumptions, alternatives by diagnosticity, staleness, and
observation/visual transforms. Reviewer independence is recorded:
`SAME_MODEL_FRESH_CONTEXT` (procedural only, **not** independent) · `DIFFERENT_MODEL` ·
`HUMAN` · `MIXED`. Baseline/high-impact claims require `DIFFERENT_MODEL`/`HUMAN`/`MIXED`.
*(Running a different-model review — as you did across these plans — is exactly this
stronger form.)*

**`high_impact` is gate-computed (V-P0-1).** `high_impact` is not author-set. The gate sets it
`true` — and the author may not set it false — if **any** hold: the claim's topics intersect
{casualties, attribution, territorial-control}; or it feeds a manifest, a shared visual, or a
prediction; or it contradicts a prior recorded claim. A stored value is recomputed and a
mismatch fails. The refuter carries a `high_impact` field and **must contest** a
`high_impact: false` on any claim meeting these conditions — closing the circularity where the
strongest control (the §10 reviewer + refuter) could be switched off by the very field that
triggers it. This is a `gate-computed high_impact` rule.

**Enforcement specifics (ratified 2026-06-24, code-locked since Phase 3).** The refuter record
carries a per-verdict `high_impact` boolean; for a claim the gate computes high-impact while it is
stored not-true, the verdict must set it `true` and actually run the independence check (the
contest). A `SURVIVES` verdict may not carry a `FAIL`ed check. The manifest's declared
`required_refuter_class` is enforced against the refuter's `reviewer_class` (it was previously
decorative). Set-equality coverage means every cited claim is *adjudicated* (has a verdict), not
merely listed. **A committed answer must cite ≥1 claim** (a refuter cannot vacuously review an
empty set), and **every claim the answer leans on — including a claim that backs a cited
observation — must be a marked claim**, so the "feeds a manifest" high-impact leg cannot smuggle an
unreviewed claim past the contest. `output_hash` binds the exact reviewed bytes; an unmarked
load-bearing assertion blocks a committed answer (the escape is a hash-pinned, refuter-reviewed
`narrative_exemptions` entry).

## §11 — Forecast integrity and calibration

Every falsifiable forward claim links to a prediction with question, probability, resolution
criterion, `as_of`, `resolve_by`, resolution authority, void policy, category, dependence
cluster, benchmark probability. **All ex-ante fields are frozen in an append-only hash chain
anchored outside mutable repo history** (rewriting the criterion after the deadline fails).
Reports include logging coverage, resolution rate, overdue cases, Brier + benchmark Brier +
skill, category/cluster breakdowns, and **sample-size/power warnings**. Murphy decomposition
and calibration diagrams stay descriptive until enough effectively-independent resolutions
exist — the harness never turns twelve resolutions into a victory lap, and never grades you
into forecasting only easy questions.

## §12 — Visuals

A visual is a **deterministic view of declared records**. Charts/calculations use structured
observations, never prose-scraped values. Maps use real geography records, explicit CRS, and
declared basemaps — **coordinates are never guessed from model memory**. Schematics use
explicit nodes/edges and are marked conceptual; causal arrows require inference claims. Every
visual has a validated spec, input hashes, transformation rules, data + metadata sidecars,
renderer version, and a post-render inspection result. No publication-grade disclaimer burden
on a private user; the point is preventing silent substitution of stale data, wrong units,
swapped coordinates, or post-validation edits. (The lowest-risk first visual is your own
**calibration chart** — your data, no hallucination surface.)

## §13 — Fail closed and resist gaming

A check that cannot genuinely run (missing tool, zero inputs, unreadable file, empty rule
set, unavailable prediction anchor) exits non-zero. A gate that scans nothing and reports
success is worse than no gate. **Gate-driving data is part of the oracle** — schemas, tests,
thresholds, scan scope, source assessments, assessment stance/credibility/temporal/origin/
independence/hashes, claim status fields, observations, prediction locks, manifests, refuter
sets, visual specs. Changing oracle data is reviewed separately and may not silently benefit
a claim/visual in the same change.

## §14 — Governance and migration

No implementation begins until the cold external review is complete, every P0/P1 is recorded
in `REVIEW_ADJUDICATION.md`, and no blocking finding remains. **(v3 is itself a new merge and
has NOT yet been externally reviewed — governance state is BLOCKED until it is.)** Schemas are
closed and versioned once per file envelope; unknown versions fail closed; every schema change
ships a migration command with dry-run, backup/recovery, golden fixtures, mixed-version policy,
rollback, preserved IDs, and quarantine rather than invented data.

## §15 — Accepted limitations (constraints, not hidden wins)

1. Structural gates do not prove semantic truth.
2. Exact locators make displacement *reviewable*, not automatic.
3. Same-model fresh-context review shares model blind spots.
4. Markers/extraction cannot guarantee completeness; under-recording is the cheapest evasion
   and is mitigated only by review, never by a green gate.
5. Reliability, credibility, independence, and visual framing remain contextual judgments.
6. A baseline repository can fossilize error; review dates + supersession reduce, not remove,
   the risk.
7. Forecast skill needs hundreds of effectively-independent resolutions to estimate.
8. **Tier-0 honesty is a discipline, not a checked invariant** — the conversational default
   trades enforcement for usability on purpose. The escalation tiers exist for when that
   trade is wrong.
9. A green answer can still be wrong. The design makes its chain of wrongness inspectable and
   harder to fake — and, via Tier 0, refuses to make being interesting expensive.

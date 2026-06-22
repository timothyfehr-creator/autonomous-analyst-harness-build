# COLD REVIEW — Analyst Harness v3 (reviewer: Claude Opus 4.8)

**Date:** 2026-06-22 · **Target:** `analyst-harness-v3` design/build package (no code yet) ·
**Method:** multi-agent adversarial workflow (12 dimensions + 8 core-bet steelman/attacks +
A1–A9 exploit exercises + an F1–F6 tier-seam reconciliation pass + 5 stretch analyses),
122 raw findings → triaged here.

> ## ⚠️ Independence & method caveats — read first
> 1. **Not independent.** v3 was co-authored by **Claude (Opus) + GPT 5.5 Pro**. This review is
>    by **Claude Opus 4.8** — per the Constitution's own §10 / §15.3 it is a *same-family*
>    pass, **not** a clean cross-vendor `DIFFERENT_MODEL` review. A genuinely independent
>    **GPT-5.5-Pro / third-model (e.g. Gemini) / human** pass is still required to qualify any
>    high-impact finding before governance flips to READY.
> 2. **The adversarial-verification phase was lost.** The intended 3-skeptic refutation of each
>    P0/P1 failed (a script-precedence bug, then a `StructuredOutput` retry-loop stall on the
>    resume). This synthesis substitutes **the reviewing model's own single-pass adversarial
>    triage** of the 122 raw findings (cluster → test against the actual v3 docs → keep /
>    downgrade / mark-as-already-disclosed). That is **weaker** than independent skeptic panels
>    and compounds caveat (1). Treat the findings below as **strong leads adjudicated by one
>    model**, not as independently-verified verdicts.
> 3. **Does NOT unblock governance.** No edit was made to `REVIEW_ADJUDICATION.md`, `PROGRESS.md`,
>    or any factbase datum. `governance_status` remains **BLOCKED**. The adjudication rows in
>    Appendix A are *proposed*, for you to disposition.

---

## 1. Executive summary (≤8 lines)

v3 is a **genuinely strong, honest framework** — the assessment-as-record evidence chain,
multi-axis status, event-vs-state stability, non-citable source groups, and the closed
single-official-statement→CORROBORATED exploit are real improvements, and the §15 limitation
disclosures are **calibrated correctly** (the power and semantic-ceiling analyses below
confirm the design does *not* oversell). The weaknesses concentrate exactly where the merge
added surface: **the self-judged tier seams (F1/F2)** and **governance hygiene**. The single
worst issue is that **`high_impact`/`load-bearing` are self-assigned and never recomputed**, so
the strongest control (independent review / the refuter) is switched off by construction on
precisely the contested claims that need it — and the self-pass's own recommended fix was
never written into the binding docs. Closely behind: **Tier 1 has no usable recording path**,
so the v3 premise (cheap escalation) is undelivered and the dominant real-world outcome is
Tier-0 decay/abandonment. **All nine A1–A9 exploits slipped past the planned gates.** None of
this is fatal; most is fixable in the docs before WP0.0. **Score: 74/100.**

## 2. Verdict & score

**74 / 100.** Cap-by-cap justification:

- **≤90 (any surviving P1):** multiple real P1s remain → capped at 90.
- **≤80 (migration/repro risk):** the canonical-hash rule is never frozen as a golden vector
  in WP1.1 although WP1.4+ rely on it (F-CANON); applied → capped at 80.
- **Landing at 74, not lower:** the design's honesty is a genuine strength — the semantic-
  ceiling (~15–25% of serious errors caught structurally; independent review is the only layer
  that catches substance) and the forecast power analysis (~470 effectively-independent / ~1,400
  logged resolutions for a 0.02 Brier-skill edge ⇒ multi-year) both **confirm §15** rather than
  contradict it. Tier 0 is usable day-zero, so the tool is not "bypassed" (the ≤70 cap does not
  cleanly apply) — the risk is that **Tiers 1–2 see little use**, which the design half-anticipates.
- **Not higher than 74:** the v3-specific tier seams (F1/F2) are real and the self-pass's own
  fixes are unshipped; the governance scaffold has concrete must-fix inconsistencies (§6 below);
  the privacy surface is materially under-treated; and several gates over-claim what they catch
  (corroboration, observations, visuals).

## 3. What was examined

All core docs (CONSTITUTION, DATA_MODEL, IMPLEMENTATION_PLAN, EXAMPLE_WORKFLOW, KNOWLEDGE,
TOOLING, CONVERSATION, AGENTS, CLAUDE, README, START_HERE, MERGE_NOTES, REVIEW_V3_SELFPASS,
REVIEW_ADJUDICATION) and the seed `factbase/*.yaml` + both skills. Coverage spanned all 12
REVIEW_PROMPT dimensions, all 8 core bets, exercises A1–A9, and the F1–F6 tier seams.
**Not assessable:** anything requiring code execution (none exists); real reviewer-independence
of *this* pass (see caveats); and the live forecast ledger (pre-WP0.0).

---

## 4. Findings — triaged & ranked

Severity per REVIEW_PROMPT: **P0** = breaks the core promise / can systematically corrupt
decisions or history · **P1** = materially defeats a gate/workflow/goal · **P2** = real but
deferrable. Each finding notes whether it is **NEW** or **consistent with a disclosed §15
limitation** (the latter are real but already acknowledged — they bound the score less).

### P0

**P0-1 · `high_impact` / `load-bearing` are self-assigned, never gate-recomputed, and the
refuter cannot contest a false setting (F2).** `high_impact` is a bare author-set boolean
(DATA_MODEL §5) that gates the §10 `DIFFERENT_MODEL`/`HUMAN` reviewer requirement and the
bound refuter; `load-bearing` gates the refuter and is undefined in the binding docs. The
self-pass (F2) recommended "make the refuter *contest* a false setting" — that was **never
shipped**: the refuter artifact (DATA_MODEL §10) has no field for the `high_impact` boolean,
and the mechanism is **circular** (the refuter is only *required* once a claim is already
escalated, so it can never challenge a claim marked `high_impact:false`). Net: the strongest
integrity control is switched off, by construction, on exactly the casualties/attribution/
control claims that most need it. *Fix:* make `high_impact` **gate-computed** — if `topics ∩
{casualties, attribution, control}` or the claim feeds a manifest/visual/prediction, the gate
sets it true and demands the §10 class; and add a `high_impact`/`load-bearing` field to the
refuter that the reviewer must contest. *Test:* a decision-informing claim with author
`high_impact:false` and a contested topic → gate raises it and `answer` mode fails without the
required reviewer class.

### P1 (new, actionable)

**P1-1 · Tier 1 has no usable recording path → the v3 premise is undelivered (F1+F5).** The
whole point of the merge is "cheap escalation": Tier 0 default, Tier 1 = light recording. But
there is **no Tier-1 worked example, no Tier-1 skill, and no lightweight mode** — the only
worked recording path (`EXAMPLE_WORKFLOW`, the fact-repository skill) is the **full Tier-2
chain** (≈12 steps, a dozen records). Combined with **no forced Tier-0 escalation** (the
triggers are self-judged) and a **recurrence-sweep backstop that exists in no WP**, the
predicted steady state is: everything stays at Tier 0, the rigor apparatus is inert,
abandonment (not inaccuracy) is the dominant failure. *Fix:* specify a genuinely light Tier-1
path (a `fact.py candidate/assess` worked example with credibility + CHECKED-hashing optional
per §6.6) **and** implement the recurrence backstop (see queued change #1). *Test:* a Tier-1
fixture reaches `SUPPORTED` with no information_credibility and no three-hash binding.

**P1-2 · Governance scaffolding is internally incoherent — WP0.0 would fail on its own data.**
Three concrete, independently-confirmed defects: (a) **adjudication row N10 uses disposition
`MITIGATED_IN_DESIGN`, which is *not* in that file's own allowed-disposition enum**
(`RESOLVED_IN_DESIGN / PLANNED_FIX / ACCEPTED_WITH_LIMITS / BLOCKING / REJECTED_WITH_EVIDENCE`)
— WP0.0's disposition validation would flag it; (b) the design's own **F1–F6 are not logged in
`REVIEW_ADJUDICATION.md`** at all, so the governance oracle WP0.0 reads is blind to the
author's own P1s; (c) **`REVIEW_PROMPT.md` is still titled "v2"** and its attach list **omits
`CONVERSATION.md`, `MERGE_NOTES.md`, and `REVIEW_V3_SELFPASS.md`** — i.e. the cold review the
build is gated on does not attach the Tier-0 docs it is supposed to attack. *Fix:* correct the
N10 disposition; log F1–F6 with dispositions/WPs/tests; update REVIEW_PROMPT to v3 + attach the
tier docs. *Test:* `check_review_adjudication.py` rejects an out-of-enum disposition (already a
WP0.0 acceptance case — it currently *would fire on the shipped file*).

**P1-3 · Privacy surface is materially under-treated (single-user, but real harm).** (a) The
"encrypted private overlay" is referenced but **no encryption is defined or enforced** anywhere;
(b) `sources.yaml` is a reliability dossier on **29 real, named, living people** (several
in/near the conflict zone) with only a *neutrality* treatment — no at-rest, export, or
threat-model treatment; (c) real map geometry of "locations of interest" (`geodata/*.geojson`)
falls **outside both `.gitignore` and the WP0.2 scan scope**; (d) `START_HERE` recommends
**pushing the repo to GitHub** for Ultraplan, directly contradicting "private by default" with
no redaction gate between. *Fix:* define the overlay (even just "these fields/paths live only
in git-ignored `private/`, never committed"); add `geodata/` + the named-person assessments to
the WP0.2 scan; add a redaction/secret-scan gate before any push and soften the GitHub
recommendation. *Test:* WP0.2 flags a committed `geodata/*.geojson` and a private-overlay field
in a tracked assessment.

**P1-4 · "Authoritative primary evidence" is undefined + the empty seed log makes it the
*only* reachable CORROBORATED path.** §6.1 grants CORROBORATED via "≥2 independence groups, ≥1
chain authoritative-primary **or** a source assessed A–C in scope." `source_assessments.yaml`
ships **empty**, so the A–C branch is unreachable until the user hand-builds it → the undefined,
machine-uncheckable "authoritative primary evidence" clause is the sole path, and a first-party
belligerent statement + one wire echo can bootstrap CORROBORATED (A1 walked this past WP2.5).
*Fix:* define `primary_evidence_kind` as a closed enum and rule that a first-party action
record by an interested belligerent **cannot simultaneously** satisfy the independent-group leg.
*Test:* A1's YAML (RU-MoD claim + Reuters relay, two declared groups) → CORROBORATED fails.

**P1-5 · Observation/visual gates over-claim what they can catch.** WP2.8 promises to catch
"tonnes/day used as tonnes/year" and wrong-denominator, but **`unit` is unconstrained free
text** (no vocabulary, no dimensional check), **`transformation` has no grammar** (a derivation
can be opaque/non-deterministic), **`uncertainty` and `INTERVAL` have no defined shape**, and an
observation's `value` is bound to the **locator's identity, not the source number** — so an
invented or wrongly-scoped number passes all structural gates (A5). *Fix:* add a closed unit
vocabulary + dimensional check; require `source_value`+`source_unit` and a machine-checkable
`transformation` with `derived_from` resolving denominators to records. *Test:* A5's bpd-as-
share observation with `derived_from:[]` → fails.

**P1-6 · Forecast "external" anchor is not tamper-evident against the author (B8 substantially
fails).** The anchor is a same-disk, same-user, self-timestamped file → tamper-evident against
git rewrites but **not against the forecaster**, who controls repo, anchor, resolver, and clock.
A fresh clean `(repo, anchor)` pair that simply **never locked the losers** defeats all five
planned anti-tamper tests (A8); and selective resolution / void-shopping is ungated (same user
is forecaster + resolution authority + void adjudicator, with free-text `void_policy`).
Benchmark probability and `dependence_cluster` are self-declared, so both "skill vs benchmark"
and effective-N are gameable. *(Deferred phase 6.)* *Fix:* anchor head commits to the **set +
count** of locked IDs and `score` fails closed if the scored set isn't a superset-consistent
continuation; require VOID events to cite an evidence artifact and report a separate void-rate.
*Test:* a chain missing a previously-anchored ID → `score` exits non-zero.

**P1-7 · Canonical-hash rule never frozen; reward-hack gate is same-commit only.** TOOLING/
DATA_MODEL say "publish canonicalization rules before any hash is relied upon," but **WP1.1
ships no golden canonicalization vector** while WP1.4+ depend on those hashes — a bootstrap/
reproducibility gap (also violates your own repro discipline). Separately, **WP2.2's
"can't benefit a claim in the same commit" gate is same-commit only** → split the oracle-data
change and the benefiting claim across two commits to evade. *Fix:* add a golden-vector
acceptance to WP1.1; make WP2.2 diff across a range, not one commit. *Test:* WP1.1 ships a
frozen `{yaml → normalized-json → sha256}` fixture; WP2.2 flags a two-commit split.

**P1-8 · Baseline fossilization: durable facts are invalidated only by the calendar, not by
contradicting events.** A durable fact goes `REVIEW_DUE` at `review_by` but is never
invalidated by a *contradicting event*; supersession **does not propagate to dependents** (live
analyses keep citing a superseded fact); and `REVIEW_DUE` durable facts are **silently dropped**
from queries/packs — an invisible gap Tier-0 then fills from memory. A3 also showed a *true,
durable design fact* ("the bridge carries road+rail") being selected as the answer to a
*volatile operability* question and never going stale. *Fix:* a "selection-scope" guard (a
durable capacity/design claim answering an operability query must be paired with the live-state
claim or marked "DESIGN FACT, NOT CURRENT STATE"); propagate supersession to dependents.
*Test:* A3's durable claim alone in a pack answering an operability query → validation fails.

**P1-9 · Maps: post-render inspection verifies render *fidelity*, not spatial *correctness*
(B7 fails). *(Deferred phase 5.)*** lng/lat swap and datum/CRS mislabels are baked in at
transcription and pass because the sidecar and render share one source; CRS is never validated
against coordinate magnitudes (a 3857/4326 metre/degree mislabel renders silently); geometry is
bound to evidence **only through a prose quote, never coordinates**, so wrong geometry passes
with a real-quote support assessment; crop and annotations have no spec fields to diff against.
*Fix:* validate CRS vs coordinate magnitude; bind geometry to a coordinate-anchored locator;
add declared crop/annotation spec fields. *Test:* A6's CONTROL_AREA-typed route centerline with
a quote-only locator → fails.

**P1-10 · `information_credibility` (1–6) is recorded and mandatory at Tier 2 but consumed by
no gate.** A credibility-6 counts identically to a credibility-1 toward CORROBORATED — the
second half of core bet B2 buys nothing enforceable. *Fix:* either gate on it (e.g. a credible-
floor for CORROBORATED) or demote it to optional metadata and stop charging Tier-2 ceremony for
it. *Test:* two credibility-6 assessments cannot reach CORROBORATED.

**P1-11 · Scope: WP7.2 reintroduces an explicit non-goal; Phases 5–6 are scheduled ahead of any
demand signal.** WP7.2 (model-assisted entailment) is the "large-model entailment as
gatekeeper" the plan lists as a non-goal — it should be **cut to the backlog**, not held as a
numbered WP. Phases 5 (visuals) and 6 (calibration) are 10 mandatory WPs ahead of any usage
evidence, for a tool whose proven daily value is Tier 0 + a small fact repo. *Fix:* make
Phases 5–7 explicitly **conditional on a demonstrated demand trigger** (see §8 / S5).

### Real, but already disclosed in §15 (acknowledge — not new breaks)

These surfaced strongly in the finder pool but the design **already concedes** them; the
*actionable* residue is noted:

- **Under-recording / set-equality on the author-populated manifest** (§9, §15.4). A load-bearing
  claim simply omitted from the manifest yields a passing committed answer (A7). *Actionable
  residue:* the only mitigation (WP7.1 unmarked-assertion warning) is **advisory and ships four
  phases after `answer` mode** — make it a **blocking** input to `answer` mode (per-sentence:
  marker, or an explicit `non_load_bearing` tag the refuter must contest).
- **Independence is self-declared** the gate cannot falsify (§15.5; WP2.3 explicitly checks
  *declared* consistency, not provenance). Relocates the laundering decision; A1 exploited it.
- **Semantic-review `CHECKED` is unfalsifiable for a solo author-reviewer** (§15.3; A2). No
  author/reviewer separation at Tier 1. *Actionable residue:* force a fresh-context/different-
  model pass for contested-by-default topics even at Tier 1.
- **`DIFFERENT_MODEL` refuter on the same curated pack shares blind spots** (§15.3).
- **Baseline can fossilize** (§15.6); **forecast skill needs hundreds of independent
  resolutions** (§15.7) — the power analysis (S1) puts a 0.02 Brier-skill edge at **~470
  effectively-independent / ~1,400 logged resolutions (multi-year solo)**, and a 0.01 edge
  effectively out of reach. The §11/WP6.4 "report descriptively, withhold 'skill' until a
  predeclared power plan's N" stance is **correct**.

### Downgraded by triage (transparency — finders over-rated these)

- **`relationship_input_hash` omits `claim_id`/`artifact_id`** (finder: P0 → **my P2**). The
  `semantic_review.claim_content_hash` + `artifact_hash` bind the *content* of the link targets,
  so repointing to a *different* claim/artifact breaks those bound hashes; the exploit only works
  for content-identical duplicates. Worth fixing (add the IDs to the hash, belt-and-suspenders)
  but not a P0.
- **Durable-fact-answers-volatile-question** (finder: P0 → **my P1**, folded into P1-8): requires
  user misuse and is partially mitigated by the durable/live compartments + `dispute_status`.
- **Set-equality on author manifest** (finder: P0 → **my P1 / disclosed**): it's the explicitly
  accepted §15.4 limitation, not a hidden break.

---

## 5. A1–A9 exploit artifacts (all nine slipped through)

Every mandatory exercise produced a concrete passing-but-bad artifact (full YAML in the run
output). Summary — *what slips through* and *the minimum control that would catch it*:

| # | Exploit | Verdict | Minimum control needed |
|---|---|---|---|
| A1 | First-party belligerent claim + 1 wire echo, two **declared** independence groups → CORROBORATED | PASSES_BUT_BAD | Closed `primary_evidence_kind`; first-party record can't also satisfy the independent-group leg |
| A2 | Displaced/over-broad claim, real locator, consistent hashes, self-`CHECKED` | PASSES_BUT_BAD | Reviewer≠author for contested topics; gate-computed `high_impact` |
| A3 | True durable design fact answers a volatile operability question, never goes stale | PASSES_BUT_BAD | Selection-scope guard pairing durable design facts with live-state |
| A4 | Hash-correct context pack records a **false `STALE`** omission reason, drops a current contrary claim | PASSES_BUT_BAD | Recompute every `omitted_candidate.reason`; topic-completeness check |
| A5 | Observation carries an absolute number recast as a share, wrong denominator | PASSES_BUT_BAD | `source_value`+`source_unit`; denominator resolves to a record |
| A6 | Route centerline typed `CONTROL_AREA`; geometry bound only by a prose quote | PASSES_BUT_BAD | Coordinate-anchored locator; reject quote-only geography support |
| A7 | Load-bearing claim left as unmarked prose → complete set-equality review of an under-filled manifest | PASSES_BUT_BAD | Blocking unmarked-assertion gate for `answer` mode |
| A8 | Fresh `(repo, anchor)` pair that never locked the losers defeats all 5 anti-tamper tests | PASSES_BUT_BAD | Anchor commits to the set+count of locked IDs; external notary |
| A9 | First-month shortcut: keep load-bearing claims at Tier 0; the named backstop is unimplementable | PASSES_BUT_BAD | Implement the recurrence ledger/report (queued change #1) |

The recurring root causes across A1–A9: **self-declared free-text fields the gate cannot
falsify** (independence, origin, `transformation`, `unit`, `void_policy`), **self-assignment of
the flags that trigger the strongest controls** (`high_impact`), and **the author == reviewer**
collapse for a solo user.

## 6. Stretch work (assumptions: all exploratory — no code/ledger exists)

- **S1 — Forecast power [Speculative]:** to detect a Brier-skill edge at 80% power, clustered:
  **0.03 edge ≈ 210 indep / ~630 logged; 0.02 ≈ 470 / ~1,400; 0.01 ≈ 1,900 / ~5,700.** Solo at
  5 binary predictions/week ⇒ **~4 years** for a 0.02 edge. Confirms §15.7; validates the
  "descriptive-until-power-plan-N" stance.
- **S2 — Maintenance economics [Speculative]:** sustainable solo ceiling is **low hundreds of
  claims**, set almost entirely by *live*-claim upkeep (~80–97% of burden). N=50 fine; N=200
  strained-to-abandon for any live-meaningful mix; N=1000 infeasible (50–300+ hr/mo).
  Abandonment shows up as **live records silently going STALE while the repo still looks green**.
- **S3 — Semantic ceiling [Speculative]:** structural/hashing controls *outright* catch only
  ~15–25% of serious errors (conditional on Tier 2) — their real value is making ~60–70%
  *reviewable*. Independent semantic review is the only layer that catches substance, and only
  when genuinely independent. Across *all* use (Tier 0 default), outright structural catch
  ~5–10%. **The §-promise is calibrated correctly to this ceiling; the design does not oversell.**
- **S4 — Visual ceiling [Probable]:** Record/Transformation/Rendering layers = STRONG (when
  built); **Framing = PARTIAL, Interpretation = WEAKEST** — both delegated to the Tier-2 refuter
  and to prose discipline, neither present at Tier 0/1 where most visuals will live.
- **S5 — Smallest safer architecture [Probable]:** ship **(i)** Tier 0 (CONVERSATION.md, day-zero,
  no code); **(ii)** a tiny reviewed baseline — the 6 evidence-chain schemas + records-mode gates
  + `fact.py query/candidate/assess/promote` + the WP4.5 durable spine (the actual high-ROI core
  that prevents inherited-memory error); **(iii)** the committed-answer loop (manifest + markers +
  set-equality refuter, Phase 3); **plus** the ~50-line recurrence backstop. **Drop/defer:**
  Phase 6 entirely (keep a 5-field prediction log, no calibration math), most of Phase 5 (one
  Matplotlib chart + Mermaid schematics; no CRS stack until a map is needed), Phase 7, and **WP1.7
  migration** (no v1 data exists for a fresh user). ≈ 20 of 41 WPs deliver 3 of the 4 stated jobs.

## 7. Coverage matrix (dimensions × artifacts)

| Dim | CONST | DATA_MODEL | IMPL_PLAN | EXAMPLE | KNOWL | CONVO | factbase | skills |
|---|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| 1 Coverage | Y | Y | Y | . | . | Y | . | . |
| 2 Data model | Y | Y | Y | Y | . | . | Y | . |
| 3 Epistemics | Y | Y | . | Y | Y | . | Y | . |
| 4 Baseline | Y | . | Y | . | Y | . | Y | Y |
| 5 Observations | Y | Y | Y | Y | . | . | . | Y |
| 6 Visuals | Y | Y | Y | Y | . | . | . | Y |
| 7 Refuter | Y | Y | Y | . | . | Y | . | . |
| 8 Forecast | Y | Y | Y | . | . | . | Y | . |
| 9 Security | Y | Y | Y | . | . | . | Y | . |
| 10 Migration | Y | Y | Y | . | . | . | . | . |
| 11 Scope | Y | . | Y | . | Y | Y | . | Y |
| 12 Incentives | Y | . | Y | . | Y | Y | . | . |
| T F1–F6 seams | Y | Y | Y | Y | . | Y | . | . |

## 8. Product / scope verdict (keep · cut · reorder)

- **KEEP:** the tier dial as anti-abandonment default; assessment-as-record chain; multi-axis
  status with event-vs-state; non-citable groups + ISW-as-research; fail-closed + set-equality
  refuter. These are the design's real strengths.
- **CUT to backlog:** WP7.2 (LLM entailment — a stated non-goal).
- **REORDER / make conditional:** treat **Milestone B (Phase 4) as the probable terminal state**;
  gate Phases 5–7 behind a *demonstrated demand trigger* recorded in PROGRESS, not as 10 mandatory
  WPs. Consider the S5 MVP cut (Phases 0–4 + Phase-3 refuter + recurrence backstop + one tiny
  visual; drop WP1.7) as the real v1.
- **ADD (small):** the recurrence/escalation backstop — the only friction against Tier-0 decay,
  currently vaporware.

---

## Appendix A — Proposed `REVIEW_ADJUDICATION.md` rows (NOT applied — you disposition these)

> These are *suggestions* for your post-review adjudication pass. I did not edit the ledger.
> Set dispositions yourself; `RESOLVED_IN_DESIGN` requires the change to actually be in the docs.

| ID | Sev | Suggested disposition | Governing change | WP / proof |
|---|---|---|---|---|
| V-P0-1 | P0 | PLANNED_FIX | gate-compute `high_impact`; refuter contests it (§10, DATA_MODEL §5/§10) | WP2.2/WP3.3: contested-topic claim w/ `high_impact:false` → fails |
| V-P1-1 | P1 | PLANNED_FIX | Tier-1 worked path + recurrence backstop (CONVERSATION, IMPL_PLAN) | new WP: Tier-1 `SUPPORTED` fixture w/o credibility/hashing passes |
| V-P1-2 | P1 | BLOCKING (pre-WP0.0) | fix N10 enum; log F1–F6; REVIEW_PROMPT→v3 + attach tier docs | WP0.0: out-of-enum disposition → exit 2 |
| V-P1-3 | P1 | PLANNED_FIX | define private overlay; scan `geodata/`+named-person; redaction gate before push | WP0.2: committed geojson / overlay field → flagged |
| V-P1-4 | P1 | PLANNED_FIX | define `primary_evidence_kind`; first-party ≠ independent leg (§6.1, WP2.5) | A1 YAML → CORROBORATED fails |
| V-P1-5 | P1 | PLANNED_FIX | unit vocabulary + `source_value`/`transformation` grammar (§6.3, WP2.8) | A5 observation → fails |
| V-P1-6 | P1 | PLANNED_FIX | anchor commits set+count; VOID cites artifact (§11, WP6.1–6.3) | A8 sequence → `score` non-zero |
| V-P1-7 | P1 | PLANNED_FIX | golden canonicalization vector in WP1.1; WP2.2 cross-commit | WP1.1 fixture; two-commit split flagged |
| V-P1-8 | P1 | PLANNED_FIX | selection-scope guard; supersession propagation (§8, WP4.1/4.3) | A3 pack → fails |
| V-P1-9 | P1 | PLANNED_FIX (Phase 5) | CRS-vs-magnitude; coordinate-anchored geometry locator | A6 spec → fails |
| V-P1-10 | P1 | ACCEPTED_WITH_LIMITS or gate it | credibility floor for CORROBORATED, or demote to metadata | two cred-6 → not CORROBORATED |
| V-P1-11 | P1 | PLANNED_FIX | cut WP7.2 to backlog; Phases 5–7 demand-gated | PROGRESS records demand trigger |
| (disclosed) | — | ACCEPTED_WITH_LIMITS | under-recording, self-declared independence, solo CHECKED, fossilization, forecast-N | already in §15; tighten WP7.1→blocking for `answer` |

## Appendix B — Queued post-review design changes (carried from chat; NOT applied)

These were proposed *after* this review began. They are **not** part of reviewed v3 and are not
written into the repo. Fold them in during your revision pass (still pre-code, pre-READY).

1. **Conversation-log compartment (proposed WP4.7).** Append-only `conversation_log.jsonl`
   (`clg-` ids, `provenance: conversation`), quarantined from the evidence chain — may
   inform/remind, never satisfy evidence/support; exits only via promotion. **Structural change →
   needs its OWN cold review before reliance.** This *also* supplies the recurrence-countability
   that P1-1 / A9 need. *Flagged risks:* (a) the log file is the **highest-leakage artifact in
   the repo** (raw thinking, source/method notes, named-person speculation) — it must be in the
   WP0.2 scan and probably `private/` by default; (b) keep its coarse confidence words **out of
   the §11 forecast scoring**; (c) "preserve hedges in summaries" is a discipline, not a checkable
   invariant — list under §15.
2. **Reuse Centaur cartography for WP5.3 (build guidance — does NOT need its own cold review).**
   Vendor (copy, don't couple) matplotlib/pyproj/Natural-Earth + ISW map design from the Centaur
   repo (`~/Documents/Centaur`), but **rewire inputs to sourced `geography` records + hash-bound
   visual specs** (Centaur is positions-driven; this harness is provenance-driven), and **skip**
   Centaur's headless-Chrome/Poppler publication-PDF pipeline. Pin the Natural Earth snapshot +
   record the borrowed Centaur source commit. (Note P1-9: WP5.3 acceptance must pin computed-
   geometry provenance, not just plotted points.)

## Appendix C — Self-certification & limitations

- Every P0/P1 above carries a location, a concrete failure scenario, a specific recommended
  change, and an exact proving test (per the finding format). Operational cost for the structural
  fixes is low (schema/enum/scan-scope edits made once); the Tier-1-path and recurrence-backstop
  fixes (P1-1) are the only ones with ongoing UX weight, and they *reduce* net burden by making
  recording cheap.
- **This review is not independent** (caveat 1) and **its verification phase was reconstructed by
  the reviewing model, not by independent skeptic panels** (caveat 2). Surviving findings are
  strong leads, not certified verdicts. **A genuinely independent (GPT-5.5-Pro / third-model /
  human) pass remains required before `governance_status: READY`.**
- The score (74) is one model's calibrated judgment; treat it as directional.

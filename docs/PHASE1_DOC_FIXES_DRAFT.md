# PHASE-1 GATE — draft doc-fixes + focused review prompt (PROPOSAL, NOT applied)

**Status: PROPOSAL.** Nothing here is applied to the governing docs. This file exists so the
Phase-1 gate is actionable: (1) run the independent review with the focused prompt below; (2)
reconcile these four draft fixes with what it finds; (3) apply the reconciled fixes to the real
governing docs, keeping each fix's **anchor token** (so `scripts/preflight_phase1.py` can detect
it); (4) set `independent_review_complete: true` in `docs/REVIEW_ADJUDICATION.md` once the
independent review is logged. The pre-flight check then clears Segment 2 (Phases 1–3).

These fixes must land **before WP1.x** because the Phase-1/2 schemas and gates implement them.
The anchor token is an **attestation anchor** — it certifies *you applied the corresponding
fix*; it is not a proof of semantic correctness (that is what the independent review is for).

---

## Focused gate-review prompt (run in GPT-5.5-Pro / Gemini / a human — NOT Claude)

> You are an independent cross-vendor reviewer. Attached: the Analyst Harness v3 design package
> (per `docs/REVIEW_PROMPT.md`'s attach list) **plus** the existing non-independent Claude
> review `docs/REVIEW_V3_COLD_claude-opus-4-8.md`. Your job is narrow and adversarial:
> 1. **Attack the P0 + the top P1s** in the Claude review (V-P0-1 self-assigned `high_impact`;
>    V-P1-1 Tier-1-undelivered; V-P1-3 privacy; V-P1-4 corroboration escape hatch; V-P1-5
>    observation-schema over-claim; V-P1-7 canonicalization bootstrap). For each: is it real?
>    Over- or under-rated? Did the Claude pass miss a sharper or adjacent failure?
> 2. **Find what a Claude-family reviewer would structurally miss** — blind spots a same-family
>    pass shares by construction (§15.3).
> 3. **Sanity-check the four draft doc-fixes below** — do they actually close V-P0-1 / V-P1-4 /
>    V-P1-5 / F3, or do they relocate the problem? Propose better language where they fall short.
> Return: confirmed/adjusted severities for the P0+top-P1s, any NEW findings, and a verdict on
> each draft fix. Be concrete; produce passing-but-bad YAML where it sharpens a point.

---

## Fix 1 — V-P0-1: make `high_impact` gate-computed (Constitution §10 + DATA_MODEL §5/§10)

**Problem:** `high_impact` is an author-set boolean that gates the strongest control (the §10
`DIFFERENT_MODEL`/`HUMAN` reviewer + the refuter); it is never recomputed, and the refuter has
no field to contest a false setting (circular: the refuter only runs once a claim is escalated).

**Proposed Constitution §10 insert** (keep the anchor phrase `gate-computed high_impact`):
> `high_impact` is **gate-computed, not author-asserted** (a `gate-computed high_impact` rule).
> The gate sets `high_impact: true` if ANY hold — the author may not set it false to dodge
> review: (a) `topics ∩ {casualties, attribution, territorial-control}`; (b) the claim feeds an
> analysis manifest, a shared visual, or a prediction; (c) it contradicts a prior recorded
> claim. A stored `high_impact` is recomputed and a mismatch fails. The refuter artifact carries
> a `high_impact` field and **must contest** a `high_impact: false` on any claim meeting (a)–(c).

**Proposed DATA_MODEL §5 change:** annotate the `high_impact` field "computed by the support/
answer gate from topics + downstream use; recomputed on validation; stored mismatch fails."

**Proving test (Phase 2/3):** a contested-topic claim authored `high_impact: false` is raised by
the gate and `answer` mode fails without the §10 reviewer class. *(Discharges V-P0-1, F2.)*

## Fix 2 — V-P1-4: `primary_evidence_kind` enum (Constitution §6.1 + DATA_MODEL §4)

**Problem:** "authoritative primary evidence" is undefined and machine-uncheckable; with the
empty seed assessment log it is the only reachable `CORROBORATED` path, so a first-party
belligerent claim + one wire echo (two declared independence groups) bootstraps corroboration.

**Proposed change** (keep the anchor token `primary_evidence_kind`): add a closed field
`primary_evidence_kind ∈ {FIRST_PARTY_ACTION_RECORD, AUTHORITATIVE_DATASET,
DIRECT_SENSOR_CAPTURE, OFFICIAL_PRIMARY_DOCUMENT}` on the claim-evidence assessment. §6.1 rule:
a chain claimed authoritative-primary must declare a `primary_evidence_kind`; a
`FIRST_PARTY_ACTION_RECORD` by an interested belligerent (government/military jurisdiction on a
contested kinetic claim) may be a primary record of its own claim but **may not also satisfy the
independent-group requirement** for `CORROBORATED`.

**Proving test (WP2.5):** the A1 YAML (RU-MoD claim + one Reuters relay, two declared groups)
→ `CORROBORATED` fails. *(Discharges V-P1-4.)*

## Fix 3 — V-P1-5: unit vocabulary + transformation grammar (Constitution §6.3 + DATA_MODEL §6)

**Problem:** WP2.8 promises to catch "tonnes/day used as tonnes/year" and wrong-denominator, but
`unit` is free text, `transformation` has no grammar, and value is bound to the locator's
identity not the source number — so an invented/wrong-scope number passes all structural gates.

**Proposed change** (keep the anchor token `unit_vocabulary`): observations declare `unit` from a
closed `unit_vocabulary` (each entry carries a dimensional class for a dimensional check);
`value_type: NUMBER` requires `source_value` + `source_unit` (the literal quantity at the
locator); any reported value in a different unit/denominator must be a declared `transformation`
from `source_value`, with `derived_from` resolving the denominator to a record. A bare
absolute-number-recast-as-share with `derived_from: []` and `transformation: null` fails.

**Proving test (WP2.8):** A5's bpd-as-share observation fails; a tonnes/day value labelled
tonnes/year fails the dimensional check. *(Discharges V-P1-5.)*

## Fix 4 — F3: Tier-1 caps at `SUPPORTED` (Constitution §6.1 / §6.6)

**Problem:** §6.6 makes information credibility + full CHECKED hashing optional at Tier 1; an
implementer could relax §6.1 at Tier 1 and silently weaken `CORROBORATED`.

**Proposed §6.6 insert** (keep the anchor phrase `caps support at SUPPORTED`):
> Tier 1 without information-credibility scoring and full `CHECKED` three-hash binding **caps
> support at `SUPPORTED`** (a Tier-1 `caps support at SUPPORTED` rule). `CORROBORATED` ALWAYS
> requires the full §6.1 conditions regardless of tier; §6.6 lowers the cost of *recording*,
> never the bar for *corroboration*.

**Proving test (WP2.5):** a Tier-1 assessment lacking credibility/CHECKED requesting
`CORROBORATED` fails; at `SUPPORTED` it passes. *(Discharges F3.)*

## Fix 5 — V-P1-10: gate `information_credibility` (Constitution §6.1)

**Problem:** `information_credibility` (1–6) is mandatory ceremony at Tier 2 but no gate consumes
it — a credibility-6 counts identically to a credibility-1 toward `CORROBORATED`.

**Proposed change** (keep the anchor phrase `credibility floor`): §6.1 — `CORROBORATED` requires
that at least one corroborating chain meet a **`credibility floor`** (e.g. `information_credibility
≤ 3` on the assessment), so a pair of low-credibility (5–6) assessments cannot reach
`CORROBORATED`. *(If you instead choose to demote `information_credibility` to optional metadata,
say so explicitly and update the pre-flight token accordingly.)*

**Proving test (WP2.5):** two `information_credibility: 6` assessments cannot reach
`CORROBORATED`. *(Discharges V-P1-10 — the finding the adjudication's binding condition names.)*

---

## How the pre-flight check reads this

`scripts/preflight_phase1.py` clears Segment 2 (exit 0) only when, in the **governing docs**
(`docs/CONSTITUTION.md` + `docs/DATA_MODEL.md`), all five anchor tokens are present —
`gate-computed high_impact` (V-P0-1), `primary_evidence_kind` (V-P1-4), `unit_vocabulary`
(V-P1-5), `credibility floor` (V-P1-10), and `caps support at SUPPORTED` (F3) — **and**
`docs/REVIEW_ADJUDICATION.md` frontmatter has `independent_review_complete: true`. (The four the
adjudication's binding condition names are V-P0-1/V-P1-4/V-P1-5/V-P1-10; F3 is enforced too as
the adjacent §6.6 corroboration-bar fix.) Until then it fails closed (exit 2) and lists what is
missing. Applying the reconciled fixes above (keeping the anchor tokens) + logging the
independent review satisfies it.

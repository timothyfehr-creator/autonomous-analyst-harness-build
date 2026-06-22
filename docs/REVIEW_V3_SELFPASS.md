# REVIEW — v3 self-pass (NON-INDEPENDENT)

**Status: same-author dry pass. Does NOT satisfy Constitution §10 reviewer-independence.**
It shares this author's blind spots by construction (§15.3). It is a head start for the
cold `DIFFERENT_MODEL`/`HUMAN` review that must precede WP0.0; it does not unblock
governance. Findings below are weighted toward the **new tier seams**, since the inherited
GPT core was reviewed in its own pass and Claude's prior design was reviewed by GPT.

## F1 — Tier 0 has no forced-escalation trigger; the whole chain is bypassable by default [P1]

- **Evidence:** Constitution §1 makes Tier 0 the default with "no records, no manifest, no
  refuter," and escalation to Tier 1/2 is self-judged ("when you want to keep / chart /
  depend on it"). §15.8 concedes "Tier-0 honesty is a discipline, not a checked invariant."
- **Failure scenario:** A load-bearing factual claim that *should* be corroborated and
  evidenced is stated at Tier 0 with a "fact" label and a confidence word, and never enters
  the chain — not by malice, but because no one *decided* it crossed the escalation line.
  Over weeks, the path of least resistance keeps everything at Tier 0; the heavy apparatus
  becomes decorative; the tool's assurance quietly degrades to "honestly-labeled vibes."
  This is the under-recording hole (GPT's N1 against Claude's v1) re-introduced *as the
  default operating mode*.
- **Is the §15.8 disclosure adequate, or a fatal flaw in costume?** It is the design's
  largest risk and cannot be fully closed without killing the lightweight default (the goal).
  But "discipline, not gate" is too soft as written — the trigger is pure self-judgment with
  no friction against rationalizing downward.
- **Recommended change:** Keep Tier 0 ungated, but (a) define **objective** escalation
  triggers in `docs/CONVERSATION.md` that are hard to rationalize past — e.g. *any claim
  that enters a written deliverable, any number you would act or spend on, any claim a
  future-you would cite* must escalate; and (b) add a periodic **recurrence sweep**: a
  Tier-0 claim that has now been asserted N times across answers is flagged as a promotion
  candidate. The discipline stays, but with friction and a backstop.
- **Verification:** `docs/CONVERSATION.md` lists objective triggers (not just "if you feel
  it matters"); a lightweight `fact.py recurrence` (later WP) reports repeated unrecorded
  assertions.

## F2 — The escalation flags ("load-bearing", "high_impact") are undefined and self-assigned [P1]

- **Evidence:** "load-bearing" gates Tier 2 / the refuter (Constitution §1, §10) and is
  never defined. `high_impact` (EXAMPLE_WORKFLOW claim fields) gates the
  DIFFERENT_MODEL/HUMAN review requirement (§10) and is a self-set boolean with no
  definition.
- **Failure scenario:** Whoever sets the flag sets it to the convenient value. A claim that
  warrants independent review is marked `high_impact: false`; a claim that warrants the full
  chain is judged "not load-bearing." The strongest controls in the design (independent
  review, refuter) are switched off by an undefined, self-assigned field — the soft
  underbelly of the whole tier ladder.
- **Recommended change:** Define both operationally in the constitution/knowledge policy
  (e.g. high_impact ⊇ {informs a real decision, contradicts a prior published claim, feeds a
  forecast or a visual you'll share, concerns casualties/attribution/control}). Make the
  refuter spec require the reviewer to *contest* a `false` setting, not just accept it.
- **Verification:** a fixture where a decision-informing claim marked `high_impact: false`
  is flagged by the refuter rubric.

## F3 — §6.6 right-sizing vs §6.1 corroboration: unstated interaction [P2]

- **Evidence:** §6.6 makes information credibility and full semantic-review hashing optional
  at Tier 1. §6.1 grants `CORROBORATED` only with "≥1 chain ... a source assessed A–C in
  scope" and `CHECKED` review with bound hashes.
- **Failure scenario:** A reader assumes Tier 1 can reach `CORROBORATED` cheaply, then is
  surprised when the gate refuses (no A–C assessment, no CHECKED hashes). Or worse, the
  implementation "helpfully" relaxes §6.1 at Tier 1 to match §6.6 and silently weakens the
  corroboration rule.
- **Recommended change:** State explicitly: **Tier 1 without credibility scoring / CHECKED
  hashing caps support at `SUPPORTED`; `CORROBORATED` always requires the full §6.1
  conditions regardless of tier.** §6.6 lowers the cost of *recording*, never the bar for
  *corroboration*.
- **Verification:** a Tier-1 fixture lacking credibility/CHECKED that requests
  `CORROBORATED` → fail; the same at `SUPPORTED` → pass.

## F4 — The `conversational` verifier mode always exits 0, which brushes against §13 [P2]

- **Evidence:** Plan WP0.1 adds a `conversational` mode that "reports Tier 0 needs no
  verification (exit 0 with a notice)." §13 condemns "a gate that scans nothing and reports
  success."
- **Failure scenario:** A user (or agent) runs `verify.py --mode conversational`, sees exit
  0, and records "verification passed" — when nothing was checked. The mode's intent
  (discoverability) is sound; the exit-0 framing can be misread as a pass.
- **Recommended change:** Make the non-gate status unmistakable — emit a distinct,
  loud, non-"PASS" notice ("Tier 0 is unverified by design; see CONVERSATION.md") and
  consider a reserved informational exit code or a banner that cannot be mistaken for a gate
  result. Document that `conversational` is a signpost, not a check.
- **Verification:** the mode's output contains the explicit "unverified by design" notice
  and never the word PASS.

## F5 — Scale and unproven ROI for a solo user (carried, still standing) [P2]

- **Evidence:** 41 work packages, 6 record types, hash chains, calibration ledger. Milestone
  ordering helps but Milestones C–D (visuals, calibration) sit behind the full chain, and
  §11 concedes forecast skill needs hundreds of resolutions.
- **Failure scenario:** The solo user reaches Milestone A/B, finds Tiers 1–2 too costly to
  use routinely, and the calibration ledger never accrues enough resolved predictions to
  mean anything — leaving large parts of the build inert. The dominant real-world failure
  is **abandonment**, not inaccuracy.
- **Recommended change:** Treat Milestone B as the *probable* terminal state in planning;
  make Phases 5–7 explicitly conditional on demonstrated use; consider a "minimum viable
  harness" cut (Tier 0 + a tiny reviewed baseline + the answer loop) as the real v1 target,
  with everything else opt-in.
- **Verification:** PROGRESS records a usage check after Milestone B before committing to
  Phases 5–7.

## F6 — Semantic-review `CHECKED` proves what was reviewed, not that the review was sound [P2]

- **Evidence:** §6.1/§6.2 hinge on a `CHECKED` assessment with bound hashes; §15.3/.4 note
  the limits. For a solo user reviewing their own work, the reviewer and the author are the
  same person.
- **Failure scenario:** The hashes faithfully record that *something* was reviewed; a hasty
  or motivated self-review marks `CHECKED` on an assessment whose locator only loosely
  supports the claim. The chain looks rigorous (hashes everywhere) but the one human
  judgment it rests on was rubber-stamped — theater-with-hashes.
- **Recommended change:** For baseline/high-impact, §10 already requires non-same-model
  review — keep that firm. For routine Tier 1, accept the limit explicitly and lean on F1's
  recurrence sweep + periodic different-model audits of a sample of CHECKED assessments.
- **Verification:** a sampling check that surfaces N random CHECKED assessments for
  re-review.

## Net

The merge is sound and the inherited core is strong. The **new** risk surface is the tier
model, and it concentrates in two places: the **self-judged escalation boundary** (F1, F2)
and a couple of unstated interactions (F3, F4). None is fatal; F1+F2 are the ones to harden
before relying on the tool, because they are where "rigorous personal use" silently decays
into "labeled chat." Hardening them sharpens the discipline without re-imposing the ceremony
the tier model exists to avoid. A cold `DIFFERENT_MODEL` pass should target the same seams —
especially whether F1's objective triggers actually bind, or just move the rationalization.

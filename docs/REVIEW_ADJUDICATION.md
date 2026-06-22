---
schema_version: "1.0"
external_review_complete: true
review_model: "claude-opus-4-8 — NON-INDEPENDENT (same model family as a v3 co-author); cross-vendor/human pass DEFERRED to before Phase 1 per governance note below"
reviewed_at: "2026-06-22"
open_p0_p1: 0
governance_status: READY
---

# REVIEW ADJUDICATION

This is the machine-checkable disposition ledger for adversarial review findings. The
header remains blocked until a cold review of the v3 merge is complete. `open_p0_p1: 0` currently
means no *new* findings are logged yet; it does not override
`external_review_complete: false`.

Allowed dispositions:

- `RESOLVED_IN_DESIGN`
- `PLANNED_FIX`
- `ACCEPTED_WITH_LIMITS`
- `BLOCKING`
- `REJECTED_WITH_EVIDENCE`

Every P0/P1 requires a governing-file change, implementation WP, and exact proving test.

## Incorporated findings from the prior review

| ID | Severity | Disposition | Governing change | Implementation proof |
|---|---:|---|---|---|
| N1 | P0 | RESOLVED_IN_DESIGN | Constitution §§1–2, 5.1–5.2; exact artifact + claim-specific assessment replaces direct source citation | WP1.4, WP2.3, WP2.5: single hostile official + URL cannot produce `CORROBORATED` |
| N2 | P1 | RESOLVED_IN_DESIGN | Constitution §3; type-specific records eliminate universal source contradiction | WP1.3, WP2.4: valid fact/inference/assumption/projection fixture passes; invalid variants fail |
| N3 | P1 | RESOLVED_IN_DESIGN | Constitution §§7–8; manifest set equality and output-hash binding | WP1.6, WP3.2–3.4: missing claim, changed output, or incomplete review set blocks `answer` |
| N4 | P1 | RESOLVED_IN_DESIGN | Constitution §5.6; claim markers preserve visible status | WP3.2, WP3.4: unmarked `UNVERIFIED`, `THIN`, `CONTESTED`, assumption, inference, or projection fails |
| N5 | P1 | RESOLVED_IN_DESIGN | Constitution §§2.4, 5.5, 6; claim-specific temporal scope | WP1.4, WP2.7: recent review of old evidence cannot refresh validity |
| N6 | P1 | RESOLVED_IN_DESIGN | Constitution §9; all ex-ante fields frozen in hash chain + external anchor | WP1.5, WP6.1: criterion/question edit or Git rewrite fails against anchor |
| N7 | P1 | RESOLVED_IN_DESIGN | Constitution §§3, 9; projection linkage, coverage, benchmark, resolution reporting | WP2.4, WP6.2–6.4: unlinked projection fails; overdue/void/coverage remain visible |
| N8 | P1 | RESOLVED_IN_DESIGN | Constitution §§2.4–2.5, 5.4; stance, origin chain, independence group | WP1.4, WP2.3, WP2.6: same-origin copies cannot satisfy contest; mixed credible stances marked uncontested fail |
| N9 | P1 | RESOLVED_IN_DESIGN | Constitution §12; closed root-versioned schemas and migration contract | WP1.1, WP1.7: unknown fields fail; golden migration, dry-run, backup, rollback pass |
| N10 | P1 | ACCEPTED_WITH_LIMITS | README data handling; neutral identity registry; sensitive locator scanner *(disposition corrected 2026-06-22 from the non-enum value `MITIGATED_IN_DESIGN`, per finding V-P1-2)* | WP0.2, WP1.2–1.4: signed/private locators and prohibited private fields fail |
| N11 | P2 | RESOLVED_IN_DESIGN | Canonical commands use `.venv/bin/python`; activation follows dependencies | WP0.1: documented commands run without a `python` alias |
| N12 | P1 | RESOLVED_IN_DESIGN | Constitution §12 and Data Model envelope: root-only version | WP1.1–1.2, WP1.7: root version passes; per-record version fails |
| N13 | P1 | RESOLVED_IN_DESIGN | `sources.yaml` separates exact entities from non-citable groups; ISW is research | WP1.2, WP2.1: group references fail; exact entities resolve |
| N14 | P1 | RESOLVED_IN_DESIGN | Constitution §11 and AGENTS: gate-driving data is oracle data; assessments append-only | WP2.2: assessment change plus benefiting claim in one unadjudicated change fails |
| N15 | P1 | RESOLVED_IN_DESIGN | This ledger; Constitution §12; WP0.0 blocks on open findings | WP0.0: missing/open finding exits `2` and blocks scaffold |
| N16 | P1 | RESOLVED_IN_DESIGN | Constitution §§1, 5.3, 10; typed observations prevent value extraction from prose | WP1.6, WP2.8, WP5.1–5.5: wrong value/unit/denominator/scope binding fails; render data must match sidecar |

## Accepted limitations

1. Structural gates do not prove semantic truth. Exact locators and explicit semantic
   review make the judgment inspectable.
2. Same-model fresh-context review is useful but not independent and cannot qualify
   baseline/high-impact review.
3. Claim markers and extraction warnings cannot guarantee completeness.
4. Forecast calibration will be noisy for a long time; skill claims require a predeclared
   power threshold and effectively independent resolutions.
5. Reliability, information credibility, independence, and visual framing remain
   contextual judgments.
6. A baseline repository can fossilize error; strict promotion, review dates, and
   supersession reduce rather than eliminate that risk.
7. A visual can still mislead through selection and framing; the spec makes choices
   auditable but not automatically neutral.

## External-review update procedure

1. Run `docs/REVIEW_PROMPT.md` in a fresh model without prior findings.
2. Add each new P0/P1 below with disposition, governing change, WP, and exact test.
3. Set `open_p0_p1` to the unresolved count.
4. Set `external_review_complete: true` only after reading the complete cold output.
5. Set `governance_status: READY` only when `open_p0_p1: 0` and no blocker remains.
6. Mirror the result in `docs/PROGRESS.md`.

## New external findings — v3 cold review (2026-06-22)

### Governance note (READ — defines the limits of this READY state)

The v3 cold review was performed by **Claude Opus 4.8** and is recorded in
`docs/REVIEW_V3_COLD_claude-opus-4-8.md` (score 74/100; 1 P0 + ~11 P1; all nine A1–A9 exploits
slipped past the planned gates). **This review is NOT independent** of the design (Claude
co-authored v3; per §10 / Accepted-limitation #2 it is a *same-family* pass), and its 3-skeptic
adversarial-verification phase was reconstructed by the reviewing model rather than run as
independent panels. Governance is set **READY under `ACCEPTED_WITH_LIMITS`** by the repo owner
(pragmatic path, 2026-06-22) so that **Phase 0 (governance + scaffold) may proceed** — the
lowest-risk place to run on a non-independent review.

**Binding condition on this READY state:** a genuinely independent **cross-vendor
(GPT-5.5-Pro / Gemini / human)** pass on the P0 + top P1s, and doc-incorporation of the
evidence-chain findings (V-P0-1, V-P1-4, V-P1-5, V-P1-10), **must complete before Phase 1
(WP1.x) begins**. Phase 1 is the evidence-chain rigor layer where a missed Claude blind spot
actually bites. `READY` here authorizes Phase 0 only.

**What `open_p0_p1: 0` means here:** every finding below is *adjudicated* (disposition +
governing change + WP + proving test). It does **not** mean the `PLANNED_FIX` changes are
implemented — those are tracked in their named WPs.

### v3 cold-review findings

| ID | Sev | Disposition | Governing change | WP / proving test |
|---|---:|---|---|---|
| V-P0-1 | P0 | PLANNED_FIX | Make `high_impact` gate-computed (topics∩{casualties,attribution,control} or feeds manifest/visual/prediction ⇒ true); refuter gains a `high_impact`/`load-bearing` field it must contest (Constitution §10, DATA_MODEL §5/§10) | WP2.2 / WP3.3: contested-topic claim with author `high_impact:false` is raised and `answer` fails without the §10 reviewer class |
| V-P1-1 | P1 | PLANNED_FIX | Specify a light Tier-1 worked path (credibility + CHECKED-hashing optional per §6.6); implement the recurrence backstop (`fact.py recurrence`) — see queued change #1 | new WP + CONVERSATION.md: a Tier-1 fixture reaches `SUPPORTED` without credibility/three-hash binding; recurrence report lists repeated unrecorded assertions |
| V-P1-2 | P1 | RESOLVED_IN_DESIGN | **Fixed in this commit:** N10 disposition corrected to a valid enum; F1–F6 logged here; `REVIEW_PROMPT.md`→v3 + Tier-0 docs attached | WP0.0: `check_review_adjudication.py` rejects an out-of-enum disposition; all P0/P1 carry disposition+WP+test |
| V-P1-3 | P1 | PLANNED_FIX | Define the private overlay (fields/paths confined to git-ignored `private/`); add `geodata/` + named-person assessments to the WP0.2 scan; add a redaction/secret gate before any push; soften the GitHub recommendation in START_HERE | WP0.2: a committed `geodata/*.geojson` and a private-overlay field in a tracked assessment are flagged |
| V-P1-4 | P1 | PLANNED_FIX | Define `primary_evidence_kind` (closed enum); a first-party belligerent action-record may NOT also satisfy the independent-group leg (Constitution §6.1) | WP2.5: A1 YAML (RU-MoD claim + 1 wire relay, two declared groups) → CORROBORATED fails |
| V-P1-5 | P1 | PLANNED_FIX | Closed `unit` vocabulary + dimensional check; require `source_value`/`source_unit`; `transformation` grammar with `derived_from` resolving denominators to records (Constitution §6.3) | WP2.8 / WP1.6: A5 bpd-as-share observation with `derived_from:[]` → fails; tonnes/day-as-/year → fails |
| V-P1-6 | P1 | PLANNED_FIX | Anchor head commits to the set+count of locked prediction IDs; `score` fails closed on a non-superset chain; VOID events must cite an evidence artifact; report void-rate (Constitution §11) | WP6.1–6.3 *(Phase 6)*: A8 fresh-chain-missing-an-ID → `score` exits non-zero |
| V-P1-7 | P1 | PLANNED_FIX | Ship a golden canonicalization vector in WP1.1 before any downstream hash is relied on; make WP2.2's reward-hack gate diff across a commit range, not one commit | WP1.1 / WP2.2: frozen `{yaml→normalized-json→sha256}` fixture; a two-commit split of oracle-data + benefiting claim is flagged |
| V-P1-8 | P1 | PLANNED_FIX | Selection-scope guard (a durable design/capacity claim answering an operability query must pair with the live-state claim or be marked "DESIGN FACT, NOT CURRENT STATE"); propagate supersession to dependents (Constitution §8) | WP4.1 / WP4.3: A3 durable claim standing alone as an operability answer → fails |
| V-P1-9 | P1 | PLANNED_FIX | Validate CRS against coordinate magnitude; bind geometry to a coordinate-anchored locator (reject quote-only); declared crop/annotation spec fields (Constitution §12) | WP5.1/5.3/5.5 *(Phase 5)*: A6 CONTROL_AREA-typed route centerline with a quote-only locator → fails |
| V-P1-10 | P1 | PLANNED_FIX | Either gate `information_credibility` (credible floor for CORROBORATED) or demote it to optional metadata (Constitution §6.1/§6.6) | WP2.5: two credibility-6 assessments cannot reach CORROBORATED |
| V-P1-11 | P1 | PLANNED_FIX | Cut WP7.2 (model entailment — a stated non-goal) to the candidate backlog; make Phases 5–7 conditional on a demonstrated demand trigger recorded in PROGRESS | IMPLEMENTATION_PLAN edit; PROGRESS records the trigger before Phase 5/6 WPs start |

### Self-pass F1–F6 — now formally logged (per V-P1-2)

| ID | Sev | Disposition | Incorporated as |
|---|---:|---|---|
| F1 | P1 | PLANNED_FIX | Tier-0 forced-escalation friction + recurrence backstop → **V-P1-1** |
| F2 | P1 | PLANNED_FIX | `high_impact`/`load-bearing` self-assignment + refuter must contest → **V-P0-1** |
| F3 | P2 | PLANNED_FIX | State explicitly in §6.1/§6.6 that Tier-1 without credibility/CHECKED caps at `SUPPORTED`; `CORROBORATED` always needs full §6.1 |
| F4 | P2 | PLANNED_FIX | WP0.1 `conversational` mode emits a loud "unverified by design" notice, never the word `PASS` |
| F5 | P2 | ACCEPTED_WITH_LIMITS | Treat Milestone B as the probable terminal state; Phases 5–7 demand-gated → **V-P1-11** |
| F6 | P2 | ACCEPTED_WITH_LIMITS | Solo author-reviewer `CHECKED` rubber-stamping → Accepted-limitations #2/#3 (sampling re-review of CHECKED assessments) |

### Real-but-disclosed (map to existing Accepted limitations — not new breaks)

Under-recording / set-equality on the author manifest (#3; *actionable residue:* make WP7.1's
unmarked-assertion warning **blocking** for `answer` mode); self-declared independence (#5);
solo `CHECKED` (#2); `DIFFERENT_MODEL`-on-same-pack blind spots (#2); fossilization (#6);
forecast needs hundreds of independent resolutions (#4 — the review's power analysis: ~470
effectively-independent / ~1,400 logged for a 0.02 Brier-skill edge ⇒ multi-year). The score's
honesty rests on these being disclosed, not hidden.

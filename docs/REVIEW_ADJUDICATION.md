---
schema_version: "1.0"
external_review_complete: false
review_model: null
reviewed_at: null
open_p0_p1: 0
governance_status: BLOCKED
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
| N10 | P1 | MITIGATED_IN_DESIGN | README data handling; neutral identity registry; sensitive locator scanner | WP0.2, WP1.2–1.4: signed/private locators and prohibited private fields fail |
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

## New external findings

_None yet. This is why the gate remains blocked._

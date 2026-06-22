# Revision notes — v1 governance to v2 build plan

## Core redesign

| v1 weakness | v2 decision |
|---|---|
| Claim cited a source identity | Claim support resolves through exact artifacts and append-only claim-evidence assessments |
| `OFFICIAL/MAINSTREAM/SOCIAL` doubled as reliability | Neutral source type + scoped source reliability + relationship-specific information credibility |
| One confidence enum carried support, conflict, and staleness | Separate support, dispute, freshness, lifecycle, stability, and epistemic type |
| `CONFIRMED` could rest on one official claim | `CORROBORATED` requires checked independent origin chains |
| URL proved provenance only | Artifact stores retrieval identity; assessment stores exact claim-specific support, stance, origin, credibility, time scope, hashes, and review |
| Assumptions were impossible under universal sourcing | Type-specific claim contracts |
| Refuter coverage was a boolean | Set equality against manifest + exact output hash |
| Output could outrun records | Lightweight claim markers + output validator |
| `as_of` could be refreshed by typing today | Freshness derives from assessment temporal scope and maintenance events |
| Forecast criterion could be rewritten | All ex-ante fields locked in hash chain + external anchor |
| Gate-driving source data could be edited for reward | Assessments append-only; benefiting same-change edits gated |
| No migration plan | Root envelope, closed schemas, explicit migration/rollback WP |
| Baseline facts were a backlog line | Knowledge policy, query/context/promotion/refresh tools, seed WP, and skill |
| Charts had no structured datum and would parse prose | Typed observations bind values, units, denominators, scope, and uncertainty to checked support |
| Visuals were absent | Visual specs, real geography, charts/maps/schematics, sidecars, post-render inspection, and skill |
| Forecasting preceded requested visual utility | Utility-first sequence: answer loop → baseline repository → visuals → slow-burn calibration |

## What remains intentionally unsolved

- Automated proof that evidence entails a claim.
- Guaranteed completeness of every assertion in prose.
- Fully independent model review.
- Fast statistical proof of forecasting skill.
- Neutrality of every visual framing choice.

The design records and checks these limits instead of letting them hide behind a green
structural run.

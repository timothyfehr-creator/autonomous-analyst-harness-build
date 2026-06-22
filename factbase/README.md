# Factbase

The factbase begins deliberately empty except for neutral source identity metadata. Real
claims are seeded only after the v2 schemas and gates exist.

## Files

| File | Purpose |
|---|---|
| `sources.yaml` | exact source entities plus non-citable groups; no reliability judgments |
| `source_assessments.yaml` | append-only scoped source reliability assessments |
| `evidence.yaml` | exact retrieved artifacts and hashes |
| `claim_evidence.yaml` | append-only claim-specific support/stance/origin/review records |
| `observations.yaml` | typed values for charts and calculations |
| `baseline/claims.yaml` | reviewed durable and append-only historical claims |
| `live/claims.yaml` | volatile claims with explicit expiry |
| `predictions.yaml` | ex-ante forecast records |
| `prediction_events.jsonl` | append-only lock/resolution/void/correction chain |
| `geography.yaml` | real geometry records with CRS and support |
| `baseline_events.jsonl` | append-only promotion/refresh/rejection/supersession chain |

## Rules

- Source IDs never satisfy a claim by themselves.
- Broad groups are non-citable.
- Reliability assessments and claim-evidence assessments are append-only.
- Artifacts are immutable by content hash.
- Baseline claims are promoted only after gates and qualifying review.
- Visuals use observations and geography IDs, never values or coordinates extracted from
  prose at render time.
- Empty seed files are intentional. Do not “helpfully” fill them from model memory.

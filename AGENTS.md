# AGENTS.md

Operating rules for any coding or research agent working in this repository. The goal is
sustained autonomous progress against a trustworthy oracle, not industrious-looking drift.

Read, in order:

1. [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
2. [docs/PROGRESS.md](docs/PROGRESS.md)
3. [docs/CONSTITUTION.md](docs/CONSTITUTION.md)
4. [docs/DATA_MODEL.md](docs/DATA_MODEL.md)
5. the relevant skill under `skills/`

No implementation work begins while `docs/REVIEW_ADJUDICATION.md` is blocked.

## Prime directive

**Never weaken, delete, skip, stub, relabel, or `xfail` a check to make the suite pass.**
Do not lower a threshold, loosen an assertion, narrow a scan, edit a fixture's expected
finding, or change gate-driving data so a favored claim turns green.

The oracle includes more than code and tests. Treat these as oracle data:

- source assessments;
- claim-evidence locator, stance, credibility, temporal scope, origin, independence, and
  binding hashes;
- claim support/dispute/freshness/lifecycle fields;
- structured observations, units, denominators, and transformations;
- prediction locks, criteria, benchmarks, and event history;
- context packs, manifests, refuter sets, and visual specs.

A red suite is information. A falsely green suite is a landmine with a build badge.

## Work loop

```text
READ STATE → EXPLORE → WRITE 3–8 LINE PLAN → IMPLEMENT ONE WP →
WRITE INVALID FIXTURE FIRST → IMPLEMENT → RUN WP ACCEPTANCE → RUN FULL SUITE →
SELF-REVIEW DIFF → UPDATE PROGRESS → SEPARATE SCOPE/ORACLE REVIEW → COMMIT GREEN → STOP
```

1. **One work package only.** Do not auto-start the next WP.
2. **Tests define done.** Agent confidence is not an evaluation.
3. **Failing fixture first.** Prove the control can catch the named exploit before making
   clean input pass.
4. **Run the complete acceptance suite.** Preserve every passing control.
5. **Stop after two failed repair loops** on the same failure and report the blocker.
6. **Commit only green work.** One WP is one rollback point.
7. **Update `docs/PROGRESS.md` before commit.** Record files, commands/results,
   assumptions, oracle-data changes, commit, and next step.

## Governance and scope review

Before committing, run a separate fresh-context review whose narrow job is to inspect the
diff for:

- scope creep beyond the active WP;
- weakened or deleted checks;
- silent skips or zero-input passes;
- oracle-data changes that benefit claims, predictions, or visuals;
- schema drift not accompanied by migration updates;
- new dependencies without a declared need;
- changes to record hashes or canonicalization rules.

The same diff may not quietly change both a source/relationship assessment and a claim
that benefits from it. Use an explicit adjudication exception or separate changes.

## Anti-overbuild

Implement the smallest change that satisfies the active WP. Do not pre-build later phases:

- no source scorer before the source-assessment WP;
- no vector database before WP7.3 demonstrates need;
- no model entailment gate before WP7.2;
- no maps before geography and observation integrity exist;
- no dashboards before deterministic scoring;
- no autonomous web-research pipeline in the current plan;
- no Centaur integration unless a later WP names it.

Missing ideas go to the candidate backlog in `docs/PROGRESS.md`, not into the current diff.

## Record integrity

- A source entity is not evidence.
- Claims never cite source IDs directly as proof.
- Artifacts are immutable by content hash.
- Claim-evidence assessments and source assessments are append-only; corrections
  supersede.
- Reviewed claim text never changes in place. Candidate text may change before first
  review; promotion binds the final content hash.
- Visuals and calculations use structured observations, never values parsed from prose.
- Maps use geography records and real coordinates, never model-memory placement.
- Prediction locks are meaningless without the external anchor; fail closed if it is
  unavailable.

## Research work

Real research begins only in WP4.5 or an explicitly named later WP (WP4.5 has landed; real
seeding lives in the private corpus via `--root private/corpus`, and the public factbase stays
empty). During research:

1. query the fact repository first;
2. mark model-memory suggestions as candidates, never facts;
3. retrieve exact artifacts;
4. record claim-specific support and origin chains;
5. use a human or different-model review for baseline/high-impact claims;
6. promote only after gates and review;
7. preserve rejected candidates and reasons in the review packet.

Do not fabricate locators, quotes, dates, coordinates, reliability samples, or review
outcomes to complete a work package.

## Visual work

Follow `skills/visuals/SKILL.md`:

- choose the simplest useful visual;
- use observation IDs for values;
- use real geometry IDs for maps;
- declare transformations, filters, aggregation, and missing-data policy;
- emit metadata and normalized data sidecars;
- inspect after rendering;
- bind the final visual hash into the analysis manifest.

A beautiful chart of the wrong denominator is still wrong, only with better typography.

## Gates fail closed

A check that cannot actually run—missing dependency, no files, unreadable registry, empty
rule set, unresolved reference, unavailable anchor—must exit `2` with a specific error.
It must never report success or silently skip.

Exit codes are fixed:

- `0`: clean;
- `1`: findings in valid inputs;
- `2`: usage error or the control could not genuinely run.

## Fixtures and determinism

- Fixtures live under `tests/fixtures/` and are synthetic.
- Every gate gets valid, invalid/adversarial, and regression coverage.
- Broad repository scans exclude fixtures by default; tests pass fixture paths explicitly.
- Tests do not hit the network.
- Wall-clock time is injectable.
- Randomness is seeded or absent.
- Output order is deterministic.
- Visual tests compare normalized data and metadata exactly; image checks are structural,
  not brittle pixel snapshots.

## Dependencies and commands

Use Python 3.11+ in a repository venv:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

All documented runtime commands use `.venv/bin/python`. Prefer the standard library.
Add dependencies only in the phase that needs them, with a concrete justification and
version range. A missing required package fails closed.

## Completion report

Every WP report states:

- files changed;
- exact commands and exit results;
- fixtures added;
- assumptions and deferred work;
- oracle-data changes;
- migration implications;
- separate review result;
- commit hash;
- exact next WP, or blocker.

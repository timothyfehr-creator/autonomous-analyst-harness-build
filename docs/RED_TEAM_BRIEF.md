# RED TEAM BRIEF — v2 constitution, fact repository, and visuals

Use this brief in a fresh, different model before building code. Do not ask for general
feedback. Assign the attack.

## Paste-in prompt

> You are red-teaming the v2 Analyst Harness before code exists. It is a private,
> single-user research system for a live, disinformation-heavy conflict. Its core chain is
> source entity → exact artifact → claim-evidence assessment → atomic claim, with typed
> observations for calculations/visuals, a reviewed baseline fact repository, answer
> manifests/refuters, and a tamper-evident forecast ledger.
>
> Your job is to find where it **fails**, not to improve its wording. For every material
> problem: state the failure mode, give a concrete breaking case, classify it as fatal,
> fixable, or acceptable-with-eyes-open, and provide the exact test that would prove a fix.
> Do not propose a redesign until you have enumerated failures. Be adversarial and specific.
>
> Attach/paste: `docs/CONSTITUTION.md`, `docs/DATA_MODEL.md`,
> `IMPLEMENTATION_PLAN.md`, `AGENTS.md`, `CLAUDE.md`, `README.md`,
> `docs/PROGRESS.md`, `docs/REVIEW_ADJUDICATION.md`, `docs/KNOWLEDGE.md`,
> `docs/TOOLING.md`, `docs/EXAMPLE_WORKFLOW.md`,
> `skills/fact-repository/SKILL.md`, `skills/visuals/SKILL.md`,
> `factbase/sources.yaml`, `factbase/source_assessments.yaml`,
> `factbase/evidence.yaml`, `factbase/claim_evidence.yaml`,
> `factbase/observations.yaml`, `factbase/geography.yaml`,
> `factbase/baseline/claims.yaml`, and `factbase/live/claims.yaml`.

## Bets to attack hardest

### 1. Did v2 actually eliminate source laundering?

Can a user game `origin_chain`, `independence_group`, source reliability, information
credibility, or semantic-review hashes so two derivative reports look independent? Is the
“authoritative primary or A–C chain” rule coherent, or can an interested official still
bootstrap corroboration? Can one artifact be split into multiple assessments to create
fake corroboration?

### 2. Is semantic review a real control or a better-dressed checkbox?

The system records an exact locator and `CHECKED` review, but the machine cannot prove
support. What is the cheapest way for a model to mark a displaced citation checked? Can
hash binding prove only that the wrong judgment was made consistently? Does the reviewer
workflow create enough friction to be skipped in daily use?

### 3. Can the baseline repository fossilize mistakes?

Attack the durable/history/live classifier, promotion event, `review_by`, refresh, and
supersession rules. Can a volatile state be worded abstractly enough to pass as durable?
Can a historical list create misleading completeness? Can old facts dominate context
packs after the world changes? Is the initial corpus small enough to review and useful
enough to justify maintenance?

### 4. Can context selection manufacture consensus?

Attack token budgets, deterministic ranking, omitted-candidate logs, topic tags, and
contested-pair handling. Can a context pack technically record omissions while still
serving a biased answer? Can stale or low-quality baseline records crowd out fresh
contrary evidence? Does query-first create automation bias toward the repository?

### 5. Are observations an integrity layer or a second truth system?

Construct cases where the claim and support are correct but the observation value, unit,
denominator, time scope, geography, or uncertainty is wrong. Can the validator detect a
wrong extraction that is internally consistent? Can derived observations hide an
arbitrary transformation? Can a corrected observation leave old visuals apparently valid?

### 6. Can visuals be wrong while every record is valid?

Attack:

- swapped longitude/latitude;
- wrong CRS;
- centroid used as event location;
- route used as control area;
- wrong denominator or aggregation;
- missing contradictory series;
- crop excluding inconvenient features;
- annotations not tied to records;
- stale geometry after validation;
- schematic arrows implying causality;
- sidecars matching the wrong render.

The tool is private, so do not invent publication-risk bureaucracy. Focus on whether the
visual leads the user to reason from a wrong input.

### 7. Is the refuter independent enough?

Same-model fresh-context review is explicitly downgraded. Is `DIFFERENT_MODEL` actually
independent if both models receive the same curated context pack and share the same source
blind spots? Can the manifest set be complete while the analysis omits its weakest
assertions? Does exact set equality merely prove complete review of an incomplete set?

### 8. Is the prediction ledger truly tamper-evident?

Attack the external local anchor: backup rollback, deletion, replay, clock manipulation,
multiple worktrees, machine migration, and resolving only favorable predictions. Does the
ledger define a forecast universe and benchmark well enough to measure skill rather than
question selection?

### 9. Incentives and daily-use failure

What behavior does the contract reward? Under-claiming? Over-atomization? Endless
candidate status? Avoiding visuals because observation creation is tedious? Copying a
trusted baseline without re-reading the support? Predict the first shortcut a single user
or agent will take after 30 days.

### 10. Governance gaming

Can an agent mark a prior finding resolved in prose while the proving test does not exist?
Can WP0.0 be satisfied by editing adjudication metadata? Does “one WP at a time” prevent
necessary cross-cutting fixes or encourage duplicate schemas? Can oracle-data and code
changes be split across commits to evade same-change policy?

## Mandatory artifacts

Produce:

1. passing-but-bad YAML for a claim/support graph that the plan would accept;
2. passing-but-bad observation and visual spec;
3. a baseline fact that is technically durable but operationally stale/misleading;
4. a context pack that records omissions yet biases the answer;
5. a prediction-history manipulation sequence;
6. a ranked fatal/fixable/acceptable list;
7. the first likely production shortcut and a minimal design response.

## What to bring back

- **Fatal:** incorporate into constitution/data model/plan before WP0.0.
- **Fixable:** log as explicit work packages or acceptance additions.
- **Acceptable:** state in Constitution §13 and this adjudication ledger.

A review is invalid if it reports only wording improvements, praises the architecture,
fails to produce adversarial artifacts, or treats internal consistency as semantic truth.

# KNOWLEDGE POLICY — Baseline fact repository

The baseline repository exists to amortize expensive verification. A durable fact checked
well once should not require a fresh research round every time the same question recurs.
That is the high-ROI core of the harness.

The repository is not a dumping ground for “things the model remembers.” Its value comes
from the retrieval, exact support, and review pass. A wrong baseline fact is worse than no
baseline fact because it is inherited silently across sessions.

## 1. Three compartments

### 1.1 Durable facts

Stable geography, definitions, institutional structure, infrastructure properties, and
other propositions expected to remain true.

**Inclusion test:** would the proposition have been equally true one year ago and likely
remain true one year from now?

Examples of suitable categories:

- a crossing supports specified transport modes;
- a port lies within a named administrative geography;
- a pipeline's designed route connects named nodes;
- a military acronym or logistics concept has a stable definition;
- a historical legal/institutional arrangement was established on a specific date.

Durable does not mean immortal. Every durable claim has `review_by`, and changes create a
replacement claim plus supersession.

### 1.2 Append-only history

Dated events remain true, but the list grows.

Examples:

- attacks on a bridge or port;
- changes to sanctions regimes;
- documented damage/repair events;
- major campaign milestones;
- official policy decisions.

Record each event separately. Never freeze a count such as “the bridge has been attacked
N times” when the durable object is really the appendable event list.

### 1.3 Live facts

Current state belongs under `factbase/live/`, not baseline:

- current control lines;
- force disposition;
- operational status;
- refinery outage percentages;
- daily or weekly flows;
- current casualty estimates;
- active restrictions and temporary closures.

These claims expire through explicit dates or named freshness profiles. A live claim may
later become a historical event, but not a timeless baseline proposition.

## 2. Traps

### Historical does not mean settled

Casualty totals, equipment-loss estimates, displacement counts, and economic losses are
revised and contested even when they refer to the past. Store them as dated claims with
scope, methodology, dispute state, and sources. Do not promote them as timeless totals.

### Definition drift

Military, legal, and economic terms can be used differently by different institutions.
A definition claim states whose convention it records and whether it is normative,
operational, or colloquial.

### Geometry drift

Administrative borders, control areas, routes, and infrastructure can change. Geometry
records declare spatial semantics, CRS, and validity dates. A structure centroid is not an
event location; a route centerline is not a control area.

### Model-memory fossilization

Model memory may identify candidate topics and plausible wording. It may not provide the
retrieval locator, quote, coordinate, or final fact. Any such candidate begins
`CANDIDATE / UNVERIFIED`.

## 3. Topic taxonomy

Begin narrow and operationally useful. Suggested top-level topics:

```text
geography
infrastructure
transport-logistics
energy-refining
military-concepts
air-defense
maritime
sanctions-economics
institutions
war-chronology
methodology
```

Use secondary tags for locations, infrastructure objects, campaigns, and data conventions.
Do not build a formal ontology before simple query usage proves it necessary.

## 4. Research and promotion workflow

### Stage 1 — Query

Search reviewed baseline and valid live claims before researching. The query output must
show status, review/expiry dates, assessment IDs, artifact IDs, observation IDs, and
hashes.

### Stage 2 — Candidate

When the repository lacks the needed proposition:

1. write one atomic candidate claim;
2. assign stability and topic;
3. make temporal semantics explicit;
4. record model-memory origin only as `UNVERIFIED`, never as evidence.

Create structured observations only when a typed value will be reused in a calculation,
comparison, or visual. Do not create them merely because a sentence contains a number.

### Stage 3 — Retrieve exact artifacts

Prefer, in order where available:

1. authoritative primary records or stable datasets;
2. accountable independent reporting;
3. recognized institutional analysis;
4. social material as a lead, direct observation, or unique artifact—not as a magical
   lower tier that becomes true when quoted elsewhere.

Capture canonical locator, publication/occurrence and retrieval times, content hash, and a
snapshot where needed.

### Stage 4 — Assess the relationship

For each artifact, record:

- exact support locator;
- support summary;
- stance;
- information credibility;
- claim-specific temporal scope;
- origin chain;
- independence group;
- semantic review.

Corroboration requires independent origins. Two news stories reproducing the same
statement are one chain.

### Stage 5 — Review

Baseline and high-impact claims require a human, different model, or mixed review. The
review checks:

- exact support rather than nearby wording;
- claim atomicity and scope;
- independence and laundering;
- disconfirming evidence;
- temporal validity;
- observation extraction, units, denominator, and geography;
- whether the claim belongs in durable, append-only, or live storage.

### Stage 6 — Promote

Promotion is an explicit command and append-only event. It changes only lifecycle from
`CANDIDATE` to `REVIEWED`, binding the unchanged claim-content hash plus assessment,
artifact, and review hashes.

After promotion, correction means replacement and supersession—not a quiet edit.

## 5. Query and context behavior

Default query selection excludes:

- candidates unless explicitly requested;
- stale or review-due claims when current facts are required;
- superseded and rejected claims;
- claims without active checked support;
- broad source groups as evidence.

A context pack freezes all selected IDs and hashes. It has a token budget, deterministic
selection policy, and an omission ledger. If a contested pair does not fit, the builder
must keep both or omit both with a reason; it may not trim contradiction into consensus.

Context packs may include observation IDs for calculations and visuals. They may not
extract values from claim prose on the fly.

## 6. Maintenance

Run `fact.py review-due` regularly. It reports:

- durable claims whose `review_by` has passed;
- volatile claims approaching or beyond expiry;
- artifacts whose locators no longer resolve where a snapshot is absent;
- assessments bound to superseded claim/artifact hashes;
- observations whose source assessments or claims are no longer active.

`fact.py refresh` creates new candidate artifacts and assessments. It never refreshes a
claim by changing a date alone.

## 7. Initial seed scope

WP4.5 should remain deliberately small:

- 10–15 durable geography/infrastructure claims, especially Crimea/Black Sea logistics
  and recurring transport chokepoints;
- 10–15 dated historical events forming a minimal chronology;
- 5–10 recurring definitions or measurement conventions for logistics, energy/refining,
  and military concepts.

This corpus is large enough to prove value and expose schema friction, but small enough to
review properly. A hundred rushed “facts” would be a regression disguised as momentum.

## 8. What baseline status does and does not mean

Baseline status means:

- the proposition passed the repository's promotion controls;
- its exact support and review trail are available;
- its maintenance date is explicit;
- future sessions may reuse it without re-researching unless the question turns on a
  disputed detail.

It does not mean:

- universally true;
- permanently current;
- free of framing;
- safe to publish;
- immune to correction.

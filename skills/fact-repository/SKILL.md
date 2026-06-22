---
name: fact-repository
status: design-spec-until-WP4.6
purpose: Reuse reviewed durable facts without importing stale or model-memory claims.
---

# Fact Repository Skill

Use this skill whenever a question may benefit from previously checked geography,
history, infrastructure, institutions, definitions, or measurement conventions.

## Core rule

**Query first. Research the gap. Promote only after evidence and review.**

The repository stores atomic claims, exact artifacts, claim-specific assessments, and—when
useful—structured observations. It is not a notebook of remembered answers.

## When to invoke

Invoke for:

- a recurring Russia–Ukraine question;
- background geography or infrastructure;
- a historical timeline;
- institutional or military definitions;
- a calculation or visual that may reuse a typed value;
- an answer where prior verified context can reduce retrieval work.

Do not invoke merely to decorate an answer with background. The best context pack is often
smaller than the model's first instinct.

## Workflow

### 1. Query before researching

```bash
.venv/bin/python scripts/fact.py query \
  --topic <topic> \
  --format yaml
```

Inspect:

- lifecycle, support, dispute, freshness, and stability;
- `review_by` or `expires_at`;
- active claim-evidence assessment IDs;
- artifact IDs;
- structured observation IDs;
- claim and record hashes.

Use only reviewed, valid, non-superseded records by default. A stale record is a lead, not
current context.

### 2. Decide whether the repository already answers the question

- **Complete:** build a context pack and continue.
- **Partially complete:** use valid records and research only the gap.
- **Absent:** create candidate claims.
- **Conflicted:** preserve both sides; do not query-filter the inconvenient half away.

### 3. Classify the missing proposition

Choose one:

- `DURABLE` — would have been equally true a year ago and likely remain true a year from
  now;
- `APPEND_ONLY_HISTORY` — a dated event that stays true while the list grows;
- `VOLATILE` — current state requiring expiry/refresh.

Do not put current force counts, outage percentages, control lines, casualty estimates, or
similar revisable quantities into the durable baseline.

### 4. Create an atomic candidate

```bash
.venv/bin/python scripts/fact.py candidate \
  --topic <topic> \
  --type FACT \
  --stability <DURABLE|APPEND_ONLY_HISTORY|VOLATILE> \
  --text "One checkable proposition"
```

Model memory may suggest wording. It does not supply evidence. Candidate status must remain
`UNVERIFIED` until artifacts and assessments exist.

### 5. Retrieve exact artifacts

For every candidate:

- capture the exact article, statement, report, post, dataset, image, video, or document;
- record canonical locator, dates, content hash, and snapshot where needed;
- identify the actual origin chain rather than only the page that repeated it;
- avoid broad source groups as evidence.

Do not invent quotes, page numbers, coordinates, dates, or URLs.

### 6. Assess each artifact against the claim

```bash
.venv/bin/python scripts/fact.py assess \
  --claim clm-id \
  --evidence evd-id
```

Record:

- exact support locator;
- support summary;
- stance;
- information credibility;
- temporal scope;
- origin chain;
- independence group;
- semantic review state and hashes.

Two outlets repeating one official statement are one information origin. Count origins,
not tabs.

### 7. Create observations only for reusable values

Create a structured observation when a value will be:

- plotted;
- compared;
- calculated with;
- reused across answers;
- bound to geography.

Record value type, unit, denominator/basis, time scope, geography, uncertainty, claim ID,
and checked assessment IDs. Do not create observations simply because prose contains a
number. Do not parse values from prose during rendering.

### 8. Run records validation

```bash
.venv/bin/python scripts/verify.py --mode records
```

A green records run establishes structural and review-binding consistency. It does not
replace semantic review.

### 9. Request the correct review

Baseline and high-impact claims require `HUMAN`, `DIFFERENT_MODEL`, or `MIXED`. A
same-model fresh-context pass may help but does not qualify as independent.

The review should attack exact support, claim scope, origin independence, contrary
evidence, freshness, and any observation extraction.

### 10. Promote or reject

```bash
.venv/bin/python scripts/fact.py promote --claim clm-id --review ref-id
```

Promotion performs only the controlled lifecycle transition `CANDIDATE`→`REVIEWED` and
appends a hash-bound event. It does not rewrite support or provenance.

After promotion, substantive correction requires:

```bash
.venv/bin/python scripts/fact.py supersede \
  --claim clm-old \
  --replacement clm-new
```

Rejected candidates remain visible in the review packet so the same weak claim is not
rediscovered next week with a different haircut.

### 11. Build a bounded context pack

```bash
.venv/bin/python scripts/fact.py context \
  --topic <topic> \
  --output context.yaml
```

The pack freezes exact claim, assessment, artifact, observation, and optional prediction
IDs/hashes. It records omitted candidates and reasons. Preserve contested pairs.

## Maintenance

```bash
.venv/bin/python scripts/fact.py review-due
.venv/bin/python scripts/fact.py refresh --claim clm-id
```

`refresh` creates new candidate evidence and assessment records. Never “refresh” by typing
today's date into an old claim.

## Failure rules

Stop and report a gap rather than:

- using model memory as support;
- citing a source identity without an exact artifact;
- treating multiple republications as corroboration;
- promoting a volatile estimate into durable baseline;
- changing reviewed claim text in place;
- creating a chart value without an observation;
- inventing a reviewer or review outcome.

## Completion checklist

- [ ] Queried first.
- [ ] Used no stale, rejected, or superseded default records.
- [ ] Classified durable/history/live correctly.
- [ ] Candidate is atomic.
- [ ] Exact artifacts captured.
- [ ] Claim-specific assessments include locators, stance, time, origin, independence.
- [ ] Any reusable values are structured observations with units/basis.
- [ ] Records mode passes.
- [ ] Qualifying review exists.
- [ ] Promotion event binds unchanged content and review hashes.
- [ ] Context pack freezes exact inputs and records omissions.

## Evaluation scenarios for WP4.6

1. Repository already contains a reviewed durable fact: agent queries and reuses it.
2. Only stale live claim exists: agent researches/refreshes rather than silently using it.
3. Model memory supplies a plausible fact: agent creates candidate, not reviewed claim.
4. Two articles share one origin: agent assigns one independence group.
5. A percentage lacks denominator: agent refuses observation until basis is resolved.
6. A reviewed fact needs correction: agent creates replacement and supersedes.
7. A context token limit would drop a contested counterclaim: agent keeps both or omits
   both with explicit reason.

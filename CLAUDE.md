# CLAUDE.md — Analyst Harness v3

Project guidance for Claude Code. It supplements [AGENTS.md](AGENTS.md); where they differ,
AGENTS wins.

## Mission

Build a private research harness that makes the chain from source to answer inspectable
and difficult to game. The useful product is not “lots of YAML.” It is:

1. a trustworthy private answer loop;
2. a reusable baseline fact repository;
3. accurate charts, timelines, maps, and schematics on request;
4. a tamper-evident forecast ledger over time.

A green result means the requested checks ran and the recorded relationships are coherent.
Never phrase it as a truth certificate.

**Tier discipline (v3, Constitution §1).** Default to **Tier 0 — conversational**: an
honestly-labeled, interesting answer with no records or manifest. Build/keep records (Tier 1)
or a committed answer with refuter (Tier 2) only when a claim is worth reusing, charting, or
depending on. Never silently force the heavy chain onto a casual question; the heavy modes
are escalation, not the price of speaking. See `docs/CONVERSATION.md`.

## Architecture to preserve

```text
source entity
  → exact evidence artifact
  → claim-evidence assessment
  → atomic claim
  → structured observation (when a reusable value is needed)
  → context pack / analysis manifest
  → answer and optional visual
  → refuter bound to exact output hash
```

Do not collapse layers for convenience:

- source type is not reliability;
- source reliability is not information credibility;
- an artifact is not a claim verdict;
- a claim is not a chart datum;
- same-model fresh-context review is not independent review;
- Git history is not an immutable prediction anchor.

## Work discipline

- Read `IMPLEMENTATION_PLAN.md` and `docs/PROGRESS.md` before editing.
- Do not start while review adjudication is blocked.
- Implement one WP, run its exact acceptance, run full tests, review the diff, update
  progress, commit green, and stop.
- Do not pull later-phase machinery forward because it feels elegant.
- Do not invent data to make a fixture or seed corpus look complete.

## Product bias

This is a single-user tool. Prefer useful, lightweight controls over enterprise ceremony.
The plan deliberately puts the answer loop, baseline facts, and visuals before calibration
polish. Preserve that order.

Presentation-risk bureaucracy is not the goal. Accuracy is. For maps, use real geometry
because wrong placement corrupts reasoning, not because a private map needs a press-office
disclaimer. For baseline facts, source once carefully because inherited memory errors
compound every session.

## Research behavior

When answering with the repository:

1. query before researching;
2. use reviewed/current records when available;
3. show explicit gaps;
4. create candidates from model memory, never facts;
5. retrieve exact artifacts and assess them against atomic claims;
6. create observations for values reused in calculations or visuals;
7. build a deterministic context pack;
8. bind the answer and any visual to exact hashes;
9. run the required refuter.

## Visual behavior

Follow `skills/visuals/SKILL.md`. Use:

- Matplotlib for deterministic charts and static maps;
- Folium/Leaflet for interactive maps;
- GeoPandas, Shapely, and PyProj for real geometry and CRS handling;
- Mermaid or Graphviz for conceptual schematics after WP5.4 selects the reliable tool.

Never draw geographic positions from memory. Never parse a chart value from claim prose.
Do not guess missing coordinates, units, denominators, or transformations.

## Commands

```bash
.venv/bin/python scripts/verify.py --mode scaffold
.venv/bin/python scripts/verify.py --mode records
.venv/bin/python scripts/verify.py --mode draft
.venv/bin/python scripts/verify.py --mode answer --analysis ana-id
pytest
```

Until a mode's WP lands, it must exit `2` as explicitly unavailable. `SKIP` is not `PASS`.

## Non-goals

Do not build autonomous web retrieval, a public release pipeline, truth scoring, a vector
database, publication cartography, or Centaur integration unless a named WP is active.

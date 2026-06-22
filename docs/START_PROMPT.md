# START_PROMPT — kickoff for planning & building in Claude Code

Paste this into Claude Code (or run it as an Ultraplan if you've pushed the repo to GitHub).
It is deliberately strict: it makes Claude Code **read, then plan, then build one step** —
never improvise past the plan, never start coding while governance is blocked.

---

You are working in the **analyst-harness-v3** repository: a private, single-user research
harness with a tiered-rigor model (Tier 0 conversational = default lightweight; Tiers 1–2 =
the opt-in evidence chain). Do **not** create or edit any code, schema, or fixture until you
have completed steps 1–3 below.

## 1. Read, in this exact order. Do not skip; do not skim.

1. `AGENTS.md` — operating rules. The **prime directive is absolute**.
2. `IMPLEMENTATION_PLAN.md` — the backlog, the milestones, and the tiered-rigor model.
3. `docs/PROGRESS.md` — current state.
4. `docs/CONSTITUTION.md` — what the harness enforces; the three tiers (§1); the
   accepted limitations (§15).
5. `docs/DATA_MODEL.md` — the normative record shapes.
6. `MERGE_NOTES.md` and `docs/REVIEW_V3_SELFPASS.md` — why the design is what it is, and its
   known soft spots (especially the self-judged escalation boundary, F1/F2).

When done, give me a ≤10-line summary proving you read them: the record types, the three
tiers, the prime directive, and the current governance state.

## 2. Governance gate — check before anything else.

Open `docs/REVIEW_ADJUDICATION.md`.

- If `governance_status` is **not** `READY`, or `external_review_complete: false`, or any
  finding is `BLOCKING`: **STOP. Do not implement.** Report exactly: *"Governance is BLOCKED:
  a cold external review of v3 must be completed and adjudicated before WP0.0."* Then offer —
  but do not perform unprompted — to (a) run `docs/REVIEW_PROMPT.md` to prepare that review,
  or (b) produce a Phase-0 plan **without writing code**.
- Only when `governance_status: READY` **and** `open_p0_p1: 0` may you proceed to step 3 and
  beyond. Do not edit the adjudication file yourself to unblock it — that is an oracle-data
  change and a prime-directive violation.

## 3. Plan first (plan mode). No code yet.

- Confirm the environment: a `.venv` exists with `pytest` + `PyYAML`. The host has **no
  `python` binary** — every command you plan or run uses `.venv/bin/python`.
- Produce an execution plan for **Phase 0 only** — WP0.0, WP0.1, WP0.2, WP0.3 — and nothing
  beyond it. For each WP list: the files it creates, the **exact acceptance commands from the
  plan**, and the valid / invalid / regression fixtures it ships. Note WP0.3 is a docs
  deliverable (`docs/CONVERSATION.md`), not code, and incorporate the self-pass F1/F2 fix —
  objective escalation triggers, not "if you feel it matters."
- Do **not** plan Phase 1 or later. Present the plan and **stop for my approval.**

## 4. Build — only after I approve the plan, and only if governance is READY.

Implement **exactly one** work package, starting with **WP0.0**, following the AGENTS loop:

```text
write the invalid fixture first → implement → run the WP acceptance commands →
run the full suite → self-review the diff → update docs/PROGRESS.md →
run a separate scope/oracle review → commit ONLY if green → STOP
```

Then stop and report. **Do not auto-start the next work package.**

## Non-negotiables (from AGENTS.md and the constitution)

- **Never** weaken, delete, skip, stub, relabel, or `xfail` a check, fixture, threshold,
  scan scope, or gate-driving datum to make the suite pass. A red suite is information; a
  falsely green suite is a landmine. If you cannot make a WP pass honestly after two repair
  attempts, **stop and report the blocker**.
- **Fail closed:** any check that cannot genuinely run exits non-zero with a clear message.
- **Anti-overbuild:** implement the smallest enforceable thing the WP names. Do not build
  ahead of its phase. Candidate ideas go in `docs/PROGRESS.md`, not into code.
- **Preserve Tier 0:** never build machinery that forces the heavy chain onto a casual
  question. The lightweight conversational default is a feature, not a gap to be closed.

## Report after every WP

Files changed; commands run + results; assumptions; deferred items; the next WP — then stop.

#!/usr/bin/env python3
"""WP2.5 — support + corroboration RECOMPUTE gate (the hardest; ships V-P1-4, V-P1-10, F3; kills A1).

Recomputes a claim's `support_status` from its ACTIVE CHECKED SUPPORTS claim-evidence assessments
and rejects an OVER-CLAIM (a stored label stronger than what the evidence earns). Per the §6 chain:

  SUPPORTED   = >=1 active CHECKED SUPPORTS assessment (§6.1).
  CORROBORATED = a four-part conjunction (§6.1a/§6.1b, §3 independence):
    C1  >=2 INDEPENDENT origins — independence is counted by the UNDERLYING origin
        `origin_chain[0].source_id` (DATA_MODEL §4 convention: origin first, relay last), so two
        assessments that trace to the same underlying source collapse to ONE origin;
    C2  an authoritative-primary `primary_evidence_kind` is present (closed kind, V-P1-4);
    C3  FIRST_PARTY_ACTION_RECORD chains are EXCLUDED from the C1 tally — a belligerent's own
        first-party record may satisfy C2 but cannot manufacture independence. This is the A1 kill:
        a belligerent's first-party claim + one wire that republishes it collapse to one origin;
    C4  the credibility floor (V-P1-10) — at least one chain that COUNTS toward C1 (i.e. a non-
        first-party chain) has integer `information_credibility` <= 3. UNASSESSED/4/5/6 fail; this
        is also the F3 Tier-1 cap (a coarse Tier-1 assessment without a <=3 credibility cannot
        reach CORROBORATED, only SUPPORTED).

Reject direction: OVER-CLAIM only — a stored SUPPORTED/CORROBORATED stronger than computed fails;
an under-label (e.g. stored SUPPORTED while the records earn CORROBORATED) passes (conservative).
This mirrors the high_impact recompute; the docs' "recompute and reject a mismatch" reads literally
symmetric — flagged as the one owner-overridable choice. Recompute is scoped to FACT/INFERENCE
(evidence-bearing types); ASSUMPTION carries no evidence and PROJECTION's CORROBORATED ban is WP2.4.

Out of scope: conflict/CONTESTED/stance interaction (WP2.6); observation/unit (WP2.8); freshness
clock (WP2.7); semantic displacement / does-the-passage-really-support (the WP3.3 refuter); the
A-C-in-scope corroboration leg (C2b) is deferred — `source_assessments.yaml` is empty, so the
authoritative-primary kind is the only live CORROBORATED path.

Schema runs first per claims file. The claim-evidence registry is required (unreadable/missing/
duplicate-key → exit 2, §13). Empty factbase → 0. Exit codes: 0 / 1 / 2.
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling import
import validate_schema as vs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CLAIMS = [REPO_ROOT / "factbase" / "baseline" / "claims.yaml",
                  REPO_ROOT / "factbase" / "live" / "claims.yaml"]
DEFAULT_CEA = REPO_ROOT / "factbase" / "claim_evidence.yaml"

SUPPORT_RANK = {"UNVERIFIED": 0, "THIN": 1, "SUPPORTED": 2, "CORROBORATED": 3}
AUTHORITATIVE_PRIMARY = {"FIRST_PARTY_ACTION_RECORD", "AUTHORITATIVE_DATASET",
                         "DIRECT_SENSOR_CAPTURE", "OFFICIAL_PRIMARY_DOCUMENT"}
FIRST_PARTY = "FIRST_PARTY_ACTION_RECORD"
RECOMPUTE_TYPES = {"FACT", "INFERENCE"}  # evidence-bearing; ASSUMPTION/PROJECTION out of scope


def _origin0(a):
    """The UNDERLYING origin = origin_chain[0].source_id (DATA_MODEL §4: origin first, relay last).
    Kept for reference; independence is now counted by _independence_components (which subsumes it)."""
    oc = a.get("origin_chain")
    if isinstance(oc, list) and oc and isinstance(oc[0], dict):
        return oc[0].get("source_id")
    return None


def _chain_sources(a) -> set:
    """Every source_id appearing ANYWHERE in an assessment's origin_chain (the full provenance, not
    just origin_chain[0]). Used to detect a shared underlying origin / relay between two chains."""
    oc = a.get("origin_chain")
    if not isinstance(oc, list):
        return set()
    return {n.get("source_id") for n in oc if isinstance(n, dict) and n.get("source_id") is not None}


def independence_labels(assessments) -> list:
    """Return a component label per assessment (parallel to the input). An assessment with NO
    anchorable origin (no non-null origin_chain source_id) gets label `None` — it never counts as an
    independent origin and cannot manufacture a contest (mirrors the old `_origin0`-is-None strip).
    Two ANCHORED assessments share a label (= same origin) iff their origin_chains share ANY
    source_id (one chain echoed — wherever the shared source sits, not just [0]) OR they declare the
    same `independence_group` (Constitution §3 / §6.1). Conflict uses the labels; corroboration the count."""
    items = list(assessments)
    n = len(items)
    sources = [_chain_sources(a) for a in items]
    anchored = [i for i in range(n) if sources[i]]
    parent = {i: i for i in anchored}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for x, i in enumerate(anchored):
        gi = items[i].get("independence_group")
        for j in anchored[x + 1:]:
            same_group = gi is not None and gi == items[j].get("independence_group")
            if same_group or (sources[i] & sources[j]):
                parent[find(i)] = find(j)
    labels = [None] * n
    for i in anchored:
        labels[i] = find(i)
    return labels


def independence_components(assessments) -> int:
    """Count INDEPENDENT origins — distinct non-None component labels. A wire echoed by two outlets,
    or two assessments in one independence_group, collapse to ONE independent origin; an unanchored
    (null-origin) assessment counts as zero (closes the Milestone-A wire-echo + buried-first-party
    corroboration exploits without regressing the null-origin strip)."""
    return len({lbl for lbl in independence_labels(assessments) if lbl is not None})


def _is_floor(a) -> bool:
    """A credibility-floor clearer: integer information_credibility in the DOMAIN {1..3} (not bool;
    UNASSESSED and out-of-domain 0/negative fail — the gate reads the cea raw, so guard the domain)."""
    cred = a.get("information_credibility")
    return isinstance(cred, int) and not isinstance(cred, bool) and 1 <= cred <= 3


def active_checked_by_claim(ceas, stance=None):
    """Map claim_id -> [active CHECKED cea] (optionally filtered to one `stance`). Active = the
    un-superseded leaf of its (claim_id, artifact_id) chain (partition-scoped: only a same-pair edge
    deactivates). Tolerant of a malformed cea with a null/absent id or supersedes (fail-closed, no
    KeyError). Stance-agnostic so WP2.6 (conflict) can reuse it across REFUTES/MIXED."""
    by_id = {a.get("id"): a for a in ceas if a.get("id") is not None}
    key = lambda a: (a.get("claim_id"), a.get("artifact_id"))  # noqa: E731
    superseded = set()
    for a in ceas:
        sup = a.get("supersedes")
        if sup is not None and sup in by_id and key(a) == key(by_id[sup]):
            superseded.add(sup)
    out = defaultdict(list)
    for a in ceas:
        sr = a.get("semantic_review") if isinstance(a.get("semantic_review"), dict) else {}
        if (a.get("id") not in superseded and sr.get("status") == "CHECKED"
                and (stance is None or a.get("stance") == stance)):
            out[a.get("claim_id")].append(a)
    return out


def active_supports_by_claim(ceas):
    """WP2.5 view: active CHECKED SUPPORTS assessments per claim (thin wrapper — no behavior change)."""
    return active_checked_by_claim(ceas, stance="SUPPORTS")


def active_reliabilities_by_source(sas_records):
    """Map source_id -> set of ACTIVE reliability letters. Active = an un-superseded leaf of its
    supersedes chain (sas has no partition key — active is per connected component). A source can hold
    several active leaves (different scopes), so the value is a set."""
    by_id = {r.get("id"): r for r in (sas_records or []) if isinstance(r, dict) and r.get("id")}
    superseded = {r.get("supersedes") for r in by_id.values() if r.get("supersedes") in by_id}
    out = {}
    for r in by_id.values():
        if r.get("id") in superseded:
            continue
        sid = r.get("source_id")
        if sid:
            out.setdefault(sid, set()).add(r.get("reliability"))
    return out


def ac_rated_sources(sas_records) -> set:
    """Source_ids with an ACTIVE reliability in {A,B,C} — the §6.1 'a source assessed A-C in scope'
    corroboration leg (C2b). NOTE: 'in scope' is deferred (ASSUMED) — the sas `scope` is free-text and
    not structurally matchable today; a future WP can tighten with a structured scope / cea->sas link."""
    return {sid for sid, rels in active_reliabilities_by_source(sas_records).items()
            if rels & {"A", "B", "C"}}


def compute_support(qualifying, ac_sources=frozenset()):
    """Return (computed_label, detail). Lower bound from the active CHECKED SUPPORTS assessments.
    ac_sources = source_ids with an active A-C rating (the §6.1 reliable-source leg, off by default)."""
    if not qualifying:
        return "UNVERIFIED", "no active CHECKED SUPPORTS assessment"
    counting = [a for a in qualifying if a.get("primary_evidence_kind") != FIRST_PARTY]  # C3 exclusion
    n_origins = independence_components(counting)  # §3/§6.1: shared chain source OR independence_group collapses
    c1 = n_origins >= 2
    # C2: authoritative-primary kind OR (C2b) a COUNTING origin source assessed A-C — computed over
    # `counting` so a first-party belligerent source's rating can't back-door corroboration.
    c2_primary = any(a.get("primary_evidence_kind") in AUTHORITATIVE_PRIMARY for a in qualifying)
    c2_ac = any(s in ac_sources for a in counting for s in _chain_sources(a))
    c2 = c2_primary or c2_ac
    c4 = any(_is_floor(a) for a in counting)
    if c1 and c2 and c4:
        return "CORROBORATED", ""
    missing = []
    if not c1:
        missing.append(f"only {n_origins} independent origin(s) after first-party exclusion (need >=2)")
    if not c2:
        missing.append("no authoritative-primary evidence kind and no A-C-rated origin source")
    if not c4:
        missing.append("no counting chain with information_credibility <= 3")
    return "SUPPORTED", "; ".join(missing)


def check_support(claims, ceas, ac_sources=frozenset()) -> list[str]:
    """Over-claim findings for the schema-clean merged claim set."""
    findings = []
    active = active_supports_by_claim(ceas)
    for c in claims:
        if c.get("epistemic_type") not in RECOMPUTE_TYPES:
            continue
        stored = c.get("support_status")
        if stored not in ("SUPPORTED", "CORROBORATED"):  # THIN/UNVERIFIED are at/below the floor — never an over-claim
            continue
        computed, detail = compute_support(active.get(c.get("id"), []), ac_sources)
        if SUPPORT_RANK.get(stored, 0) > SUPPORT_RANK.get(computed, 0):
            findings.append(f"claim {c.get('id')!r}: support_status stored {stored} but the evidence "
                            f"earns only {computed} ({detail})")
    return sorted(findings)


def validate_support(claims_paths, cea_path, source_assessments_path=None):
    """Return (exit_code, findings). Schema-first per claims file; recompute on the merged set.
    source_assessments_path (optional): enables the §6.1 A-C reliable-source corroboration leg; absent
    or empty ⇒ leg off (authoritative-primary remains the only path) — preserves prior behavior."""
    schema_findings, code = [], 0
    for p in claims_paths:
        c, f = vs.validate_file(p)
        code = max(code, c)
        schema_findings += f
    if code != 0:
        return code, schema_findings
    try:
        cea_data = vs.load_yaml_strict(cea_path) or {}
        ceas = cea_data.get("claim_evidence_assessments") or []
    except Exception as e:  # noqa: BLE001 — registry read/parse failure is §13 fail-closed
        return 2, [f"cannot read the claim-evidence registry for support recompute (fail closed): {e}"]
    ac_sources = frozenset()
    if source_assessments_path is not None:
        try:
            sd = vs.load_yaml_strict(source_assessments_path) or {}
            ac_sources = ac_rated_sources(sd.get("source_assessments") or [])
        except Exception as e:  # noqa: BLE001 — a bad sas registry is §13 fail-closed
            return 2, [f"cannot read source_assessments for the A-C corroboration leg (fail closed): {e}"]
    merged = []
    for p in claims_paths:
        d = vs.load_yaml_strict(p) or {}
        merged += [c for c in (d.get("claims") or []) if isinstance(c, dict)]
    findings = check_support(merged, ceas, ac_sources)
    return (1 if findings else 0), findings


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP2.5 support + corroboration recompute gate")
    p.add_argument("paths", nargs="*", type=Path, help="claim files (default baseline+live)")
    p.add_argument("--claim-evidence", type=Path, default=DEFAULT_CEA)
    args = p.parse_args(argv)
    claims_paths = args.paths or DEFAULT_CLAIMS
    code, findings = validate_support(claims_paths, args.claim_evidence)
    for f in sorted(findings):
        print(f"  [finding] {f}", file=sys.stderr)
    if code == 0:
        print("OK — support/corroboration recompute clean. (Lower-bound recompute; NOT a truth certificate.)")
    return code


if __name__ == "__main__":
    sys.exit(main())

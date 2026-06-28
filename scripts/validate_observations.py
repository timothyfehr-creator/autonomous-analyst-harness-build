#!/usr/bin/env python3
"""WP2.8 — observation integrity: the dimensional half of V-P1-5 (kills A5). SHAPE was WP1.6.

Constitution §6.3 / V-P1-5: a numeric observation records the literal source_value/source_unit; any
value reported in a different unit or denominator must be a declared, checkable transformation from
source_value, "with derived_from resolving the denominator to a record." WP1.6 enforced the SHAPE
(units in the closed vocabulary, source_value numeric, a transformation declared for any su!=un, a
denominator requires a non-empty derived_from, derived_from is a list of obs- ids). WP2.8 adds the
cross-record / dimensional checks WP1.6 can't:

  R-OBS-1 derived_from RESOLUTION: every derived_from obs- id must resolve to a known observation
          (WP1.6 only checks the obs- prefix; this checks existence in the union of observation files).
  R-OBS-2 the A5 dimensional kill: for a NUMBER/INTEGER recast (source_unit != unit, both in the
          vocabulary) whose dimensional CLASSES DIFFER (e.g. MASS_RATE→MASS, VOLUME→DIMENSIONLESS),
          a declared transformation is not enough — the change must be backed by a NON-EMPTY
          derived_from (the record that supplies the time/denominator/factor). This catches the
          "bare absolute recast as a share via a DIMENSIONLESS unit, denominator field left null"
          path WP1.6's denominator rule misses. A same-dimensional-class conversion (kg→tonnes,
          bpd→m3/day) is a scalar/numerator change — a transformation suffices, no derived_from.

Honest residual (NOT closed; no gate can): a SAME-class wrong-denominator recast where both units
are in the vocabulary (e.g. tonnes/day↔tonnes/year if both were vocab tokens) is not structurally
distinguishable from a legitimate numerator conversion without a transformation DSL (deferred); the
named "tonnes/day-as-/year" leg is closed TODAY because `/year` is not a vocabulary token (WP1.6
not-in-vocab). Arithmetic correctness of a declared transformation is the WP3.3 refuter's job.

Deferred (flagged): observation→claim / observation→cea existence resolution + the OPEN
epistemic_type==FACT and cea-ACTIVE/CHECKED questions (general obs integrity, not the A5 kill).
Fail-closed: an empty/unreadable unit vocabulary → exit 2 (no dimensional map; §13), checked BEFORE
the per-file loop; a missing/unreadable observation registry → exit 2; a duplicate-key file → exit 1
(the schema layer's DuplicateKey path — still non-zero/gate-blocking); empty observations → 0.
Exit codes: 0 / 1 / 2.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # sibling import
import schema_defs  # noqa: E402  (UNIT_VOCABULARY: unit -> dimensional_class)
import validate_schema as vs  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OBS = REPO_ROOT / "factbase" / "observations.yaml"


def load_observations_union(paths):
    """Return (merged_records, dup_id_findings). Preserves all entries so a cross-file dup id shows."""
    merged, seen, dup = [], {}, []
    for p in paths:
        data = vs.load_yaml_strict(p) or {}
        for o in (data.get("observations") or []):
            if not isinstance(o, dict):
                continue
            merged.append(o)
            oid = o.get("id")
            if oid in seen:
                dup.append(f"duplicate id {oid!r} (appears in {seen[oid]} and {p.name})")
            else:
                seen[oid] = p.name
    return merged, sorted(dup)


def _derivation_cycles(observations) -> list[str]:
    """A derived_from graph must be acyclic and self-free — §6.3 requires derived_from to resolve
    'to a record', and a self-loop / cycle supplies no external supplier (it would let a cross-class
    A5 recast self-certify). Mirrors R-CLM-3 premise acyclicity / R-CLM-12 self-supersede."""
    adj = {o.get("id"): [d for d in (o.get("derived_from") or []) if isinstance(d, str)] for o in observations}
    color, findings, reported = {}, [], set()

    def dfs(node, path):
        color[node] = 1
        for nxt in adj.get(node, []):
            if nxt not in adj:
                continue  # unresolved parent → R-OBS-1 flags it; not a cycle node
            if color.get(nxt) == 1:
                cyc = frozenset(path[path.index(nxt):] + [node]) if nxt in path else frozenset([node])
                if cyc not in reported:
                    reported.add(cyc)
                    findings.append(f"observation derived_from cycle: {sorted(cyc)} (a derivation may "
                                    f"not trace to itself — derived_from must resolve to a supplying record)")
            elif color.get(nxt, 0) == 0:
                dfs(nxt, path + [node])
        color[node] = 2

    for n in adj:
        if color.get(n, 0) == 0:
            dfs(n, [])
    return sorted(findings)


def check_observations(observations, obs_ids, claim_ids=None, cea_ids=None) -> list[str]:
    """R-OBS-1 derived_from resolution (+ self/cycle guard) + R-OBS-2 the A5 cross-class dimensional
    check + R-OBS-3 (R3-P1-2) claim/CEA backing resolution when the registries are supplied (records
    composition passes them; the standalone gate stays dimensional-only)."""
    findings = list(_derivation_cycles(observations))
    vocab = schema_defs.UNIT_VOCABULARY
    for o in observations:
        oid = o.get("id")
        # R-OBS-1: every derived_from id must resolve to a known observation
        for d in (o.get("derived_from") or []):
            if isinstance(d, str) and d not in obs_ids:
                findings.append(f"observation {oid!r}: derived_from {d!r} does not resolve to a known observation")
        # R-OBS-3 (R3-P1-2): the observation's evidence leg must EXIST — its claim_id and every
        # claim_evidence_assessment_id must resolve, else an observation can claim backing that is
        # not there (and feed a committed answer via the manifest unrefuted).
        if claim_ids is not None:
            cid = o.get("claim_id")
            if cid is not None and cid not in claim_ids:
                findings.append(f"observation {oid!r}: claim_id {cid!r} does not resolve to a known claim")
        if cea_ids is not None:
            for a in (o.get("claim_evidence_assessment_ids") or []):
                if isinstance(a, str) and a not in cea_ids:
                    findings.append(f"observation {oid!r}: claim_evidence_assessment_ids {a!r} does not "
                                    f"resolve to a known assessment")
        # R-OBS-2: a cross-dimensional-class numeric recast must be backed by a non-empty derived_from
        if o.get("value_type") in ("NUMBER", "INTEGER"):
            su, un = o.get("source_unit"), o.get("unit")
            if su in vocab and un in vocab and su != un and vocab[su] != vocab[un]:
                if not (o.get("derived_from") or []):
                    findings.append(
                        f"observation {oid!r}: cross-dimensional-class recast {su!r}({vocab[su]}) -> "
                        f"{un!r}({vocab[un]}) requires a resolving derived_from (the dimensional change "
                        f"must trace to a record), not just a transformation — A5")
    return sorted(findings)


def validate_observations(paths, claim_ids=None, cea_ids=None):
    """Return (exit_code, findings). Vocab fail-closed first; schema-first per file; then integrity.
    claim_ids/cea_ids (records composition) enable R-OBS-3 claim/CEA backing resolution."""
    if not schema_defs.UNIT_VOCABULARY:  # the dimensional-class map could not load — cannot run (§13)
        return 2, ["[FAIL closed] unit vocabulary is empty/unreadable — no dimensional-class map "
                   "(check config/unit_vocabulary.yaml)"]
    schema_findings, code = [], 0
    for p in paths:
        c, f = vs.validate_file(p)
        code = max(code, c)
        schema_findings += f
    if code != 0:
        return code, schema_findings
    merged, dup = load_observations_union(paths)
    obs_ids = {o.get("id") for o in merged}
    findings = dup + check_observations(merged, obs_ids, claim_ids, cea_ids)
    return (1 if findings else 0), findings


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP2.8 observation integrity gate (dimensional / A5)")
    p.add_argument("paths", nargs="*", type=Path, help="observation files (default factbase/observations.yaml)")
    args = p.parse_args(argv)
    paths = args.paths or [DEFAULT_OBS]
    code, findings = validate_observations(paths)
    for f in sorted(findings):
        print(f"  [finding] {f}", file=sys.stderr)
    if code == 0:
        print("OK — observation integrity clean. (Structural dimensional check; NOT a truth certificate.)")
    return code


if __name__ == "__main__":
    sys.exit(main())

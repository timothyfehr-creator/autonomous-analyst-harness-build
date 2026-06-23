"""Shared supersession-chain structural checks (extracted from WP2.2b; reused by WP2.3b).

A supersedes graph where each record points to AT MOST one predecessor (the older record it
corrects). A well-formed registry is a forest of chains, each terminating at a null root and having
exactly one ACTIVE leaf (the un-superseded current record). This enforces:
  - no self-supersede (a self-loop is not a chain);
  - no orphan supersedes (a non-null pointer must resolve to a known record in the same log);
  - no supersession cycle (walking supersedes must terminate at a null root);
  - exactly one active leaf per chain.

With a `partition_key`, a chain is scoped to records sharing that key (e.g. a claim-evidence
chain is per `(claim_id, artifact_id)` pair): a supersedes edge that CROSSES partitions is itself
a finding, and leaf-counting / union are done only within a partition. With no `partition_key`
(the source-assessment case) a chain is any connected supersedes component, preserving WP2.2b
behaviour exactly.
"""
from __future__ import annotations

from collections import defaultdict


def check_supersession(records, *, partition_key=None, label="record") -> list[str]:
    """Return deterministically-sorted structural findings for one append-only log."""
    findings = []
    ids = {r.get("id") for r in records}
    by_id = {r.get("id"): r for r in records}
    keyfn = partition_key or (lambda _r: None)

    # self-supersede / orphan pointer / cross-partition edge
    for r in records:
        rid, sup = r.get("id"), r.get("supersedes")
        if sup is None:
            continue
        if sup == rid:
            findings.append(f"{label} {rid!r} cannot supersede itself")
        elif sup not in ids:
            findings.append(f"{label} {rid!r} supersedes {sup!r} which does not resolve to a known {label}")
        elif partition_key is not None and keyfn(r) != keyfn(by_id[sup]):
            findings.append(f"{label} {rid!r} supersedes {sup!r} across different chains "
                            f"({keyfn(r)} vs {keyfn(by_id[sup])}); a chain may not cross partitions")

    # cycle detection (walk supersedes pointers; dedupe by the cycle's node set)
    reported = set()
    for r in records:
        seen, cur = [], r.get("id")
        while cur is not None and cur in by_id:
            if cur in seen:
                key = frozenset(seen[seen.index(cur):])
                if key not in reported:
                    reported.add(key)
                    findings.append(f"{label} supersession cycle: {sorted(key)}")
                break
            seen.append(cur)
            cur = by_id[cur].get("supersedes")

    # one active leaf per chain (component via resolvable, same-partition supersedes edges)
    parent = {rid: rid for rid in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in records:
        sup = r.get("supersedes")
        if sup is not None and sup in ids and (partition_key is None or keyfn(r) == keyfn(by_id[sup])):
            parent[find(r.get("id"))] = find(sup)

    superseded = {r.get("supersedes") for r in records
                  if r.get("supersedes") in ids and r.get("supersedes") is not None}
    in_cycle = set().union(*reported) if reported else set()
    leaves = defaultdict(list)
    for rid in ids:
        if rid not in superseded and rid not in in_cycle:  # un-superseded, non-cyclic = active leaf
            leaves[find(rid)].append(rid)
    for _comp, lvs in sorted(leaves.items()):
        if len(lvs) > 1:
            findings.append(f"supersession chain has {len(lvs)} active leaves {sorted(lvs)}; "
                            f"exactly one is allowed")

    return sorted(findings)

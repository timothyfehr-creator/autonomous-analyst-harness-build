#!/usr/bin/env python3
"""Phase 4 (lean MVP) — the fact-repository tool.

  fact.py add <spec.yaml> --as-of <ts> [--root DIR]
      Build a CHECKED fact from a retrieved artifact + an EXACT quote, validate it through the
      records integrity gates, and persist ONLY if it composes clean (fail-closed). A fact traces
      to a real retrieved artifact and a verbatim quote — never model memory.

  fact.py query [--root DIR] [--topic T] [--text S] [--id clm-...]
      List the baseline facts and the source + quote backing each.

  fact.py source <spec.yaml> --as-of <ts> [--root DIR]
      Ensure a source identity + append SCOPED reliability ratings (A-F sas- records), validate the
      source + governance gates (independent of the claim DAG), persist ONLY if clean. Ratings are
      dated, scoped, append-only judgments — separate from per-claim credibility.

The corpus lives under <root>/factbase (default: the repo). Keep a REAL corpus in a gitignored
location (e.g. `--root private/corpus`) so the public repo's factbase stays empty.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import schema_defs as sd  # noqa: E402
import validate_assessment_governance as v_gov  # noqa: E402
import validate_conflict as v_con  # noqa: E402
import validate_freshness as v_fresh  # noqa: E402
import validate_schema as vs  # noqa: E402
import validate_sources as v_src  # noqa: E402
import validate_support as v_sup  # noqa: E402
import verify  # noqa: E402
import yaml  # noqa: E402

# factbase file (under factbase/) -> its list collection key
FB_FILES = {
    "sources.yaml": "sources", "source_assessments.yaml": "source_assessments",
    "evidence.yaml": "evidence", "claim_evidence.yaml": "claim_evidence_assessments",
    "baseline/claims.yaml": "claims", "live/claims.yaml": "claims",
    "predictions.yaml": "predictions", "observations.yaml": "observations",
    "geography.yaml": "geography",
}


def _slug(text, n=6):
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return "-".join(words[:n])[:48] or "x"


def _norm(s):
    return " ".join((s or "").split())


def _load(path: Path, key):
    if not path.is_file():
        return {"schema_version": "2.0", key: []}
    return vs.load_yaml_strict(path) or {"schema_version": "2.0", key: []}


def _dump(path: Path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))


def _fresh_id(base, taken):
    """A new id derived from `base` that is not already in `taken` (append-only collision suffix)."""
    if base not in taken:
        return base
    n = 2
    while f"{base}-v{n}" in taken:
        n += 1
    return f"{base}-v{n}"


def _recompute_claim_status(claim, all_ceas, sas_records):
    """Set support_status + dispute_status from the FULL cea set (both fields are excluded from
    claim_content_hash, so this is order-safe vs the per-cea binding). The §6.1 A-C leg is computed
    from the staged sas so stored == what records_check recomputes."""
    ac = v_sup.ac_rated_sources(sas_records)
    claim["support_status"] = v_sup.compute_support(
        v_sup.active_supports_by_claim(all_ceas).get(claim["id"], []), ac)[0]
    claim["dispute_status"] = v_con.compute_dispute(
        v_sup.active_checked_by_claim(all_ceas).get(claim["id"], []))


def _compose_check(docs, as_of):
    """Stage the full factbase docs to a tmp tree and run the records gates. Returns (code, lines)."""
    with tempfile.TemporaryDirectory() as dd:
        st = Path(dd)
        for f in FB_FILES:
            _dump(st / "factbase" / f, docs[f])
        for jl in ("prediction_events.jsonl", "baseline_events.jsonl"):
            (st / "factbase" / jl).write_text("")
        return verify.records_check(st, as_of)


def _persist(root: Path, docs):
    for f in FB_FILES:
        _dump(root / "factbase" / f, docs[f])


def build_records(spec: dict, as_of: str):
    """Return (sources, evidence_list, claim, ceas) from a seed spec. A claim carries ONE assessment
    (spec.source/artifact/assessment — back-compat) OR MANY (spec.assessments[], each with its own
    source/artifact/stance/quote — a CONTESTED claim). support_status/dispute_status are placeholders
    here (both excluded from claim_content_hash) and COMPUTED by the caller from the full cea set, so
    the support + conflict gates pass by construction. Raises ValueError on a non-verbatim quote."""
    c = spec["claim"]
    clm_slug = _slug(c["text"])
    clm_id = c.get("id") or f"clm-{clm_slug}"
    if spec.get("assessments"):
        units = spec["assessments"]
    else:  # single-assessment back-compat: source + artifact live at the top level
        u0 = dict(spec["assessment"])
        u0["source"], u0["artifact"] = spec["source"], spec["artifact"]
        units = [u0]
    claim = {"id": clm_id, "text": c["text"], "epistemic_type": c.get("epistemic_type", "FACT"),
             "support_status": "UNVERIFIED", "dispute_status": "UNKNOWN",  # placeholders; caller computes
             "freshness_status": "CURRENT", "lifecycle": "REVIEWED",
             "stability": c.get("stability", "DURABLE"), "topics": c["topics"],
             "high_impact": c.get("high_impact", False), "created_at": as_of, "supersedes": None,
             "temporal": {"kind": "TIMELESS", "valid_as_of": None, "valid_from": None,
                          "valid_to": None, "event_time": None},
             "review_by": c.get("review_by"), "expires_at": None, "freshness_profile": None}
    if c.get("impact_category"):
        claim["impact_category"] = c["impact_category"]
    cch = vs.claim_content_hash(claim)  # excludes support/dispute_status → stable vs the caller's recompute
    sources, evidence, ceas, seen = [], [], [], set()
    for u in units:
        s, a = u["source"], u["artifact"]
        text = a.get("text") or (Path(a["text_file"]).read_text(encoding="utf-8") if a.get("text_file") else None)
        if not text:
            raise ValueError("each assessment's artifact needs `text` or `text_file`")
        quote = u["quote"]
        if _norm(quote) not in _norm(text):
            raise ValueError(f"quote is not a verbatim substring of its artifact text: {quote[:60]!r}")
        src_id = s["id"]
        src_slug = src_id[4:] if src_id.startswith("src-") else src_id
        key, n = f"{clm_slug}-{src_slug}", 2
        while key in seen:
            key, n = f"{clm_slug}-{src_slug}-{n}", n + 1
        seen.add(key)
        content_hash = "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
        if {"title", "source_type"} <= set(s):  # create the identity if a full record is given
            sources.append({"id": src_id, "title": s["title"], "source_type": s["source_type"],
                            "aliases": s.get("aliases", []), "canonical_home": s.get("canonical_home"),
                            "active_from": None, "active_to": None})
        evd_id = a.get("id") or f"evd-{key}"
        evidence.append({"id": evd_id, "source_id": src_id, "artifact_type": a.get("artifact_type", "ARTICLE"),
                         "title": a.get("title", c["text"][:80]), "canonical_locator": a["url"],
                         "content_hash": content_hash, "published_at": a.get("published_at", a["retrieved_at"]),
                         "retrieved_at": a["retrieved_at"]})
        rih = "sha256:" + hashlib.sha256(("REL|" + _norm(quote)).encode("utf-8")).hexdigest()
        ceas.append({"id": u.get("id") or f"cea-{key}", "claim_id": clm_id, "artifact_id": evd_id,
                     "support_locator": {"kind": "PAGE_AND_QUOTE", "page": 1, "quote": quote},
                     "support_summary": u.get("summary", quote[:120]), "stance": u.get("stance", "SUPPORTS"),
                     "information_credibility": u["information_credibility"],
                     "temporal_scope": {"kind": "TIMELESS", "start": None, "end": None},
                     "origin_chain": [{"source_id": src_id, "artifact_id": evd_id}],
                     "independence_group": f"ind-{key}",
                     "semantic_review": {"status": "CHECKED", "reviewer": u.get("reviewer", "model:unknown"),
                                         "reviewed_at": as_of, "claim_content_hash": cch,
                                         "artifact_hash": content_hash, "relationship_input_hash": rih},
                     "supersedes": None})
    return sources, evidence, claim, ceas


def cmd_add(args):
    spec = vs.load_yaml_strict(Path(args.spec))
    try:
        sources, evidence, claim, ceas = build_records(spec, args.as_of)
    except (ValueError, KeyError) as e:
        print(f"[fact add] spec error: {e}", file=sys.stderr)
        return 2
    root = Path(args.root)
    docs = {f: _load(root / "factbase" / f, k) for f, k in FB_FILES.items()}
    for src in sources:
        if not any(s.get("id") == src["id"] for s in docs["sources.yaml"]["sources"]):
            docs["sources.yaml"]["sources"].append(src)
    docs["evidence.yaml"]["evidence"].extend(evidence)
    docs["claim_evidence.yaml"]["claim_evidence_assessments"].extend(ceas)
    docs["baseline/claims.yaml"]["claims"].append(claim)
    # compute-then-store: derive support_status + dispute_status from the FULL cea set so the support
    # and conflict gates pass by construction (both fields are excluded from claim_content_hash).
    all_ceas = docs["claim_evidence.yaml"]["claim_evidence_assessments"]
    _recompute_claim_status(claim, all_ceas, docs["source_assessments.yaml"]["source_assessments"])
    # stage onto a tmp copy and run the records gates BEFORE persisting (fail-closed)
    code, lines = _compose_check(docs, args.as_of)
    if code != 0:
        print("\n".join(lines), file=sys.stderr)
        print(f"\n[fact add] NOT persisted — the fact does not compose cleanly (exit {code}). "
              f"Fix the spec/source and retry.", file=sys.stderr)
        return code
    _persist(root, docs)  # persist only on a clean compose
    n = len(ceas)
    print(f"[fact add] OK — claim {claim['id']!r} ({claim['support_status']}/{claim['dispute_status']}, "
          f"{n} assessment{'' if n == 1 else 's'}) composes clean, persisted under {root}/factbase.")
    return 0


def cmd_query(args):
    root = Path(args.root)
    claims = []
    for f in ("baseline/claims.yaml", "live/claims.yaml"):
        claims += _load(root / "factbase" / f, "claims").get("claims", [])
    ceas = _load(root / "factbase" / "claim_evidence.yaml", "claim_evidence_assessments").get(
        "claim_evidence_assessments", [])
    evd = {e["id"]: e for e in _load(root / "factbase" / "evidence.yaml", "evidence").get("evidence", [])}
    srcs = {s["id"]: s for s in _load(root / "factbase" / "sources.yaml", "sources").get("sources", [])}

    def match(c):
        return ((not args.id or c.get("id") == args.id)
                and (not args.topic or args.topic in (c.get("topics") or []))
                and (not args.text or args.text.lower() in (c.get("text") or "").lower()))

    hits = [c for c in claims if match(c)]
    if not hits:
        print("(no matching facts)")
        return 0
    for c in hits:
        print(f"\n● {c['id']}  [{c.get('support_status')}/{c.get('dispute_status')}/"
              f"{c.get('freshness_status')}]  topics={c.get('topics')}")
        print(f"  {c.get('text')}")
        for a in ceas:
            if a.get("claim_id") == c["id"]:
                e = evd.get(a.get("artifact_id"), {})
                s = srcs.get(e.get("source_id"), {})
                q = (a.get("support_locator") or {}).get("quote", "")
                print(f"    <- {s.get('title', '?')} (credibility {a.get('information_credibility')}): "
                      f"\"{q[:140]}\"")
                print(f"       {e.get('canonical_locator', '')}")
    print(f"\n{len(hits)} fact(s).")
    return 0


def cmd_source(args):
    spec = vs.load_yaml_strict(Path(args.spec))
    s = spec.get("source") or {}
    src_id = s.get("id")
    if not src_id:
        print("[fact source] spec.source.id is required", file=sys.stderr)
        return 2
    root = Path(args.root)
    srcs = _load(root / "factbase" / "sources.yaml", "sources")
    sas = _load(root / "factbase" / "source_assessments.yaml", "source_assessments")
    # ensure the identity (create if a full record is given and it's new)
    if {"title", "source_type"} <= set(s) and not any(x.get("id") == src_id for x in srcs["sources"]):
        srcs["sources"].append({"id": src_id, "title": s["title"], "source_type": s["source_type"],
                                "aliases": s.get("aliases", []), "canonical_home": s.get("canonical_home"),
                                "active_from": None, "active_to": None})
    src_slug = src_id[4:] if src_id.startswith("src-") else src_id
    seen = {a.get("id") for a in sas["source_assessments"]}
    added = []
    for r in spec.get("ratings") or []:
        sid = base = f"sas-{src_slug}-{_slug(r['scope'], 4)}"
        n = 2
        while sid in seen:
            sid, n = f"{base}-{n}", n + 1
        seen.add(sid)
        rec = {"id": sid, "source_id": src_id, "scope": r["scope"], "reliability": r["reliability"],
               "sample_definition": r["sample_definition"], "sample_size": int(r["sample_size"]),
               "rationale": r["rationale"],
               "assessed_by": r.get("assessed_by", "ai:claude-opus-4-8-draft + owner-review-pending"),
               "assessed_at": args.as_of, "supersedes": None}
        sas["source_assessments"].append(rec)
        added.append(rec)
    # validate the SOURCE layers only (ratings are independent of the claim DAG) — fail-closed
    with tempfile.TemporaryDirectory() as dd:
        fb = Path(dd) / "factbase"
        fb.mkdir(parents=True)
        _dump(fb / "sources.yaml", srcs)
        _dump(fb / "source_assessments.yaml", sas)
        sc, sf = v_src.validate_sources_file(fb / "sources.yaml")
        gc, gf = v_gov.validate_governance_file(fb / "source_assessments.yaml")
    code, findings = max(sc, gc), sf + gf
    if code != 0:
        print("\n".join(findings), file=sys.stderr)
        print(f"\n[fact source] NOT persisted — source/rating does not validate (exit {code}).", file=sys.stderr)
        return code
    _dump(root / "factbase" / "sources.yaml", srcs)
    _dump(root / "factbase" / "source_assessments.yaml", sas)
    summ = ", ".join(f"{a['scope'][:24]}={a['reliability']}" for a in added)
    print(f"[fact source] OK — {src_id!r}: {len(added)} scoped rating(s) [{summ}] persisted under "
          f"{root}/factbase")
    return 0


CEA_OPTS = ("credibility", "stance", "summary", "retract")
CLAIM_OPTS = ("text", "topics", "impact_category", "high_impact", "stability", "review_by")


def _supersede_cea(args, docs, root, all_ceas, claims_all, sas, old):
    """Append a superseding cea in the SAME (claim_id, artifact_id) partition (re-rate / fix stance /
    fix summary / retract), then recompute-and-restore the parent claim's status (trap T1)."""
    bad = [o for o in CLAIM_OPTS if getattr(args, o)]
    if bad:
        print(f"[fact supersede] {bad} are claim options; target {old['id']!r} is an assessment "
              f"(use --credibility/--stance/--summary/--retract/--reviewer)", file=sys.stderr)
        return 2
    if not any([args.credibility, args.stance, args.summary, args.reviewer, args.retract]):
        print("[fact supersede] no change specified for the assessment", file=sys.stderr)
        return 2
    parent = next((c for c in claims_all if c.get("id") == old.get("claim_id")), None)
    if parent is None:
        print(f"[fact supersede] parent claim {old.get('claim_id')!r} not found", file=sys.stderr)
        return 2
    new = copy.deepcopy(old)
    new["id"] = _fresh_id(old["id"], {a["id"] for a in all_ceas})
    new["supersedes"] = old["id"]
    if args.credibility is not None:
        new["information_credibility"] = args.credibility
    if args.stance:
        new["stance"] = args.stance
    if args.summary:
        new["support_summary"] = args.summary
    sr = new["semantic_review"]
    sr["status"] = "REJECTED" if args.retract else "CHECKED"
    sr["reviewed_at"] = args.as_of
    if args.reviewer:
        sr["reviewer"] = args.reviewer
    sr["claim_content_hash"] = vs.claim_content_hash(parent)  # claim unchanged → binds the current content
    all_ceas.append(new)
    _recompute_claim_status(parent, all_ceas, sas)  # the active set changed → restore the stored label
    code, lines = _compose_check(docs, args.as_of)
    if code != 0:
        print("\n".join(lines), file=sys.stderr)
        print(f"\n[fact supersede] NOT persisted — does not compose cleanly (exit {code}).", file=sys.stderr)
        return code
    _persist(root, docs)
    verb = "retracted (REJECTED)" if args.retract else "superseded"
    print(f"[fact supersede] OK — assessment {old['id']!r} {verb} by {new['id']!r}; claim "
          f"{parent['id']!r} now {parent['support_status']}/{parent['dispute_status']}. persisted under "
          f"{root}/factbase.")
    return 0


def _supersede_claim(args, docs, root, all_ceas, claims_all, sas, old):
    """Correct a claim's content (text/topics/category/...): a NEW claim (new id, supersedes old) +
    the old claim's active CHECKED ceas CLONED as fresh leaves under the new claim (a cea cannot cross
    claim_id partitions — trap T2), and the old claim frozen to SUPERSEDED (hash-safe, drops it from
    the freshness recompute)."""
    bad = [o for o in CEA_OPTS if getattr(args, o)]
    if bad:
        print(f"[fact supersede] {bad} are assessment options; target {old['id']!r} is a claim "
              f"(use --text/--topics/--impact-category/--high-impact/--stability/--review-by)", file=sys.stderr)
        return 2
    if not any(getattr(args, o) for o in CLAIM_OPTS):
        print("[fact supersede] no change specified for the claim", file=sys.stderr)
        return 2
    new = copy.deepcopy(old)
    if args.text:
        new["text"] = args.text
    if args.topics:
        new["topics"] = [t.strip() for t in args.topics.split(",") if t.strip()]
    if args.impact_category:
        new["impact_category"] = args.impact_category
    if args.high_impact:
        new["high_impact"] = (args.high_impact == "true")
    if args.stability:
        new["stability"] = args.stability
    if args.review_by:
        new["review_by"] = args.review_by
    new["id"] = _fresh_id(f"clm-{_slug(new['text'])}", {c["id"] for c in claims_all})
    new["supersedes"] = old["id"]
    new["created_at"] = args.as_of
    new["lifecycle"] = "REVIEWED"
    new["support_status"], new["dispute_status"] = "UNVERIFIED", "UNKNOWN"  # placeholders; recomputed below
    cch = vs.claim_content_hash(new)
    active = v_sup.active_checked_by_claim(all_ceas).get(old["id"], [])  # carry forward both stances
    taken = {a["id"] for a in all_ceas}
    for a in active:
        clone = copy.deepcopy(a)
        clone["id"] = _fresh_id(a["id"], taken)
        taken.add(clone["id"])
        clone["claim_id"] = new["id"]
        clone["supersedes"] = None  # a fresh leaf in the new (claim_id, artifact_id) partition
        clone["semantic_review"]["claim_content_hash"] = cch
        clone["semantic_review"]["reviewed_at"] = args.as_of
        if args.reviewer:
            clone["semantic_review"]["reviewer"] = args.reviewer
        all_ceas.append(clone)
    old["lifecycle"] = "SUPERSEDED"  # freeze in place (excluded field → hash-safe); old ceas untouched
    tgt_file = "baseline/claims.yaml" if any(
        c.get("id") == old["id"] for c in docs["baseline/claims.yaml"]["claims"]) else "live/claims.yaml"
    docs[tgt_file]["claims"].append(new)
    _recompute_claim_status(new, all_ceas, sas)
    code, lines = _compose_check(docs, args.as_of)
    if code != 0:
        print("\n".join(lines), file=sys.stderr)
        print(f"\n[fact supersede] NOT persisted — does not compose cleanly (exit {code}). "
              f"(a content edit that raises high_impact needs --high-impact/--impact-category; a stale "
              f"review_by needs --review-by.)", file=sys.stderr)
        return code
    _persist(root, docs)
    print(f"[fact supersede] OK — claim {old['id']!r} (now SUPERSEDED) replaced by {new['id']!r} "
          f"({new['support_status']}/{new['dispute_status']}), {len(active)} assessment(s) carried "
          f"forward. persisted under {root}/factbase.")
    return 0


def cmd_supersede(args):
    root = Path(args.root)
    docs = {f: _load(root / "factbase" / f, k) for f, k in FB_FILES.items()}
    all_ceas = docs["claim_evidence.yaml"]["claim_evidence_assessments"]
    claims_all = docs["baseline/claims.yaml"]["claims"] + docs["live/claims.yaml"]["claims"]
    sas = docs["source_assessments.yaml"]["source_assessments"]
    cea = next((a for a in all_ceas if a.get("id") == args.target), None)
    if cea is not None:
        return _supersede_cea(args, docs, root, all_ceas, claims_all, sas, cea)
    claim = next((c for c in claims_all if c.get("id") == args.target), None)
    if claim is not None:
        return _supersede_claim(args, docs, root, all_ceas, claims_all, sas, claim)
    print(f"[fact supersede] target {args.target!r} not found among assessment or claim ids", file=sys.stderr)
    return 2


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="lean fact-repository tool (add / query / source / supersede)")
    p.add_argument("--root", default=".", help="repo/corpus root containing factbase/ (default: .)")
    sub = p.add_subparsers(dest="cmd", required=True)
    pa = sub.add_parser("add", help="add a checked fact from a seed spec (fail-closed)")
    pa.add_argument("spec", help="seed-spec YAML (source/artifact/claim/assessment)")
    pa.add_argument("--as-of", required=True, help="ISO timestamp for created_at/reviewed_at")
    pa.set_defaults(fn=cmd_add)
    pq = sub.add_parser("query", help="list/search the baseline facts")
    pq.add_argument("--topic")
    pq.add_argument("--text")
    pq.add_argument("--id")
    pq.set_defaults(fn=cmd_query)
    ps = sub.add_parser("source", help="ensure a source identity + append scoped reliability ratings")
    ps.add_argument("spec", help="seed-spec YAML (source + ratings[])")
    ps.add_argument("--as-of", required=True, help="ISO timestamp for assessed_at")
    ps.set_defaults(fn=cmd_source)
    pu = sub.add_parser("supersede", help="append-only correction of a claim or an assessment (fail-closed)")
    pu.add_argument("--target", required=True, help="cea-... (assessment) or clm-... (claim) id to correct")
    pu.add_argument("--as-of", required=True, help="ISO timestamp for the correction (reviewed_at/created_at)")
    pu.add_argument("--reviewer", help="who is making the correction, e.g. human:tim (default: keep prior)")
    # assessment (cea) corrections
    pu.add_argument("--credibility", type=int, choices=range(1, 7), metavar="{1-6}",
                    help="(assessment) re-rate information_credibility")
    pu.add_argument("--stance", choices=sorted(sd.STANCE), help="(assessment) fix the stance")
    pu.add_argument("--summary", help="(assessment) fix the support summary")
    pu.add_argument("--retract", action="store_true",
                    help="(assessment) deactivate it (REJECTED) — drops it from the active support/conflict set")
    # claim corrections
    pu.add_argument("--text", help="(claim) corrected claim text")
    pu.add_argument("--topics", help="(claim) comma-separated topics")
    pu.add_argument("--impact-category", dest="impact_category", choices=sorted(sd.IMPACT_CATEGORY),
                    help="(claim) impact category")
    pu.add_argument("--high-impact", dest="high_impact", choices=["true", "false"], help="(claim) high_impact flag")
    pu.add_argument("--stability", choices=sorted(sd.STABILITY), help="(claim) stability class")
    pu.add_argument("--review-by", dest="review_by", help="(claim) next-review date (>= --as-of)")
    pu.set_defaults(fn=cmd_supersede)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

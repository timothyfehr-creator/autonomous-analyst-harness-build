#!/usr/bin/env python3
"""Phase 4 (lean MVP) — the fact-repository tool.

  fact.py add <spec.yaml> --as-of <ts> [--root DIR]
      Build a CHECKED fact from a retrieved artifact + an EXACT quote, validate it through the
      records integrity gates, and persist ONLY if it composes clean (fail-closed). A fact traces
      to a real retrieved artifact and a verbatim quote — never model memory.

  fact.py query [--root DIR] [--topic T] [--text S] [--id clm-...]
      List the baseline facts and the source + quote backing each.

The corpus lives under <root>/factbase (default: the repo). Keep a REAL corpus in a gitignored
location (e.g. `--root private/corpus`) so the public repo's factbase stays empty.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_schema as vs  # noqa: E402
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


def build_records(spec: dict, as_of: str):
    """Return (source_or_None, evidence, claim, cea) from a seed spec. Raises ValueError on a
    dishonest spec — the quote must be a verbatim substring of the retrieved artifact text."""
    s, a, c, asmt = spec["source"], spec["artifact"], spec["claim"], spec["assessment"]
    text = a.get("text") or (Path(a["text_file"]).read_text(encoding="utf-8") if a.get("text_file") else None)
    if not text:
        raise ValueError("artifact needs `text` or `text_file` (the exact retrieved content)")
    quote = asmt["quote"]
    if _norm(quote) not in _norm(text):
        raise ValueError("assessment.quote is not a verbatim substring of the artifact text — a "
                         "locator must point to real retrieved text, not a paraphrase or memory")
    slug = _slug(c["text"])
    content_hash = "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()
    src_id = s["id"]
    source = None
    if {"title", "source_type"} <= set(s):  # a full source record to create if it's new
        source = {"id": src_id, "title": s["title"], "source_type": s["source_type"],
                  "aliases": s.get("aliases", []), "canonical_home": s.get("canonical_home"),
                  "active_from": None, "active_to": None}
    evd_id = a.get("id") or f"evd-{slug}"
    evidence = {"id": evd_id, "source_id": src_id, "artifact_type": a.get("artifact_type", "ARTICLE"),
                "title": a.get("title", c["text"][:80]), "canonical_locator": a["url"],
                "content_hash": content_hash, "published_at": a.get("published_at", a["retrieved_at"]),
                "retrieved_at": a["retrieved_at"]}
    clm_id = c.get("id") or f"clm-{slug}"
    claim = {"id": clm_id, "text": c["text"], "epistemic_type": c.get("epistemic_type", "FACT"),
             "support_status": "SUPPORTED", "dispute_status": "UNCONTESTED",
             "freshness_status": "CURRENT", "lifecycle": "REVIEWED",
             "stability": c.get("stability", "DURABLE"), "topics": c["topics"],
             "high_impact": c.get("high_impact", False), "created_at": as_of, "supersedes": None,
             "temporal": {"kind": "TIMELESS", "valid_as_of": None, "valid_from": None,
                          "valid_to": None, "event_time": None},
             "review_by": c.get("review_by"), "expires_at": None, "freshness_profile": None}
    if c.get("impact_category"):
        claim["impact_category"] = c["impact_category"]
    rih = "sha256:" + hashlib.sha256(("REL|" + _norm(quote)).encode("utf-8")).hexdigest()
    cea = {"id": asmt.get("id") or f"cea-{slug}", "claim_id": clm_id, "artifact_id": evd_id,
           "support_locator": {"kind": "PAGE_AND_QUOTE", "page": 1, "quote": quote},
           "support_summary": asmt.get("summary", quote[:120]), "stance": asmt.get("stance", "SUPPORTS"),
           "information_credibility": asmt["information_credibility"],
           "temporal_scope": {"kind": "TIMELESS", "start": None, "end": None},
           "origin_chain": [{"source_id": src_id, "artifact_id": evd_id}],
           "independence_group": f"ind-{slug}",
           "semantic_review": {"status": "CHECKED", "reviewer": asmt.get("reviewer", "model:unknown"),
                               "reviewed_at": as_of, "claim_content_hash": vs.claim_content_hash(claim),
                               "artifact_hash": content_hash, "relationship_input_hash": rih},
           "supersedes": None}
    return source, evidence, claim, cea


def cmd_add(args):
    spec = vs.load_yaml_strict(Path(args.spec))
    try:
        source, evidence, claim, cea = build_records(spec, args.as_of)
    except (ValueError, KeyError) as e:
        print(f"[fact add] spec error: {e}", file=sys.stderr)
        return 2
    root = Path(args.root)
    docs = {f: _load(root / "factbase" / f, k) for f, k in FB_FILES.items()}
    if source and not any(s.get("id") == source["id"] for s in docs["sources.yaml"]["sources"]):
        docs["sources.yaml"]["sources"].append(source)
    docs["evidence.yaml"]["evidence"].append(evidence)
    docs["claim_evidence.yaml"]["claim_evidence_assessments"].append(cea)
    docs["baseline/claims.yaml"]["claims"].append(claim)
    # stage onto a tmp copy and run the records gates BEFORE persisting (fail-closed)
    with tempfile.TemporaryDirectory() as dd:
        st = Path(dd)
        for f in FB_FILES:
            _dump(st / "factbase" / f, docs[f])
        for jl in ("prediction_events.jsonl", "baseline_events.jsonl"):
            (st / "factbase" / jl).write_text("")
        code, lines = verify.records_check(st, args.as_of)
    if code != 0:
        print("\n".join(lines), file=sys.stderr)
        print(f"\n[fact add] NOT persisted — the fact does not compose cleanly (exit {code}). "
              f"Fix the spec/source and retry.", file=sys.stderr)
        return code
    for f in FB_FILES:  # persist only on a clean compose
        _dump(root / "factbase" / f, docs[f])
    print(f"[fact add] OK — claim {claim['id']!r} (SUPPORTED) composes clean and is persisted under "
          f"{root}/factbase. Backed by {evidence['canonical_locator']}")
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


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="lean fact-repository tool (add / query)")
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
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

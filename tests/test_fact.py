"""Phase 4 (lean MVP) — fact.py add/query. add builds a CHECKED fact from a retrieved artifact +
an exact quote, validates it through the records gates, and persists ONLY if clean (fail-closed).
"""
import pathlib
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import fact  # noqa: E402
import validate_schema as vs  # noqa: E402

ASOF = "2026-06-28T00:00:00Z"


def _spec(claim_text, quote, topics=("geography", "infrastructure"), artifact_text=None):
    return {
        "source": {"id": "src-test-ref", "title": "Test Reference", "source_type": "REFERENCE",
                   "canonical_home": "https://example.invalid"},
        "artifact": {"artifact_type": "ARTICLE", "url": "https://example.invalid/x",
                     "retrieved_at": ASOF, "text": artifact_text or quote + "."},
        "claim": {"text": claim_text, "topics": list(topics), "stability": "DURABLE",
                  "review_by": "2027-06-28"},
        "assessment": {"quote": quote, "summary": "lead sentence", "information_credibility": 2,
                       "reviewer": "model:test"},
    }


def _write(tmp_path, spec):
    p = tmp_path / "spec.yaml"
    p.write_text(yaml.safe_dump(spec, sort_keys=False))
    return p


def _baseline_claims(root):
    f = root / "factbase" / "baseline" / "claims.yaml"
    return (vs.load_yaml_strict(f) or {}).get("claims", []) if f.is_file() else []


def test_add_persists_and_query_finds(tmp_path, capsys):
    spec = _spec("The Example Bridge spans the Example River, connecting town A and town B.",
                 "The Example Bridge spans the Example River connecting town A and town B")
    code = fact.main(["--root", str(tmp_path), "add", str(_write(tmp_path, spec)), "--as-of", ASOF])
    assert code == 0, capsys.readouterr()
    claims = _baseline_claims(tmp_path)
    assert len(claims) == 1 and claims[0]["support_status"] == "SUPPORTED"
    # query finds it + shows the backing source/quote
    assert fact.main(["--root", str(tmp_path), "query", "--topic", "geography"]) == 0
    out = capsys.readouterr().out
    assert "Example Bridge" in out and "Test Reference" in out


def test_add_rejects_quote_not_in_artifact(tmp_path):
    # the honesty guard: a locator must point to REAL retrieved text, not a paraphrase/memory
    spec = _spec("The Example Bridge is famous.", "The Example Bridge is made of solid gold",
                 artifact_text="The Example Bridge spans the Example River.")
    code = fact.main(["--root", str(tmp_path), "add", str(_write(tmp_path, spec)), "--as-of", ASOF])
    assert code == 2  # spec error, nothing persisted
    assert _baseline_claims(tmp_path) == []


def test_add_fail_closed_on_uncomposable_fact(tmp_path):
    # a high-impact claim stored high_impact:false (the records high_impact gate raises it) must NOT
    # persist — add stages + validates through the gates and only writes on a clean compose.
    spec = _spec("Russian strikes killed five hundred civilians at the crossing.",
                 "Russian strikes killed five hundred civilians at the crossing",
                 topics=("casualties",))
    code = fact.main(["--root", str(tmp_path), "add", str(_write(tmp_path, spec)), "--as-of", ASOF])
    assert code == 1  # composes dirty (high_impact recompute) → fail closed
    assert _baseline_claims(tmp_path) == []  # not persisted


def test_build_records_binds_hashes():
    spec = _spec("The Example Bridge spans the Example River, connecting A and B.",
                 "The Example Bridge spans the Example River connecting A and B")
    _srcs, evd, clm, ceas = fact.build_records(spec, ASOF)  # now returns LISTS (multi-assessment)
    cea, ev = ceas[0], evd[0]
    # the assessment binds the artifact + the CURRENT claim content (what validate_claim_evidence checks)
    assert cea["semantic_review"]["artifact_hash"] == ev["content_hash"]
    assert cea["semantic_review"]["claim_content_hash"] == vs.claim_content_hash(clm)
    # the reviewed artifact is bound into its own origin_chain (FR-4 B1)
    assert cea["origin_chain"][0]["artifact_id"] == ev["id"] == cea["artifact_id"]


# ---- fact.py source — scoped reliability ratings ----
def _src_spec(scope="own announcements", reliability="C", rationale="track record fair"):
    return {"source": {"id": "src-test-mil", "title": "Test Military", "source_type": "MILITARY"},
            "ratings": [{"scope": scope, "reliability": reliability,
                         "sample_definition": "qualitative review of ~10 statements vs later outcomes",
                         "sample_size": 10, "rationale": rationale, "assessed_by": "ai:test"}]}


def _sas(root):
    f = root / "factbase" / "source_assessments.yaml"
    return (vs.load_yaml_strict(f) or {}).get("source_assessments", []) if f.is_file() else []


def test_source_rate_persists_and_creates_identity(tmp_path):
    code = fact.main(["--root", str(tmp_path), "source", str(_write(tmp_path, _src_spec())), "--as-of", ASOF])
    assert code == 0
    sas = _sas(tmp_path)
    assert len(sas) == 1 and sas[0]["reliability"] == "C" and sas[0]["source_id"] == "src-test-mil"
    assert sas[0]["supersedes"] is None and sas[0]["assessed_at"] == ASOF
    srcs = (vs.load_yaml_strict(tmp_path / "factbase" / "sources.yaml") or {}).get("sources", [])
    assert any(s["id"] == "src-test-mil" for s in srcs)  # identity created


def test_source_rate_fail_closed_on_empty_rationale(tmp_path):
    # the governance gate forces non-empty provenance — a blank rationale must NOT persist
    code = fact.main(["--root", str(tmp_path), "source",
                      str(_write(tmp_path, _src_spec(rationale="   "))), "--as-of", ASOF])
    assert code == 1
    assert _sas(tmp_path) == []  # not persisted


def test_source_multiple_scoped_ratings(tmp_path):
    # one belligerent source, two scopes (reliable for its own announcements, unreliable for enemy losses)
    spec = _src_spec()
    spec["ratings"].append({"scope": "adversary casualty claims", "reliability": "E",
                            "sample_definition": "qualitative review", "sample_size": 8,
                            "rationale": "systematic over-claim", "assessed_by": "ai:test"})
    assert fact.main(["--root", str(tmp_path), "source", str(_write(tmp_path, spec)), "--as-of", ASOF]) == 0
    sas = _sas(tmp_path)
    assert {s["reliability"] for s in sas} == {"C", "E"} and len({s["id"] for s in sas}) == 2


# ---- WP-1: multi-assessment CONTESTED facts ----
def _contested_spec(high_impact=True, impact_category="CASUALTIES"):
    claim = {"text": "Total Russian military deaths in Ukraine exceed one million as of mid-2026.",
             "topics": ["casualties"], "stability": "DURABLE", "review_by": "2027-06-29",
             "high_impact": high_impact}
    if impact_category:
        claim["impact_category"] = impact_category
    return {
        "claim": claim,
        "assessments": [
            {"source": {"id": "src-claimant-mil", "title": "Claimant Military", "source_type": "MILITARY"},
             "artifact": {"url": "https://example.invalid/a", "retrieved_at": ASOF, "artifact_type": "ARTICLE",
                          "text": "The claimant reports that total enemy military deaths exceed one million."},
             "quote": "total enemy military deaths exceed one million", "stance": "SUPPORTS",
             "information_credibility": 5, "reviewer": "ai:test", "summary": "belligerent claim (low cred)"},
            {"source": {"id": "src-independent-count", "title": "Independent Count", "source_type": "RESEARCH_INSTITUTE"},
             "artifact": {"url": "https://example.invalid/b", "retrieved_at": ASOF, "artifact_type": "ARTICLE",
                          "text": "Independently confirmed deaths number in the low hundreds of thousands, far below one million."},
             "quote": "Independently confirmed deaths number in the low hundreds of thousands, far below one million",
             "stance": "REFUTES", "information_credibility": 2, "reviewer": "ai:test", "summary": "independent estimate"},
        ],
    }


def test_contested_claim_composes_supported_and_contested(tmp_path):
    code = fact.main(["--root", str(tmp_path), "add", str(_write(tmp_path, _contested_spec())), "--as-of", ASOF])
    assert code == 0
    claims = _baseline_claims(tmp_path)
    assert len(claims) == 1
    assert claims[0]["support_status"] == "SUPPORTED" and claims[0]["dispute_status"] == "CONTESTED"
    ceas = (vs.load_yaml_strict(tmp_path / "factbase" / "claim_evidence.yaml") or {}).get("claim_evidence_assessments", [])
    assert len(ceas) == 2 and {a["stance"] for a in ceas} == {"SUPPORTS", "REFUTES"}


def test_contested_casualty_without_category_fails_closed(tmp_path):
    # a contested casualty claim that doesn't carry high_impact:true is raised by the records gate
    spec = _contested_spec(high_impact=False, impact_category=None)
    code = fact.main(["--root", str(tmp_path), "add", str(_write(tmp_path, spec)), "--as-of", ASOF])
    assert code == 1 and _baseline_claims(tmp_path) == []


def test_two_assessments_same_artifact_fails(tmp_path):
    # two assessments pinned to the SAME artifact_id → one-active-leaf fork → fail closed
    spec = _contested_spec()
    spec["assessments"][0]["artifact"]["id"] = spec["assessments"][1]["artifact"]["id"] = "evd-collide"
    code = fact.main(["--root", str(tmp_path), "add", str(_write(tmp_path, spec)), "--as-of", ASOF])
    assert code != 0 and _baseline_claims(tmp_path) == []

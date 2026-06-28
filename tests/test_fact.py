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
    _src, evd, clm, cea = fact.build_records(spec, ASOF)
    # the assessment binds the artifact + the CURRENT claim content (what validate_claim_evidence checks)
    assert cea["semantic_review"]["artifact_hash"] == evd["content_hash"]
    assert cea["semantic_review"]["claim_content_hash"] == vs.claim_content_hash(clm)
    # the reviewed artifact is bound into its own origin_chain (FR-4 B1)
    assert cea["origin_chain"][0]["artifact_id"] == evd["id"] == cea["artifact_id"]

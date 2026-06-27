"""WP3.2 — validate_output: output-text ↔ manifest binding. Output-hash binding, marker resolution
(both directions = A7 structural half), status preservation (§7), and the unmarked-assertion
heuristic (A7 semantic half: WARN in draft, BLOCK in answer with a hash-pinned escape).
"""
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_output as vo  # noqa: E402
import validate_schema as vs  # noqa: E402

SK = ROOT / "tests" / "fixtures" / "skeleton"
CLAIM = vs.load_yaml_strict(SK / "skeleton_claims.yaml")["claims"][0]
CID = CLAIM["id"]


def _live(claim=CLAIM):
    return types.SimpleNamespace(claims={claim["id"]: claim})


def _ana(tmp_path, prose, markers, exemptions=None):
    """Build an analysis dict whose output_hash binds `prose`, plus the written output file."""
    (tmp_path / "outputs").mkdir(exist_ok=True)
    f = tmp_path / "outputs" / "ana-x.md"
    f.write_text(prose, encoding="utf-8")
    ana = {"output_path": "outputs/ana-x.md", "output_hash": vs.file_content_hash(f),
           "claim_markers": markers, "narrative_exemptions": exemptions or []}
    return ana


def test_clean_output_binds_and_resolves(tmp_path):
    ana = _ana(tmp_path, "The Skeleton Crossing supports road transport. [[c1]]\n",
               {"c1": {"claim_id": CID, "claim_hash": "x"}})
    code, findings = vo.validate_output(ana, _live(), tmp_path)
    assert code == 0, findings
    assert not findings


def test_missing_output_file_is_cannot_run(tmp_path):
    ana = {"output_path": "outputs/nope.md", "output_hash": "sha256:" + "0" * 64,
           "claim_markers": {}, "narrative_exemptions": []}
    code, findings = vo.validate_output(ana, _live(), tmp_path)
    assert code == 2 and "not found" in "\n".join(findings)


def test_edited_text_breaks_output_hash(tmp_path):
    ana = _ana(tmp_path, "Original answer. [[c1]]\n", {"c1": {"claim_id": CID, "claim_hash": "x"}})
    (tmp_path / "outputs" / "ana-x.md").write_text("Tampered answer. [[c1]]\n")  # post-review edit
    code, findings = vo.validate_output(ana, _live(), tmp_path)
    assert code == 1 and any("output_hash does not bind" in f for f in findings), findings


def test_unresolved_prose_marker(tmp_path):
    ana = _ana(tmp_path, "Road supported. [[c1]] Rail too. [[c9]]\n",
               {"c1": {"claim_id": CID, "claim_hash": "x"}})
    code, findings = vo.validate_output(ana, _live(), tmp_path)
    assert code == 1 and any("[[c9]] does not resolve" in f for f in findings), findings


def test_extra_manifest_claim_never_cited(tmp_path):
    ana = _ana(tmp_path, "Road supported. [[c1]]\n",
               {"c1": {"claim_id": CID, "claim_hash": "x"},
                "c2": {"claim_id": CID, "claim_hash": "x"}})
    code, findings = vo.validate_output(ana, _live(), tmp_path)
    assert code == 1 and any("'c2' is never cited" in f for f in findings), findings


def test_status_preservation_thin_unmarked(tmp_path):
    thin = {**CLAIM, "support_status": "THIN"}
    ana = _ana(tmp_path, "Road supported. [[c1]]\n", {"c1": {"claim_id": CID, "claim_hash": "x"}})
    code, findings = vo.validate_output(ana, _live(thin), tmp_path)
    assert code == 1 and any("omits required visible status tag" in f and "THIN" in f for f in findings), findings


def test_status_preservation_thin_tagged_passes(tmp_path):
    thin = {**CLAIM, "support_status": "THIN"}
    ana = _ana(tmp_path, "Road supported. [[c1|THIN]]\n", {"c1": {"claim_id": CID, "claim_hash": "x"}})
    code, findings = vo.validate_output(ana, _live(thin), tmp_path)
    assert code == 0, findings


def test_unmarked_assertion_warns_in_draft_blocks_in_answer(tmp_path):
    prose = "Rail traffic resumed across the crossing this week.\nRoad supported. [[c1]]\n"
    ana = _ana(tmp_path, prose, {"c1": {"claim_id": CID, "claim_hash": "x"}})
    # draft / standalone: WARN only → exit 0
    code, findings = vo.validate_output(ana, _live(), tmp_path, block_unmarked=False)
    assert code == 0 and any("[warn] unmarked" in f for f in findings), findings
    # answer: BLOCKS → exit 1
    code2, findings2 = vo.validate_output(ana, _live(), tmp_path, block_unmarked=True)
    assert code2 == 1 and any("answer BLOCKS" in f for f in findings2), findings2


def test_unmarked_assertion_cleared_by_exemption(tmp_path):
    sentence = "Rail traffic resumed across the crossing this week."
    prose = sentence + "\nRoad supported. [[c1]]\n"
    ana = _ana(tmp_path, prose, {"c1": {"claim_id": CID, "claim_hash": "x"}},
               exemptions=[vo._sentence_hash(sentence)])
    code, findings = vo.validate_output(ana, _live(), tmp_path, block_unmarked=True)
    assert code == 0, findings  # the reviewed exemption clears the block


def test_a7_colocated_unmarked_claim_is_blocked(tmp_path):
    # the A7 line-grain hole: an unmarked load-bearing claim on the SAME line as an unrelated
    # marked claim must STILL be caught (sentence-grain + attach-backward).
    prose = "Russia lost sixty thousand troops in May. The bridge is open. [[c1]]\n"
    ana = _ana(tmp_path, prose, {"c1": {"claim_id": CID, "claim_hash": "x"}})
    code, findings = vo.validate_output(ana, _live(), tmp_path, block_unmarked=True)
    assert code == 1 and any("Russia lost sixty thousand troops" in f for f in findings), findings


def test_marked_trailing_sentence_not_false_flagged(tmp_path):
    # a sentence whose marker trails it on the same line must NOT be flagged (no regression)
    ana = _ana(tmp_path, "The bridge is open across the river. [[c1]]\n",
               {"c1": {"claim_id": CID, "claim_hash": "x"}})
    code, findings = vo.validate_output(ana, _live(), tmp_path, block_unmarked=True)
    assert code == 0, findings


def test_bulleted_unmarked_claim_is_blocked_marked_passes(tmp_path):
    bad = _ana(tmp_path, "- Russia lost sixty thousand troops in May.\nRoad open. [[c1]]\n",
               {"c1": {"claim_id": CID, "claim_hash": "x"}})
    code, findings = vo.validate_output(bad, _live(), tmp_path, block_unmarked=True)
    assert code == 1, findings  # a bulleted claim is still a claim
    good = _ana(tmp_path, "- The bridge is open across the river [[c1]]\n",
                {"c1": {"claim_id": CID, "claim_hash": "x"}})
    code2, findings2 = vo.validate_output(good, _live(), tmp_path, block_unmarked=True)
    assert code2 == 0, findings2  # a marked bullet passes


def test_output_path_traversal_fails_closed(tmp_path):
    (tmp_path / "outputs").mkdir()
    (tmp_path.parent / "secret.md").write_text("outside the tree\n")
    ana = {"output_path": "../secret.md", "output_hash": "sha256:" + "0" * 64,
           "claim_markers": {}, "narrative_exemptions": []}
    code, findings = vo.validate_output(ana, _live(), tmp_path)
    assert code == 2 and "escapes output_root" in "\n".join(findings)
    ana_abs = {**ana, "output_path": str(tmp_path.parent / "secret.md")}
    assert vo.validate_output(ana_abs, _live(), tmp_path)[0] == 2


def test_schema_rejects_traversing_output_path(tmp_path):
    p = tmp_path / "bad_ana.yaml"
    p.write_text((SK / "skeleton_analysis.yaml").read_text().replace(
        "output_path: outputs/ana-skeleton.md", "output_path: ../../etc/passwd"))
    code, findings = vs.validate_file(p)
    assert code == 1 and any("output_path" in f and "traversal" in f for f in findings), findings


def test_heading_and_blockquote_assertions_are_scanned(tmp_path):
    # Milestone-A P0 review: a load-bearing assertion smuggled into a heading or blockquote was
    # skipped by the old skip-list. It must now be scanned (BLOCKS in answer mode).
    for prose in ("## Russia lost sixty thousand troops in May\nRoad open. [[c1]]\n",
                  "> Russia lost sixty thousand troops in May.\nRoad open. [[c1]]\n"):
        ana = _ana(tmp_path, prose, {"c1": {"claim_id": CID, "claim_hash": "x"}})
        code, findings = vo.validate_output(ana, _live(), tmp_path, block_unmarked=True)
        assert code == 1, (prose, findings)


def test_high_impact_prose_laundering_blocked(tmp_path):
    # cross-vendor review P0-4: a high-impact assertion ("killed 500 civilians") hidden in the same
    # sentence as a marker for an unrelated LOW-impact claim must block (the marker can't launder it).
    ana = _ana(tmp_path, "Road transport is supported and Russia killed 500 civilians. [[c1]]\n",
               {"c1": {"claim_id": CID, "claim_hash": "x"}})  # CID = skeleton low-impact claim
    code, findings = vo.validate_output(ana, _live(), tmp_path, block_unmarked=True)
    assert code == 1 and any("high-impact assertion not bound" in f for f in findings), findings


def test_high_impact_prose_passes_when_hi_marked(tmp_path):
    # a genuine high-impact claim, properly marked, is NOT laundering — the assertion is covered
    hi = {**CLAIM, "id": "clm-hi", "topics": ["casualties"]}  # gate-computes high_impact true
    ana = _ana(tmp_path, "Russia killed 500 civilians. [[c1]]\n",
               {"c1": {"claim_id": "clm-hi", "claim_hash": "x"}})
    code, findings = vo.validate_output(ana, _live(hi), tmp_path, block_unmarked=True)
    assert not any("high-impact assertion not bound" in f for f in findings), findings


def test_high_impact_cross_category_laundering_blocked(tmp_path):
    # cross-vendor RE-review of P0-4: a casualties marker must NOT launder a co-located
    # territorial-control assertion — coverage is per CATEGORY, not "any hi marker present".
    cas = {**CLAIM, "id": "clm-cas", "topics": ["casualties"]}
    ana = _ana(tmp_path, "Russia killed 500 civilians [[c1]] and seized control of Donetsk.\n",
               {"c1": {"claim_id": "clm-cas", "claim_hash": "x"}})
    code, findings = vo.validate_output(ana, _live(cas), tmp_path, block_unmarked=True)
    assert code == 1 and any("high-impact assertion not bound" in f for f in findings), findings
    # a synonym in the SAME category (prose 'deaths' vs claim topic 'casualties') is NOT a false positive
    ana2 = _ana(tmp_path, "Russia caused 500 deaths. [[c1]]\n", {"c1": {"claim_id": "clm-cas", "claim_hash": "x"}})
    assert not any("high-impact assertion not bound" in f
                   for f in vo.validate_output(ana2, _live(cas), tmp_path, block_unmarked=True)[1])


def test_skeleton_output_is_clean(tmp_path):
    # the real skeleton answer: stage its output + manifest, expect 0 with no warns
    import shutil
    (tmp_path / "outputs").mkdir()
    shutil.copy(SK / "skeleton_output.md", tmp_path / "outputs" / "ana-skeleton.md")
    ana = vs.load_yaml_strict(SK / "skeleton_analysis.yaml")["analyses"][0]
    code, findings = vo.validate_output(ana, _live(), tmp_path, block_unmarked=True)
    assert code == 0, findings

"""Tests for `scripts/preflight_phase1.py` — the machine guard that blocks Segment 2 (WP1.x)
until the Phase-1 gate is cleared: the four doc-fixes (V-P0-1, V-P1-4, V-P1-5, F3) present in
the governing docs AND an independent cross-vendor/human review logged.

Logic tested on synthetic roots so the suite stays green regardless of the live gate state.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import preflight_phase1 as pf  # noqa: E402

ALL_TOKENS = list(pf.REQUIRED_TOKENS.values())


def _make_root(tmp, tokens, indep: bool):
    (tmp / "docs").mkdir(parents=True, exist_ok=True)
    (tmp / "docs" / "CONSTITUTION.md").write_text(
        "# Constitution\n\n" + "\n".join(f"... {t} ..." for t in tokens) + "\n", encoding="utf-8")
    (tmp / "docs" / "DATA_MODEL.md").write_text("# Data model\n", encoding="utf-8")
    fm = "true" if indep else "false"
    (tmp / "docs" / "REVIEW_ADJUDICATION.md").write_text(
        f"---\nschema_version: \"1.0\"\nindependent_review_complete: {fm}\n---\n# adj\n",
        encoding="utf-8")
    return tmp


def test_cleared_when_all_fixes_present_and_review_done(tmp_path):
    root = _make_root(tmp_path, ALL_TOKENS, indep=True)
    code, blockers = pf.preflight(root)
    assert code == 0, blockers
    assert blockers == []


def test_missing_one_doc_fix_blocks(tmp_path):
    root = _make_root(tmp_path, [t for t in ALL_TOKENS if t != "unit_vocabulary"], indep=True)
    code, blockers = pf.preflight(root)
    assert code == 2
    assert any("unit_vocabulary" in b for b in blockers)


def test_missing_independent_review_blocks(tmp_path):
    root = _make_root(tmp_path, ALL_TOKENS, indep=False)
    code, blockers = pf.preflight(root)
    assert code == 2
    assert any("independent" in b.lower() for b in blockers)


def test_every_required_fix_is_enforced(tmp_path):
    # dropping each token in turn must produce a blocker naming it
    for drop in ALL_TOKENS:
        root = _make_root(tmp_path / drop, [t for t in ALL_TOKENS if t != drop], indep=True)
        code, blockers = pf.preflight(root)
        assert code == 2 and any(drop in b for b in blockers), drop


def test_fails_closed_on_missing_governing_docs(tmp_path):
    # empty root: no governing docs, no review -> blocked (fail closed)
    code, blockers = pf.preflight(tmp_path)
    assert code == 2
    assert len(blockers) >= 1


def test_cli_blocked_returns_2(tmp_path):
    root = _make_root(tmp_path, ALL_TOKENS, indep=False)
    assert pf.main(["--root", str(root)]) == 2


def test_wrapped_anchor_token_still_matches(tmp_path):
    # a soft-wrapped anchor (line break inside the phrase) must still be detected
    (tmp_path / "docs").mkdir(parents=True)
    const = "# C\n" + "\n".join(
        (t.replace(" ", "\n", 1) if t == "caps support at SUPPORTED" else t) for t in ALL_TOKENS)
    (tmp_path / "docs" / "CONSTITUTION.md").write_text(const, encoding="utf-8")
    (tmp_path / "docs" / "DATA_MODEL.md").write_text("# D\n", encoding="utf-8")
    (tmp_path / "docs" / "REVIEW_ADJUDICATION.md").write_text(
        "---\nindependent_review_complete: true\n---\n", encoding="utf-8")
    code, blockers = pf.preflight(tmp_path)
    assert code == 0, blockers


def test_real_repo_runs_cleanly():
    # state-independent: the gate is either cleared (0) or blocked (2); never crashes.
    code, _blockers = pf.preflight(ROOT)
    assert code in (0, 2)

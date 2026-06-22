"""WP0.3 — confirm the Tier-0 conversational contract (docs/CONVERSATION.md).

WP0.3 ships no code; its acceptance is a usability check. This makes the acceptance bullets a
machine-checkable structural invariant: the doc must define the four labels, the confidence
vocabulary, the self-refute convention, the objective escalation triggers (the F1 hardening),
the high_impact + load-bearing definitions (the F2 doc-level fix), and >=2 worked examples; and
`verify.py --mode conversational` must point here. Presence checks — removing a required section
turns this red.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import verify  # noqa: E402

DOC = (ROOT / "docs" / "CONVERSATION.md").read_text(encoding="utf-8")
LOW = DOC.lower()


def test_doc_exists_and_nonempty():
    assert len(DOC) > 2000


def test_defines_the_four_labels():
    for label in ("fact", "inference", "assumption", "projection"):
        assert f"**{label}" in LOW or f"**{label} /" in LOW, label


def test_defines_confidence_vocabulary():
    for word in ("established", "likely", "uncertain", "speculative"):
        assert word in LOW, word


def test_defines_self_refute_convention():
    assert "self-refute" in LOW
    assert "weakest link" in LOW


def test_lists_objective_escalation_triggers():
    assert "must escalate" in LOW
    # objective triggers (F1): not "if you feel it matters"
    assert "written deliverable" in LOW
    assert "act on, spend on" in LOW or "act on" in LOW
    assert "3+ times" in LOW or "3+ " in LOW  # recurrence backstop


def test_defines_high_impact_and_load_bearing():
    assert "high_impact" in LOW
    assert "load-bearing" in LOW
    # high_impact must be objective, not self-set: the "any hold" / decision/casualties test
    assert "informs a real decision" in LOW
    assert "casualties" in LOW


def test_has_at_least_two_worked_examples():
    assert LOW.count("worked example") >= 2


def test_verify_conversational_mode_points_here():
    code, lines = verify.run_mode("conversational", ROOT)
    out = "\n".join(lines)
    assert code == 0
    assert "CONVERSATION.md" in out
    assert "PASS" not in out  # re-assert the F4 property at the contract boundary

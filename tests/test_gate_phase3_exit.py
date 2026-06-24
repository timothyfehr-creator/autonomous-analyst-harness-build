"""WP3.4 — the Phase-3 exit auto-gate (gate_phase3_exit.py). Each witness must be RED-when-broken,
mirroring the Phase-1/2 gates' per-witness discipline. Exit 0/2 only.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gate_phase3_exit as g3  # noqa: E402


def test_phase3_gate_passes():
    assert g3.main() == 0


def test_each_witness_passes():
    for fn in (g3._draft_empty, g3._draft_compose, g3._answer_compose, g3._answer_no_analysis,
               g3._answer_no_refuter, g3._subgate_propagate, g3._a7_structural,
               g3._a7_semantic_blocks, g3._refuter_coverage, g3._refuter_binding,
               g3._v_p0_1_refuter, g3._phase2_green):
        assert fn() is None, fn.__name__


def test_answer_compose_witness_is_load_bearing(monkeypatch):
    # if answer stopped composing the skeleton (returned non-zero), the witness must catch it
    monkeypatch.setattr(g3.verify, "answer_check", lambda *a, **k: (2, ["broken"]))
    assert g3._answer_compose() is not None


def test_v_p0_1_witness_is_load_bearing(monkeypatch):
    # if the refuter gate stopped enforcing the contest/independence invariants, the witness fails
    monkeypatch.setattr(g3.v_ref, "validate_refuter", lambda *a, **k: (0, []))
    assert g3._v_p0_1_refuter() is not None


def test_a7_semantic_witness_is_load_bearing(monkeypatch):
    # if answer-mode stopped BLOCKING unmarked assertions, the witness fails
    monkeypatch.setattr(g3.v_out, "validate_output", lambda *a, **k: (0, []))
    assert g3._a7_semantic_blocks() is not None


def test_phase2_green_witness_is_load_bearing(monkeypatch):
    monkeypatch.setattr(g3.g2, "main", lambda: 2)
    assert g3._phase2_green() is not None

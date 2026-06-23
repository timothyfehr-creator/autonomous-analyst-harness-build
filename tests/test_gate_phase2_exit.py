"""WP2.x — the Phase-2 exit auto-gate (gate_phase2_exit.py). Each witness must be RED-when-broken,
mirroring the Phase-1 gate's per-witness discipline.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import gate_phase2_exit as g2  # noqa: E402


def test_phase2_gate_passes():
    assert g2.main() == 0


def test_records_empty_witness_passes():
    assert g2._records_empty() is None


def test_records_compose_witness_passes():
    assert g2._records_compose() is None


def test_a_exploits_witness_passes():
    assert g2._a_exploits() is None


def test_phase1_green_witness_passes():
    assert g2._phase1_green() is None


def test_a_exploits_witness_is_load_bearing(monkeypatch):
    # if a gate stopped rejecting its exploit (returned 0), the witness must catch the regression
    monkeypatch.setattr(g2.v_sup, "validate_support", lambda *a, **k: (0, []))
    msg = g2._a_exploits()
    assert msg and "REGRESSED" in msg


def test_compose_witness_is_load_bearing(monkeypatch):
    # if records stopped composing the skeleton (returned non-zero), the witness must catch it
    monkeypatch.setattr(g2.verify, "records_check", lambda *a, **k: (2, ["broken"]))
    assert g2._records_compose() is not None

"""WP0.1 — tests for the unified verifier `scripts/verify.py`.

Discharges F4 (the `conversational` mode must read as "unverified by design" and NEVER as a
gate PASS) and exercises the mode ladder: scaffold→0, records/draft/answer/unknown→2,
no-mode→scaffold. Written failing-first.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import verify  # noqa: E402


def _run(mode, root=ROOT):
    return verify.run_mode(mode, root)  # (code, lines)


# --- F4: the conversational mode must never be mistakable for a verification result ---
def test_conversational_is_unverified_and_never_says_PASS():
    code, lines = _run("conversational")
    out = "\n".join(lines)
    assert code == 0
    assert "unverified by design" in out.lower()
    assert "PASS" not in out  # F4: must never read as a gate pass
    assert "CONVERSATION.md" in out  # points to the labeling contract


def test_scaffold_real_repo_clean():
    assert _run("scaffold")[0] == 0


def test_no_mode_defaults_to_scaffold():
    assert verify.run_mode(None, ROOT)[0] == 0


def test_scaffold_incomplete_root_fails_closed(tmp_path):
    assert _run("scaffold", tmp_path)[0] == 2


def test_records_mode_unavailable():
    code, lines = _run("records")
    assert code == 2 and "unavailable" in "\n".join(lines).lower()


def test_draft_mode_unavailable():
    assert _run("draft")[0] == 2


def test_answer_mode_unavailable():
    assert _run("answer")[0] == 2


def test_unknown_mode_fails_closed():
    code, lines = _run("bogus")
    assert code == 2 and "unknown" in "\n".join(lines).lower()


def test_cli_scaffold_exit0():
    assert verify.main(["--mode", "scaffold"]) == 0


def test_cli_records_exit2():
    assert verify.main(["--mode", "records"]) == 2

"""WP0.0 — tests for the review-adjudication gate.

Valid / invalid-adversarial / regression coverage, plus a dogfood of the real ledger and a
fail-closed check. Synthetic fixtures live in tests/fixtures/ and are passed by explicit path.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_review_adjudication as cra  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def _code(name: str, check_files: bool = False) -> int:
    text = (FIX / name).read_text(encoding="utf-8")
    code, _errors, _infos = cra.check_text(text, root=ROOT, check_files=check_files)
    return code


def test_complete_passes():
    assert _code("adj_complete.md") == 0


def test_missing_field_blocks():
    # a P0/P1 finding missing its proving test -> fail closed (2)
    assert _code("adj_missing_field.md") == 2


def test_blocking_disposition_blocks():
    assert _code("adj_blocking.md") == 2


def test_blocked_governance_status_blocks():
    # the core WP0.0 purpose: BLOCKED governance must not pass
    assert _code("adj_blocked_status.md") == 2


def test_duplicate_id_is_finding():
    assert _code("adj_duplicate_id.md") == 1


def test_out_of_enum_disposition_is_finding():
    # the N10 bug class: a disposition outside the allowed enum
    assert _code("adj_bad_disposition.md") == 1


def test_real_ledger_passes_full_gate():
    """Dogfood: the REAL repo ledger + required-documents check must be clean (0)."""
    text = (ROOT / "docs" / "REVIEW_ADJUDICATION.md").read_text(encoding="utf-8")
    code, errors, _infos = cra.check_text(text, root=ROOT, check_files=True)
    assert code == 0, errors


def test_unreadable_file_fails_closed(tmp_path):
    assert cra.main(["--adjudication", str(tmp_path / "does_not_exist.md")]) == 2


def test_missing_required_document_blocks(tmp_path):
    """A valid ledger but an incomplete repo root → required-files check fails closed (2)."""
    text = (FIX / "adj_complete.md").read_text(encoding="utf-8")
    code, _errors, _infos = cra.check_text(text, root=tmp_path, check_files=True)
    assert code == 2

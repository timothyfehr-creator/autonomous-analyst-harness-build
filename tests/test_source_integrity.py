"""WP2.1 — source registry integrity gate (validate_sources.py). Cross-record rules on top of the
WP1.2 schema: global ID uniqueness, group member resolution, active-window coherence. Failing-first.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_sources as vsrc  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


def _run(name):
    """Return (exit_code, findings) so tests can assert the SPECIFIC rule fired (tamper-evident:
    asserting only the exit code lets a backstopping rule mask the removal of the named one)."""
    return vsrc.validate_sources_file(FIX / name)


def test_valid_registry_passes():
    assert vsrc.main([str(FIX / "src_integrity_valid.yaml")]) == 0


def test_real_factbase_sources_pass():
    # the only seeded factbase file must clear its own integrity gate
    assert vsrc.main([str(ROOT / "factbase" / "sources.yaml")]) == 0


def test_duplicate_id_invalid():
    # dup-ONLY fixture (no group) so the uniqueness rule is probed independently of member-resolution
    code, findings = _run("src_dup_id_only.yaml")
    assert code == 1
    assert any("duplicate id 'src-dup'" in f for f in findings), findings


def test_group_member_unresolved_invalid():
    code, findings = _run("src_group_member_unresolved.yaml")
    assert code == 1
    assert any("does not resolve to a known source" in f for f in findings), findings


def test_group_member_is_group_invalid():
    # assert the PREFIX-specific message, not just exit 1 (the unresolved branch would mask removal)
    code, findings = _run("src_group_member_is_group.yaml")
    assert code == 1
    assert any("must be a src- source id" in f for f in findings), findings


def test_active_window_inverted_invalid():
    assert vsrc.main([str(FIX / "src_active_window_bad.yaml")]) == 1


def test_schema_break_returns_schema_code_not_masked():
    # a schema-broken file fails at the schema layer (1); integrity is not run on malformed records
    assert vsrc.main([str(FIX / "src_schema_bad.yaml")]) == 1


def test_unparseable_fails_closed():
    assert vsrc.main([str(FIX / "envelope_unknown_version.yaml")]) == 2

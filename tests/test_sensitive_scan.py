"""WP0.2 — tests for `scripts/sensitive_scan.py` (sensitive-locator + secret hygiene).

Adversarial-fixtures-first. Discharges N10 (signed/private locators + prohibited private fields
fail) and V-P1-3 (geodata + named-person assessments in scope; private overlay defined).

Critical false-positive guards: the REAL repo must scan clean (0) — sources.yaml's 29 named
people (neutral identity = allowed), the sha256 hashes throughout DATA_MODEL/EXAMPLE_WORKFLOW,
public source URLs, and legit assessment fields (rationale) must NOT trip the scan.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import sensitive_scan as ss  # noqa: E402


def kinds(text):
    return sorted({k for k, _masked in ss.scan_text(text)})


# --- signed / auth URL (N10) ---
def test_signed_url_flagged():
    t = "canonical_locator: https://b.s3.amazonaws.com/d.pdf?X-Amz-Signature=abc123def456ghi789"
    assert "SIGNED_URL" in kinds(t)


def test_signed_url_token_param_flagged():
    assert "SIGNED_URL" in kinds("https://api.example.com/x?access_token=sekrit_value_here_123")


def test_signed_url_nearmiss_canonical_clean():
    # same artifact, credentials/tracking stripped -> must NOT flag (near-miss control)
    assert ss.scan_text("canonical_locator: https://b.s3.amazonaws.com/d.pdf") == []


# --- credential-shaped strings (N10) ---
def test_aws_key_flagged():
    assert "CREDENTIAL" in kinds("aws_key = AKIAIOSFODNN7EXAMPLE")


def test_private_key_block_flagged():
    assert "CREDENTIAL" in kinds("-----BEGIN OPENSSH PRIVATE KEY-----\nb3Blbn...\n-----END OPENSSH PRIVATE KEY-----")


def test_bearer_assignment_flagged():
    assert "CREDENTIAL" in kinds("api_key: 's3cr3t_aBcDeF012345678901234567'")


def test_sha256_hash_not_flagged():
    # GUARD: DATA_MODEL/EXAMPLE_WORKFLOW are full of sha256:<64 hex> — must never flag.
    assert ss.scan_text("content_hash: sha256:" + "0" * 64) == []
    assert ss.scan_text("relationship_input_hash: sha256:" + "ab" * 32) == []


# --- private-network URL ---
def test_private_net_url_flagged():
    assert "PRIVATE_NET_URL" in kinds("see http://192.168.1.50/internal/report")


def test_localhost_url_flagged():
    assert "PRIVATE_NET_URL" in kinds("http://127.0.0.1:8000/x")


def test_public_url_not_flagged():
    # GUARD: real source URLs (gov, news, x.com) must stay clean.
    assert ss.scan_text("canonical_home: https://x.com/ChrisO_wiki") == []
    assert ss.scan_text("canonical_home: https://mil.ru/") == []


# --- file:// outside the repo ---
def test_file_uri_flagged():
    assert "FILE_URI" in kinds("snapshot_ref: file:///Users/me/private/secret.pdf")


# --- private-overlay reserved field (N10 / V-P1-3 private overlay) ---
def test_private_overlay_field_flagged():
    assert "PRIVATE_OVERLAY_FIELD" in kinds("  private_notes: collected via a human source")


def test_source_method_field_flagged():
    assert "PRIVATE_OVERLAY_FIELD" in kinds("    source_method: SIGINT intercept")


def test_legit_assessment_rationale_not_flagged():
    # GUARD: assessment `rationale` is where reliability reasoning legitimately lives (WP1.2).
    assert ss.scan_text("    rationale: Strong attribution; two corrections in sample.") == []
    assert ss.scan_text("    reliability: B") == []


# --- geodata path rule (V-P1-3) ---
def test_committed_geodata_flagged():
    assert ss.is_committed_geodata("geodata/kerch-strike-points.geojson") is True


def test_geodata_in_private_overlay_clean():
    assert ss.is_committed_geodata("private/geodata/kerch-strike-points.geojson") is False


def test_non_geodata_path_clean():
    assert ss.is_committed_geodata("factbase/sources.yaml") is False
    assert ss.is_committed_geodata("factbase/geography.yaml") is False


# --- integration + fail-closed ---
def test_real_repo_scans_clean():
    code, findings = ss.scan_tracked(ROOT)
    if code == 2 and any(getattr(f, "kind", None) == "NO_GIT" for f in findings):
        import pytest
        pytest.skip("not a git checkout (e.g. an unzipped review bundle) — repo scan is git-only")
    assert code == 0, findings


def test_cli_real_repo_zero():
    code, findings = ss.scan_tracked(ROOT)
    if code == 2 and any(getattr(f, "kind", None) == "NO_GIT" for f in findings):
        import pytest
        pytest.skip("not a git checkout (e.g. an unzipped review bundle) — repo scan is git-only")
    assert ss.main(["--root", str(ROOT)]) == 0


def test_fail_closed_not_a_git_repo(tmp_path):
    code, _ = ss.scan_tracked(tmp_path)
    assert code == 2

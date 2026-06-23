"""WP2.2c — cross-commit reward-hack range gate (check_reward_hack.py). Unit tests on the pure
classify_path/evaluate logic + integration tests over throwaway git repos built in tmp_path.
"""
import pathlib
import subprocess
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import check_reward_hack as rh  # noqa: E402


# ============================ pure unit tests (no git) ============================
def test_classify_path_precedence():
    assert rh.classify_path("factbase/baseline/claims.yaml") == "DATA"
    assert rh.classify_path("tests/fixtures/skeleton/skeleton_claims.yaml") == "ORACLE"
    assert rh.classify_path("config/high_impact_triggers.yaml") == "ORACLE"
    assert rh.classify_path("scripts/validate_high_impact.py") == "ORACLE"
    assert rh.classify_path("README.md") == "UNCLASSIFIED"


def test_evaluate_oracle_only_clean():
    code, f, _ = rh.evaluate([("M", "scripts/g.py")], [], [], attested=False)
    assert code == 0 and not f


def test_evaluate_data_only_clean():
    # a factbase claim text edit (no hi flip / no trigger change), no oracle -> nothing fires
    code, f, _ = rh.evaluate([("M", "factbase/baseline/claims.yaml")],
                             [{"id": "clm-x", "status": "M", "base_hi": False, "head_hi": False,
                               "trigger_inputs_changed": []}], [], attested=False)
    assert code == 0 and not f


def test_evaluate_co_change_flagged_and_attestation_clears():
    changed = [("M", "scripts/g.py"), ("M", "factbase/baseline/claims.yaml")]
    code, f, _ = rh.evaluate(changed, [], [], attested=False)
    assert code == 1 and any("R-RH" in x for x in f)
    code2, f2, cleared = rh.evaluate(changed, [], [], attested=True)
    assert code2 == 0 and not f2 and any("R-RH" in c for c in cleared)


def test_evaluate_netnew_data_does_not_trip_rrh():
    # net-new factbase data (status A) is not "modified" -> R-RH does not fire
    code, f, _ = rh.evaluate([("M", "scripts/g.py"), ("A", "factbase/x.yaml")], [], [], attested=False)
    assert code == 0 and not f


def test_evaluate_high_impact_flip_flagged():
    code, f, _ = rh.evaluate([("M", "factbase/baseline/claims.yaml")],
                             [{"id": "clm-x", "status": "M", "base_hi": True, "head_hi": False,
                               "trigger_inputs_changed": []}], [], attested=False)
    assert code == 1 and any("R-HI" in x and "true" in x for x in f)


def test_evaluate_in_place_rating_change_not_cleared_by_attestation():
    # R-EDIT is an append-only violation, NOT a "reviewed separately" escape
    asses = [{"id": "sas-x", "status": "M", "base_reliability": "D", "head_reliability": "A"}]
    code, f, _ = rh.evaluate([("M", "factbase/source_assessments.yaml")], [], asses, attested=True)
    assert code == 1 and any("R-EDIT" in x for x in f)


# ============================ integration tests (real tmp git repos) ============================
def _git(repo, *args):
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def _init(repo):
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "t@example.invalid")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "commit.gpgsign", "false")


def _write(repo, rel, text):
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def _commit(repo, msg):
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD")


CLAIM = '''schema_version: "2.0"
claims:
  - id: clm-x
    text: {text}
    epistemic_type: FACT
    support_status: SUPPORTED
    dispute_status: UNCONTESTED
    freshness_status: CURRENT
    lifecycle: REVIEWED
    stability: DURABLE
    topics: [{topics}]
    high_impact: {hi}
    created_at: "2026-06-22T00:00:00Z"
    supersedes: null
    temporal: {{kind: AS_OF, event_time: null, as_of: "2026-06-22T00:00:00Z"}}
    review_by: "2026-12-22T00:00:00Z"
'''

ASSESS = '''schema_version: "2.0"
source_assessments:
  - id: sas-soc
    source_id: src-social
    scope: social posts
    reliability: {rel}
    sample_definition: 10 posts
    sample_size: 10
    rationale: ok
    assessed_by: human:tim
    assessed_at: "2026-06-22"
    supersedes: null
'''


def _base_repo(tmp_path):
    repo = tmp_path / "repo"
    _init(repo)
    _write(repo, "scripts/validate_sources.py", "THRESHOLD = 3\n")
    _write(repo, "factbase/baseline/claims.yaml", CLAIM.format(text="A", topics="casualties", hi="true"))
    _write(repo, "factbase/source_assessments.yaml", ASSESS.format(rel="D"))
    base = _commit(repo, "base")
    return repo, base


def test_two_commit_split_flagged(tmp_path):
    # commit 1 weakens an oracle; commit 2 edits a factbase claim's text; range spans both
    repo, base = _base_repo(tmp_path)
    _write(repo, "scripts/validate_sources.py", "THRESHOLD = 1\n")
    _commit(repo, "lower threshold")
    _write(repo, "factbase/baseline/claims.yaml", CLAIM.format(text="B", topics="casualties", hi="true"))
    _commit(repo, "edit claim text")
    code, findings, _ = rh.run(repo, base, "HEAD")
    assert code == 1 and any("R-RH" in f for f in findings), findings


def test_attested_co_change_cleared(tmp_path):
    repo, base = _base_repo(tmp_path)
    _write(repo, "scripts/validate_sources.py", "THRESHOLD = 1\n")
    _commit(repo, "lower threshold\n\nReviewed-separately: ticket-1")
    _write(repo, "factbase/baseline/claims.yaml", CLAIM.format(text="B", topics="casualties", hi="true"))
    _commit(repo, "edit claim text\n\nReviewed-separately: ticket-1")
    code, findings, cleared = rh.run(repo, base, "HEAD")
    assert code == 0 and not findings and any("R-RH" in c for c in cleared), (findings, cleared)


def test_high_impact_flip_flagged(tmp_path):
    repo, base = _base_repo(tmp_path)
    # all-DATA tamper: flip high_impact true->false and drop the casualties topic in one commit
    _write(repo, "factbase/baseline/claims.yaml", CLAIM.format(text="A", topics="logistics", hi="false"))
    _commit(repo, "quietly downgrade")
    code, findings, _ = rh.run(repo, base, "HEAD")
    assert code == 1 and any("R-HI" in f and "true" in f for f in findings), findings


def test_in_place_rating_change_flagged(tmp_path):
    repo, base = _base_repo(tmp_path)
    _write(repo, "factbase/source_assessments.yaml", ASSESS.format(rel="A"))  # D -> A in place
    _commit(repo, "bump reliability")
    code, findings, _ = rh.run(repo, base, "HEAD")
    assert code == 1 and any("R-EDIT" in f for f in findings), findings


def test_social_source_upgrade_collusion_flagged(tmp_path):
    # a NEW superseding assessment (append-only-respecting) + a claim change in the same range,
    # no attestation -> R-COLLUDE (benefiting a same-range claim without a named exception)
    repo, base = _base_repo(tmp_path)
    _write(repo, "factbase/source_assessments.yaml", ASSESS.format(rel="D") +
           '''  - id: sas-soc-2
    source_id: src-social
    scope: social posts
    reliability: A
    sample_definition: 10 posts
    sample_size: 10
    rationale: upgraded
    assessed_by: human:tim
    assessed_at: "2026-06-23"
    supersedes: sas-soc
''')
    _write(repo, "factbase/baseline/claims.yaml", CLAIM.format(text="now-supported", topics="logistics", hi="false"))
    _commit(repo, "upgrade social source and adjust claim")
    code, findings, _ = rh.run(repo, base, "HEAD")
    assert code == 1 and any("R-COLLUDE" in f for f in findings), findings


def test_oracle_only_clean(tmp_path):
    repo, base = _base_repo(tmp_path)
    _write(repo, "scripts/validate_sources.py", "THRESHOLD = 1\n")
    _commit(repo, "refactor gate, no data touched")
    code, findings, _ = rh.run(repo, base, "HEAD")
    assert code == 0 and not findings, findings


def test_missing_base_fails_closed():
    with pytest.raises(SystemExit) as e:
        rh.main(["--head", "HEAD"])  # --base omitted -> argparse error (exit 2)
    assert e.value.code == 2


def test_bad_base_fails_closed(tmp_path):
    repo, _ = _base_repo(tmp_path)
    code, findings, _ = rh.run(repo, "deadbeefdeadbeef", "HEAD")
    assert code == 2 and any("fail closed" in f for f in findings), findings


def test_not_a_git_repo_fails_closed(tmp_path):
    code, findings, _ = rh.run(tmp_path / "nope", "HEAD~1", "HEAD")
    assert code == 2


def test_standing_invariant_high_impact_fixture_stays_red(tmp_path):
    # R4: the high_impact reward-hack case must keep flagging (a later WP cannot silently regress it)
    repo, base = _base_repo(tmp_path)
    _write(repo, "factbase/baseline/claims.yaml", CLAIM.format(text="A", topics="logistics", hi="false"))
    _commit(repo, "downgrade")
    code, _, _ = rh.run(repo, base, "HEAD")
    assert code == 1

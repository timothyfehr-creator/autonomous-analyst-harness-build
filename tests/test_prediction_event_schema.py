"""WP1.5 — prediction registry (YAML envelope) + append-only event-log (JSONL) schemas.

Shape + per-record cross-field rules only. The cross-LINE append-only chain (previous_event_hash
continuity, event_hash recomputation, external anchor) is Phase-2 integrity, not here.
An empty event log is VALID (logs start empty); only LOCK / PROMOTE variant bodies are specified
in DATA_MODEL §7/§13, so those are the variants enforced. Failing-first.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_schema as vs  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


# ---- prediction registry (YAML) ----
def test_valid_prediction_envelope_passes():
    assert vs.main([str(FIX / "prd_valid.yaml")]) == 0


def test_empty_prediction_registry_passes():
    assert vs.main([str(ROOT / "factbase" / "predictions.yaml")]) == 0


def test_probability_out_of_range_invalid():
    assert vs.main([str(FIX / "prd_prob_out_of_range.yaml")]) == 1


def test_resolve_by_not_after_as_of_invalid():
    assert vs.main([str(FIX / "prd_resolve_before_asof.yaml")]) == 1


def test_resolution_authority_must_be_source_invalid():
    assert vs.main([str(FIX / "prd_authority_not_source.yaml")]) == 1


def test_prediction_unknown_field_invalid():
    assert vs.main([str(FIX / "prd_unknown_field.yaml")]) == 1


def test_predictions_registered():
    assert "predictions" in vs.SCHEMAS


# ---- append-only event logs (JSONL) ----
def test_empty_event_logs_pass():
    # the seed logs ship empty and must validate cleanly (append-only logs start empty)
    assert vs.main([str(ROOT / "factbase" / "prediction_events.jsonl")]) == 0
    assert vs.main([str(ROOT / "factbase" / "baseline_events.jsonl")]) == 0


def test_valid_lock_event_passes():
    assert vs.main([str(FIX / "prediction_events_lock_valid.jsonl")]) == 0


def test_valid_promote_event_passes():
    assert vs.main([str(FIX / "baseline_events_promote_valid.jsonl")]) == 0


def test_lock_missing_record_hash_invalid():
    assert vs.main([str(FIX / "prediction_events_lock_missing_record_hash.jsonl")]) == 1


def test_event_bad_type_invalid():
    assert vs.main([str(FIX / "prediction_events_bad_type.jsonl")]) == 1


def test_event_bad_event_hash_invalid():
    assert vs.main([str(FIX / "prediction_events_bad_event_hash.jsonl")]) == 1


def test_event_duplicate_json_key_invalid():
    assert vs.main([str(FIX / "prediction_events_dup_key.jsonl")]) == 1


def test_promote_missing_hash_invalid():
    assert vs.main([str(FIX / "baseline_events_promote_missing_hash.jsonl")]) == 1


def test_promote_bad_hashlist_invalid():
    assert vs.main([str(FIX / "baseline_events_promote_bad_hashlist.jsonl")]) == 1


def test_unrecognized_jsonl_fails_closed():
    # a .jsonl whose name matches no known event log can't be validated -> fail closed (exit 2)
    p = FIX / "prd_valid.yaml"  # any path; we synthesize an unknown-stem path below
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, dir=str(FIX)) as fh:
        fh.write('{"event_id":"evt-x","event_type":"LOCK"}\n')
        name = fh.name
    try:
        assert vs.main([name]) == 2
    finally:
        pathlib.Path(name).unlink()


def test_event_logs_registered():
    assert "prediction_events" in vs.EVENT_SCHEMAS and "baseline_events" in vs.EVENT_SCHEMAS

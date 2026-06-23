"""WP1.1 — schema-core framework + the GOLDEN CANONICALIZATION VECTOR (V-P1-7).

The golden vector is hand-specified (sorted keys, compact separators, NFC, computed/mutable
fields excluded, null-vs-absent distinct, list order preserved) so it is a real frozen oracle,
not "whatever the code produces." Every later WP runs this file via `pytest`, so any change to
hashing turns red immediately (the R1 tripwire). Written failing-first.
"""
import pathlib
import sys
import unicodedata

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import validate_schema as vs  # noqa: E402

FIX = ROOT / "tests" / "fixtures"


# ---------------- GOLDEN CANONICALIZATION VECTOR (V-P1-7) ----------------
# (input object, exclude fields) -> exact canonical JSON string. Hand-verified.
GOLDEN = [
    ({"b": 1, "a": 2}, (), '{"a":2,"b":1}'),
    ({"id": "x", "computed": 9, "n": {"z": 1, "y": 2}}, ("computed",), '{"id":"x","n":{"y":2,"z":1}}'),
    ({"a": None, "b": 1}, (), '{"a":null,"b":1}'),
    ({"items": [3, 1, 2]}, (), '{"items":[3,1,2]}'),
    ({"t": True, "f": False}, (), '{"f":false,"t":true}'),
]


def test_canonicalize_matches_golden_vector():
    for obj, exclude, expected in GOLDEN:
        assert vs.canonicalize(obj, exclude) == expected, (obj, exclude)


def test_record_hash_is_sha256_of_canonical_bytes():
    import hashlib
    for obj, exclude, expected in GOLDEN:
        want = "sha256:" + hashlib.sha256(expected.encode("utf-8")).hexdigest()
        assert vs.record_hash(obj, exclude) == want


def test_canonicalize_nfc_normalizes_strings():
    decomposed = unicodedata.normalize("NFD", "café")  # 'e' + combining acute
    composed = unicodedata.normalize("NFC", "café")
    assert decomposed != composed
    assert vs.canonicalize({"x": decomposed}) == vs.canonicalize({"x": composed})


def test_null_vs_absent_are_distinct():
    assert vs.canonicalize({"a": None, "b": 1}) != vs.canonicalize({"b": 1})


def test_excluded_fields_do_not_affect_hash():
    a = {"id": "x", "support_status": "UNVERIFIED", "n": 1}
    b = {"id": "x", "support_status": "CORROBORATED", "n": 1}
    assert vs.record_hash(a, ("support_status",)) == vs.record_hash(b, ("support_status",))


# ---------------- envelope validation ----------------
def test_envelope_valid_exit0():
    assert vs.main([str(FIX / "envelope_valid.yaml")]) == 0


def test_envelope_unknown_version_exit2():
    assert vs.main([str(FIX / "envelope_unknown_version.yaml")]) == 2


def test_per_record_version_rejected_exit1():
    assert vs.main([str(FIX / "envelope_per_record_version.yaml")]) == 1


def test_duplicate_key_rejected_exit1():
    assert vs.main([str(FIX / "envelope_dup_key.yaml")]) == 1


def test_zero_input_fails_closed_exit2():
    assert vs.main([]) == 2  # no files given -> fail closed
    assert vs.main([str(FIX / "envelope_empty_missing_version.yaml")]) == 2


# ---------------- validation primitives (against a demo schema spec) ----------------
DEMO = {"prefix": "dmo-", "required": {"id", "created_at", "kind", "n"},
        "optional": {"note"}, "enums": {"kind": {"A", "B"}},
        "types": {"n": "number", "id": "id", "created_at": "datetime"}}


def test_unknown_field_rejected():
    rec = {"id": "dmo-1", "created_at": "2026-06-22T00:00:00Z", "kind": "A", "n": 1, "surprise": 9}
    findings = vs.validate_record(rec, DEMO)
    assert any("unknown field" in f.lower() and "surprise" in f for f in findings)


def test_bool_as_number_rejected():
    rec = {"id": "dmo-1", "created_at": "2026-06-22T00:00:00Z", "kind": "A", "n": True}
    findings = vs.validate_record(rec, DEMO)
    assert any("n" in f and ("number" in f.lower() or "bool" in f.lower()) for f in findings)


def test_bad_timestamp_rejected():
    rec = {"id": "dmo-1", "created_at": "2026-06-22 00:00:00", "kind": "A", "n": 1}  # no T/Z
    findings = vs.validate_record(rec, DEMO)
    assert any("created_at" in f for f in findings)


def test_bad_enum_rejected():
    rec = {"id": "dmo-1", "created_at": "2026-06-22T00:00:00Z", "kind": "Z", "n": 1}
    findings = vs.validate_record(rec, DEMO)
    assert any("kind" in f for f in findings)


def test_bad_id_prefix_rejected():
    rec = {"id": "wrong-1", "created_at": "2026-06-22T00:00:00Z", "kind": "A", "n": 1}
    findings = vs.validate_record(rec, DEMO)
    assert any("id" in f.lower() for f in findings)


def test_valid_record_clean():
    rec = {"id": "dmo-1", "created_at": "2026-06-22T00:00:00Z", "kind": "A", "n": 1, "note": "ok"}
    assert vs.validate_record(rec, DEMO) == []


def test_findings_are_deterministically_ordered():
    rec = {"id": "BAD", "created_at": "nope", "kind": "Z", "n": True, "x": 1, "y": 2}
    assert vs.validate_record(rec, DEMO) == vs.validate_record(dict(rec), DEMO)

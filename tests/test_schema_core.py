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


# ---- WP3.0 R1 extension: the two Phase-3 hash conventions, hand-frozen ----
# claim_content_hash = record_hash(claim, exclude=CLAIM_CONTENT_EXCLUDE). Frozen so the exclude set
# AND the canonicalization both lock — any drift in either turns this red at the causing WP.
_CONTENT_CLAIM = {"id": "clm-x", "text": "t", "epistemic_type": "FACT", "topics": ["a"],
                  "high_impact": False, "stability": "DURABLE", "support_status": "SUPPORTED",
                  "lifecycle": "REVIEWED", "created_at": "2026-01-01T00:00:00Z"}


def test_claim_content_hash_frozen_vector():
    assert vs.claim_content_hash(_CONTENT_CLAIM) == \
        "sha256:01dda7c886a732805066b80b1df5cee85fc2810493de7f32cb467e420f1d3216"


def test_claim_content_hash_excludes_status_includes_content():
    base = vs.claim_content_hash(_CONTENT_CLAIM)
    # ALL 9 excluded fields must be no-ops (locks every member of CLAIM_CONTENT_EXCLUDE: dropping
    # any one from the set would make a benign re-review/refresh/supersession spuriously break a
    # marker, and would turn THIS red). Setting an excluded field that the base lacks must still
    # equal base — proving it is stripped.
    import schema_defs
    excluded_vals = {"lifecycle": "SUPERSEDED", "support_status": "CORROBORATED",
                     "dispute_status": "CONTESTED", "freshness_status": "STALE",
                     "created_at": "2099-01-01T00:00:00Z", "supersedes": "clm-other",
                     "review_by": "2099-01-01T00:00:00Z", "expires_at": "2099-01-01T00:00:00Z",
                     "freshness_profile": "volatile-7d"}
    assert set(excluded_vals) == set(schema_defs.CLAIM_CONTENT_EXCLUDE)  # keep this test exhaustive
    for fld, val in excluded_vals.items():
        assert vs.claim_content_hash({**_CONTENT_CLAIM, fld: val}) == base, fld
    # mutating real content (incl. high_impact, deliberately IN) MUST change it
    for fld, val in [("text", "different"), ("topics", ["b"]), ("high_impact", True),
                     ("epistemic_type", "INFERENCE"), ("stability", "VOLATILE"),
                     ("temporal", {"kind": "TIMELESS"})]:
        assert vs.claim_content_hash({**_CONTENT_CLAIM, fld: val}) != base, fld


def test_output_hash_is_raw_bytes_not_canonicalized(tmp_path):
    # output_hash = sha256(raw UTF-8 bytes), NO canonicalization — frozen vector
    p = tmp_path / "ans.md"
    p.write_text("committed answer.\n", encoding="utf-8")
    assert vs.file_content_hash(p) == \
        "sha256:b15dcb13a569352c3c995858948cefddc0958efae9c5189d3c7378ee0e198ffb"
    # NFD and NFC of the same string hash DIFFERENTLY (proves no NFC normalization, unlike record_hash)
    import unicodedata
    nfc = tmp_path / "nfc.md"; nfc.write_bytes(unicodedata.normalize("NFC", "café").encode("utf-8"))
    nfd = tmp_path / "nfd.md"; nfd.write_bytes(unicodedata.normalize("NFD", "café").encode("utf-8"))
    assert vs.file_content_hash(nfc) != vs.file_content_hash(nfd)
    assert vs.record_hash("café") == vs.record_hash(unicodedata.normalize("NFD", "café"))  # record_hash DOES normalize


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

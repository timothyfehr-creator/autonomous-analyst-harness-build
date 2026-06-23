#!/usr/bin/env python3
"""WP1.1 — schema-core framework: closed-schema validation + the canonical hash serialization.

Provides the primitives every later schema WP (1.2–1.6) and gate (2.x/3.x) builds on:
  - canonicalize() / record_hash(): the FROZEN canonical serialization. The golden vector in
    tests/test_schema_core.py pins it; any change there turns the suite red (the R1 tripwire).
  - strict YAML load (rejects duplicate keys), envelope validation (root-only version 2.0,
    unknown version fails closed, per-record version prohibited), and validate_record() (closed
    fields, id format, datetime, enum, number-not-bool) with deterministic finding order.
  - register_schema(): later WPs register per-record schemas; validate_file() then enforces them.

Exit codes: 0 clean · 1 findings in valid input · 2 cannot-run / fail closed (no files, missing
or unknown schema_version, unparseable).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
KNOWN_VERSIONS = {"2.0"}

# Per-record-type schemas registered by WP1.2–1.6: collection_name -> spec dict
# spec = {prefix, required:set, optional:set, enums:{field:set}, types:{field:"id|datetime|number|..."}}
SCHEMAS: dict[str, dict] = {}


def register_schema(collection: str, spec: dict) -> None:
    SCHEMAS[collection] = spec


# ----------------------------- canonicalization (frozen; R1) -----------------------------
def _strip(obj, exclude):
    if isinstance(obj, dict):
        return {k: _strip(v, ()) for k, v in obj.items() if k not in exclude}
    if isinstance(obj, list):
        return [_strip(v, ()) for v in obj]
    if isinstance(obj, str):
        return unicodedata.normalize("NFC", obj)
    return obj


def canonicalize(obj, exclude=()) -> str:
    """Deterministic JSON: NFC strings, sorted keys, compact, top-level `exclude` fields dropped,
    null distinct from absent, list order preserved."""
    return json.dumps(_strip(obj, set(exclude)), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def record_hash(obj, exclude=()) -> str:
    return "sha256:" + hashlib.sha256(canonicalize(obj, exclude).encode("utf-8")).hexdigest()


# ----------------------------- strict YAML load -----------------------------
class DuplicateKey(yaml.YAMLError):
    pass


class _StrictLoader(yaml.SafeLoader):
    pass


def _no_dup_mapping(loader, node, deep=False):
    mapping = {}
    for k_node, v_node in node.value:
        k = loader.construct_object(k_node, deep=deep)
        if k in mapping:
            raise DuplicateKey(f"duplicate key: {k!r}")
        mapping[k] = loader.construct_object(v_node, deep=deep)
    return mapping


_StrictLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _no_dup_mapping)


def load_yaml_strict(path: Path):
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_StrictLoader)


# ----------------------------- primitives -----------------------------
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")


def is_iso_datetime(s) -> bool:
    return isinstance(s, str) and bool(_DATE_RE.match(s) or _DATETIME_RE.match(s))


def is_id(s, prefix: str) -> bool:
    return isinstance(s, str) and bool(re.match(rf"^{re.escape(prefix)}[a-z0-9][a-z0-9.\-]*$", s))


def validate_record(rec: dict, spec: dict) -> list[str]:
    """Return a deterministically-sorted list of finding strings for one record vs its spec."""
    findings = []
    if not isinstance(rec, dict):
        return [f"record is not a mapping: {rec!r}"]
    allowed = set(spec.get("required", set())) | set(spec.get("optional", set()))
    for field in sorted(set(rec) - allowed):
        findings.append(f"unknown field {field!r}")
    for field in sorted(set(spec.get("required", set())) - set(rec)):
        findings.append(f"missing required field {field!r}")
    for field, typ in sorted(spec.get("types", {}).items()):
        if field not in rec:
            continue
        v = rec[field]
        if typ == "id":
            if not is_id(v, spec.get("prefix", "")):
                findings.append(f"field {field!r}: invalid id {v!r} (expected prefix {spec.get('prefix','')!r})")
        elif typ == "datetime":
            if not is_iso_datetime(v):
                findings.append(f"field {field!r}: invalid datetime {v!r} (need ISO date or ...T..Z)")
        elif typ == "number":
            if isinstance(v, bool) or not isinstance(v, (int, float)):
                findings.append(f"field {field!r}: expected number, got {type(v).__name__}")
        elif typ == "integer":
            if isinstance(v, bool) or not isinstance(v, int):
                findings.append(f"field {field!r}: expected integer, got {type(v).__name__}")
    for field, allowed_vals in sorted(spec.get("enums", {}).items()):
        if field in rec and rec[field] not in allowed_vals:
            findings.append(f"field {field!r}: {rec[field]!r} not in enum {sorted(allowed_vals)}")
    return sorted(findings)


def validate_envelope(data) -> list[str]:
    """Structure findings (collection shape, per-record version). Version itself handled upstream."""
    findings = []
    collections = [k for k in data if k != "schema_version"]
    if len(collections) != 1:
        return [f"envelope must have exactly one collection besides schema_version, found {sorted(collections)}"]
    name = collections[0]
    coll = data[name]
    if not isinstance(coll, list):
        return [f"collection {name!r} must be a list"]
    for i, rec in enumerate(coll):
        if isinstance(rec, dict) and "schema_version" in rec:
            findings.append(f"per-record schema_version prohibited (collection {name!r}, record {i})")
    if name in SCHEMAS:
        for i, rec in enumerate(coll):
            for f in validate_record(rec, SCHEMAS[name]):
                findings.append(f"{name}[{i}]: {f}")
    return sorted(findings)


def validate_file(path: Path):
    """Return (exit_code, findings) for one registry file."""
    try:
        data = load_yaml_strict(path)
    except DuplicateKey as e:
        return 1, [f"{path.name}: {e}"]
    except (OSError, yaml.YAMLError) as e:
        return 2, [f"{path.name}: cannot parse ({e})"]
    if not isinstance(data, dict) or "schema_version" not in data:
        return 2, [f"{path.name}: missing root schema_version (fail closed)"]
    if data["schema_version"] not in KNOWN_VERSIONS:
        return 2, [f"{path.name}: unknown schema_version {data['schema_version']!r} (known: {sorted(KNOWN_VERSIONS)})"]
    findings = [f"{path.name}: {f}" for f in validate_envelope(data)]
    return (1 if findings else 0), findings


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP1.1 closed-schema / envelope validator")
    p.add_argument("paths", nargs="*", type=Path)
    args = p.parse_args(argv)
    if not args.paths:
        print("[FAIL closed] no input files given", file=sys.stderr)
        return 2
    code, all_findings = 0, []
    for path in args.paths:
        c, findings = validate_file(path)
        code = max(code, c)
        all_findings += findings
    for f in sorted(all_findings):
        print(f"  [finding] {f}", file=sys.stderr)
    if code == 0:
        print("OK — schema/envelope checks clean.")
    return code


if __name__ == "__main__":
    sys.exit(main())

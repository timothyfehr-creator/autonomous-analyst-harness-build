#!/usr/bin/env python3
"""WP0.2 — sensitive-locator + secret hygiene scanner.

Defence-in-depth over tracked *content* (evidence records, factbase data, docs): evidence
records can carry signed URLs, private document IDs, tokens, and source/method notes. Rejects:
credential-shaped strings, signed/auth URLs, private-network URLs, `file://` locators, tracked
geodata of locations of interest (V-P1-3), and private-overlay-reserved fields in tracked
records (N10). Masks findings. Fails closed (exit 2) on no git repo or zero tracked files.

Scope: tracked files EXCLUDING `tests/` (synthetic adversarial fixtures, scanned by explicit
test path) and this module itself (a ruleset must not scan its own patterns). Reliability
rationale legitimately lives in assessment `rationale` (WP1.2); neutral source identity
(names, handles, public home URLs) is allowed — only the reserved private-overlay fields and
secret-shaped locators are rejected.

Exit codes: 0 clean · 1 sensitive findings · 2 could-not-run (no git / zero tracked files).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import namedtuple
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
Finding = namedtuple("Finding", "kind path detail")

EXCLUDE_PREFIXES = ("tests/", ".venv/", "__pycache__/")
EXCLUDE_FILES = ("scripts/sensitive_scan.py",)  # the ruleset must not scan its own patterns

# Credential detection is by key-name/prefix context, NOT entropy — so the sha256:<hex> hashes
# throughout DATA_MODEL/EXAMPLE_WORKFLOW never trip it. Bare "token" is excluded so
# `token_budget` stays clean; only access_token/auth_token/bearer count.
AWS_KEY_RE = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
PRIVATE_KEY_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
SECRET_KEY_RE = re.compile(
    r"(?i)\b(api[_-]?key|secret|password|passwd|access[_-]?token|auth[_-]?token|bearer)\b"
    r"\s*[:=]\s*['\"]?([A-Za-z0-9_\-/+]{16,})"
)
SIGNED_URL_RE = re.compile(
    r"(?i)https?://[^\s'\"\)]+[?&]"
    r"(x-amz-signature|x-amz-credential|awsaccesskeyid|x-amz-security-token|signature|expires"
    r"|sig|token|access_token|api_key|apikey|auth_token)=[^\s'\"&\)]+"
)
PRIVATE_NET_RE = re.compile(
    r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0"
    r"|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}"
    r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})"
)
# Requires an actual path after file:// — a real local locator always has one; a bare
# "file://" (e.g. prose describing this scanner) is not a sensitive locator.
FILE_URI_RE = re.compile(r"file://[^\s'\"\)]*/[^\s'\"\)]+")
OVERLAY_FIELD_RE = re.compile(
    r"(?im)^\s*(private_notes|collection_notes|source_method|method_notes|analyst_notes"
    r"|raw_signed_url|private_locator|source_contact|reliability_note)\s*:"
)
GEODATA_EXT = (".geojson", ".json", ".kml", ".gpkg", ".shp")


def _mask(s: str) -> str:
    s = s.strip()
    return (s[:8] + f"…[masked:{len(s)}]") if len(s) > 10 else "[masked]"


def scan_text(text: str):
    """Return [(kind, masked_detail)] for secret-shaped content. Pure; no I/O."""
    out = []
    for m in AWS_KEY_RE.finditer(text):
        out.append(("CREDENTIAL", _mask(m.group(0))))
    if PRIVATE_KEY_RE.search(text):
        out.append(("CREDENTIAL", "[private key block]"))
    for m in SECRET_KEY_RE.finditer(text):
        out.append(("CREDENTIAL", _mask(m.group(2))))
    for m in SIGNED_URL_RE.finditer(text):
        out.append(("SIGNED_URL", _mask(m.group(0))))
    for m in PRIVATE_NET_RE.finditer(text):
        out.append(("PRIVATE_NET_URL", _mask(m.group(0))))
    for m in FILE_URI_RE.finditer(text):
        out.append(("FILE_URI", _mask(m.group(0))))
    for m in OVERLAY_FIELD_RE.finditer(text):
        out.append(("PRIVATE_OVERLAY_FIELD", m.group(1)))
    return out


def is_committed_geodata(relpath: str) -> bool:
    """Tracked geometry of locations of interest belongs in git-ignored private/, not geodata/."""
    rp = relpath.replace("\\", "/")
    if rp.startswith("private/"):
        return False
    return rp.startswith("geodata/") and rp.lower().endswith(GEODATA_EXT)


def _excluded(rel: str) -> bool:
    return rel in EXCLUDE_FILES or any(rel.startswith(p) for p in EXCLUDE_PREFIXES)


def scan_file(path: Path, repo_root: Path):
    rel = str(path.relative_to(repo_root)).replace("\\", "/")
    findings = []
    if is_committed_geodata(rel):
        findings.append(Finding("COMMITTED_GEODATA", rel,
                                "sensitive geometry must live in private/, not tracked"))
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return findings  # skip binary / unreadable
    for kind, detail in scan_text(text):
        findings.append(Finding(kind, rel, detail))
    return findings


def _tracked_files(root: Path):
    try:
        out = subprocess.run(["git", "-C", str(root), "ls-files"],
                             capture_output=True, text=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return [ln for ln in out.stdout.splitlines() if ln]


def scan_tracked(root: Path):
    files = _tracked_files(root)
    if files is None:
        return 2, [Finding("NO_GIT", str(root), "not a git repository — failing closed")]
    if not files:
        return 2, [Finding("ZERO_TRACKED", str(root), "no tracked files — failing closed")]
    findings = []
    for rel in files:
        if _excluded(rel):
            continue
        findings += scan_file(root / rel, root)
    return (1 if findings else 0), findings


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="WP0.2 sensitive-locator + secret hygiene scanner")
    p.add_argument("--root", type=Path, default=REPO_ROOT)
    args = p.parse_args(argv)
    code, findings = scan_tracked(args.root)
    for f in sorted(findings):
        print(f"  [{f.kind}] {f.path}: {f.detail}", file=sys.stderr)
    if code == 0:
        print("OK — no sensitive locators or secret-shaped strings in tracked content.")
    elif code == 2:
        print(f"FAILED closed — scan could not genuinely run: {findings[0].detail}", file=sys.stderr)
    else:
        print(f"FAILED — {len(findings)} sensitive finding(s).", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())

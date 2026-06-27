#!/usr/bin/env python3
"""WP3.2 — output-text ↔ manifest binding (the answer-mode output control).

Where validate_manifest_structural (WP3.1) checks the manifest pins live records, THIS checks the
reviewed ANSWER TEXT faithfully reflects that manifest:

  - output_hash binds the exact prose bytes: sha256(raw UTF-8 file) == analysis.output_hash
    (WP3.0 raw-bytes rule); a post-review edit of the answer turns red. Missing file → cannot-run 2.
  - marker resolution (both directions, the A7 STRUCTURAL half):
      * every `[[marker]]` in the prose resolves to a claim_markers key (no dangling marker);
      * every claim_markers key is USED in the prose (no manifest claim left uncited — "extra
        manifest claims never used");
  - status preservation (§7): a cited claim that is live UNVERIFIED/THIN, CONTESTED, STALE, or
    ASSUMPTION/INFERENCE/PROJECTION must carry the matching visible status tag, `[[c1|THIN]]`;
  - unmarked assertion-like sentences (the A7 SEMANTIC half): an inherently heuristic scan.
      * draft / standalone (block_unmarked=False): WARN only — does not change the exit code;
      * answer (block_unmarked=True, WP3.4): BLOCKS (exit 1) unless the sentence is marked,
        demoted, or hash-listed in analysis.narrative_exemptions (the reviewed escape).

Returns (exit_code, findings): 0 clean · 1 finding in valid input · 2 cannot-run (missing output).
The marker↔live-record hash binding is validate_manifest_structural's job (run in draft first).
"""
from __future__ import annotations

import hashlib
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_high_impact as v_hi  # noqa: E402
import validate_schema as vs  # noqa: E402

MARKER_RE = re.compile(r"\[\[([A-Za-z0-9_-]+)(?:\|([A-Z][A-Z_,]*))?\]\]")
# Genuinely non-assertive line shapes: code fences (literal), table rows (data that must come from
# observations), blank. Tables remain a DISCLOSED residual (a prose claim smuggled into a table cell
# is not scanned; data belongs in observations and the manifest-coverage backstop still applies).
_ALWAYS_SKIP = re.compile(r"^\s*(\||```|$)")
# Prefixes that can still FRONT a load-bearing claim — strip and scan the claim inside: list bullets,
# headings (a heading can assert: "## Russia lost 60000 troops"), and blockquotes (Milestone-A P0
# review showed headings/blockquotes were smuggling unmarked assertions through the old skip-list).
_LIST_PREFIX = re.compile(r"^\s*([-*+]\s+|\d+\.\s+|#{1,6}\s+|>\s*)")
# Sentence split: after a terminator + whitespace. Grain is sentence-level (not line-level) so an
# unmarked claim co-located with an unrelated marked claim on one line is still caught (A7).
_SENT_SPLIT = re.compile(r"(?<=[.!?])\s+")


def _normalize_sentence(s: str) -> str:
    """Content key for the narrative-exemption allowlist: NFC, collapsed whitespace, stripped."""
    return unicodedata.normalize("NFC", " ".join(s.split())).strip()


def _sentence_hash(s: str) -> str:
    return "sha256:" + hashlib.sha256(_normalize_sentence(s).encode("utf-8")).hexdigest()


def required_status_tags(claim: dict) -> set:
    """The visible-status tags §7 requires for a cited claim (empty for a clean SUPPORTED FACT)."""
    tags = set()
    if claim.get("support_status") in {"UNVERIFIED", "THIN"}:
        tags.add(claim["support_status"])
    if claim.get("dispute_status") == "CONTESTED":
        tags.add("CONTESTED")
    if claim.get("freshness_status") == "STALE":
        tags.add("STALE")
    if claim.get("epistemic_type") in {"ASSUMPTION", "INFERENCE", "PROJECTION"}:
        tags.add(claim["epistemic_type"])
    return tags


def _assertion_candidates(prose: str):
    """Yield sentences that look like load-bearing assertions and carry NO marker. Sentence-grain
    with ATTACH-BACKWARD adjacency: a sentence is 'marked' if it contains a marker OR the next
    sentence begins with one (markers attach to the sentence they end) — so an unmarked claim
    co-located on a line with an unrelated marked claim is still caught (closes the A7 line-grain
    hole). List bullets are stripped + scanned; headings/code/blockquote/table rows are skipped
    (genuinely non-assertive). False positives are cheap in WARN mode and escapable in BLOCK mode."""
    for raw in prose.splitlines():
        line = raw.strip()
        if _ALWAYS_SKIP.match(line):
            continue
        line = _LIST_PREFIX.sub("", line)  # a bulleted claim is still a claim — scan inside the bullet
        chunks = [c.strip() for c in _SENT_SPLIT.split(line)]
        for i, c in enumerate(chunks):
            if MARKER_RE.search(c):
                continue  # this sentence carries a marker
            nxt = chunks[i + 1] if i + 1 < len(chunks) else ""
            if MARKER_RE.match(nxt):
                continue  # a marker begins the next sentence → it attaches backward to this one
            if c.endswith("?"):
                continue  # a question is not an assertion
            if len(c.split()) < 4:
                continue  # too short to be a load-bearing proposition
            yield c


def _high_impact_uncovered(prose, markers, live, triggers):
    """Yield prose sentences that assert a HIGH-IMPACT term but are NOT bound to a high-impact
    (hence refuter-contested) marked claim. Unlike the general unmarked-assertion scan, this fires
    even when the sentence CONTAINS a marker — because a marker for an *unrelated low-impact* claim
    must not launder a high-impact assertion hidden in the same sentence (cross-vendor review P0-4:
    '...road transport and Russian strikes killed 500 civilians. [[c1]]'). A high-impact term must be
    covered by a marker (in this sentence, or attaching backward from the next) whose claim the gate
    itself computes high_impact. NOT clearable by narrative_exemptions — you cannot exempt away a
    casualty/attribution/territory assertion."""
    for raw in prose.splitlines():
        line = raw.strip()
        if _ALWAYS_SKIP.match(line):
            continue
        line = _LIST_PREFIX.sub("", line)
        chunks = [c.strip() for c in _SENT_SPLIT.split(line)]
        for i, c in enumerate(chunks):
            asserted = v_hi.categories_for(v_hi.text_trigger_hits(c, triggers))
            if not asserted:
                continue
            # every high-impact CATEGORY asserted in the sentence must be covered by a marked claim
            # that is high-impact IN that category — a casualties marker does not launder a
            # co-located territorial-control assertion (cross-vendor re-review of P0-4).
            names = [n for n, _tag in MARKER_RE.findall(c)]
            nxt = MARKER_RE.match(chunks[i + 1]) if i + 1 < len(chunks) else None
            if nxt:
                names.append(nxt.group(1))
            covered = set()
            for name in names:
                mv = markers.get(name) if isinstance(markers, dict) else None
                claim = live.claims.get(mv.get("claim_id")) if isinstance(mv, dict) else None
                if claim is not None:
                    covered |= v_hi.claim_hi_categories(claim, triggers)
            if asserted - covered:
                yield c


def validate_output(analysis: dict, live, output_root: Path, block_unmarked: bool = False):
    hard, unmarked = [], []
    # 1. output-text binding (sha256 of raw bytes == output_hash). Missing file = cannot run (2).
    # CONFINE output_path to output_root: an absolute or `..`-traversing path could bind a file the
    # reviewer never saw, outside the controlled outputs/ tree — fail closed (location confinement).
    op = analysis.get("output_path", "")
    root = Path(output_root).resolve()
    out_path = (root / op)
    if Path(op).is_absolute() or not out_path.resolve().is_relative_to(root):
        return 2, [f"  output_path {op!r} escapes output_root (absolute or '..' traversal) — "
                   f"fail closed."]
    if not out_path.is_file():
        return 2, [f"  output file {analysis.get('output_path')!r} not found under {output_root} "
                   f"(cannot run, fail closed)."]
    if vs.file_content_hash(out_path) != analysis.get("output_hash"):
        hard.append(f"output_hash does not bind the prose: file {out_path.name} hashes to "
                    f"{vs.file_content_hash(out_path)!r}, manifest pins {analysis.get('output_hash')!r}")
    prose = out_path.read_text(encoding="utf-8")

    # 2. marker resolution (both directions — the A7 structural half)
    markers = analysis.get("claim_markers") if isinstance(analysis.get("claim_markers"), dict) else {}
    used = {}  # marker name -> set of status tags seen in prose
    for name, tagstr in MARKER_RE.findall(prose):
        used.setdefault(name, set())
        if tagstr:
            used[name] |= {t for t in tagstr.split(",") if t}
    for name in sorted(set(used) - set(markers)):
        hard.append(f"prose marker [[{name}]] does not resolve to a manifest claim_markers key")
    for name in sorted(set(markers) - set(used)):
        hard.append(f"manifest claim_marker {name!r} is never cited in the prose (extra manifest claim)")

    # 3. status preservation (§7): the prose marker must carry every required status tag
    for name in sorted(set(used) & set(markers)):
        mv = markers[name]
        claim = live.claims.get(mv.get("claim_id")) if isinstance(mv, dict) else None
        if claim is None:
            continue  # resolution is manifest_structural's job; skip here
        missing = required_status_tags(claim) - used[name]
        if missing:
            hard.append(f"marker [[{name}]] omits required visible status tag(s) {sorted(missing)} "
                        f"for claim {mv.get('claim_id')!r} (§7)")

    # 4. unmarked assertion-like sentences (the A7 semantic half) — WARN, or BLOCK in answer mode
    exemptions = set(analysis.get("narrative_exemptions") or [])
    for sentence in _assertion_candidates(prose):
        if _sentence_hash(sentence) in exemptions:
            continue  # declared non-load-bearing + reviewed (the escape)
        unmarked.append(sentence)

    # 5. high-impact prose laundering (P0-4): a high-impact assertion must be bound to a high-impact
    # marked claim — even if the sentence already carries a marker for some other (low-impact) claim.
    triggers = v_hi.trigger_set()
    hi_uncovered = sorted(set(_high_impact_uncovered(prose, markers, live, triggers)))

    findings = sorted(hard)
    findings += [f"high-impact assertion not bound to a high-impact (refuter-contested) marker — a "
                 f"committed answer may not launder it: {s!r}" for s in hi_uncovered]
    if block_unmarked:
        findings += [f"unmarked load-bearing assertion (answer BLOCKS; mark it, demote it, or add "
                     f"its hash to narrative_exemptions): {s!r}" for s in unmarked]
        code = 1 if findings else 0
    else:
        # in draft the general unmarked scan is a warn, but high-impact laundering always counts
        findings += [f"[warn] unmarked assertion-like sentence (heuristic; not counted in draft): "
                     f"{s!r}" for s in unmarked]
        code = 1 if (hard or hi_uncovered) else 0
    return code, findings

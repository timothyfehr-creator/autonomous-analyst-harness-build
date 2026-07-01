#!/usr/bin/env python3
"""WP-AL.7 — the WIRED DIFFERENT_MODEL refuter (the independence control, actually run).

`answer_build.py refuter` scaffolds a gate-scoped but UNSIGNED refuter (reviewer_class
SAME_MODEL_FRESH_CONTEXT, every verdict REVISE) that fails `verify.py --mode answer` closed until an
independent reviewer signs it (§10). Until now "an independent reviewer" meant a human editing YAML by
hand. THIS module wires the other half the Constitution already contemplates: a *different model*
(OpenAI) as the genuine adversarial reviewer, so a committed answer can be certified end-to-end without
the author's own model grading its own work.

What it does NOT do (by construction — the point is honesty, not a rubber stamp):
  - it CANNOT shrink scope: the reviewed claim/assessment sets and every binding hash come from
    `answer_build.scaffold_refuter` (gate-computed from the factbase). The model fills only JUDGMENT —
    each verdict's disposition + the five checks + the honest residue. A claim the model does not
    address stays REVISE and blocks the answer.
  - it CANNOT fake independence: reviewer_class is fixed to DIFFERENT_MODEL / reviewer to
    `openai:<model>`; it never self-signs HUMAN.
  - it CANNOT launder a non-answer: the assembled refuter is persisted only after it passes the schema
    AND `validate_refuter(answer_mode=True)` against the gate-computed scope — fail-closed (append →
    validate → drop). An honest REVISE/REJECT from the model is reported and BLOCKS the commit; that is
    the control working, not a failure.
  - high_impact per verdict is carried from the gate computation (authoritative), not the model's word.

Honest limitation (recorded in the run-manifest + refuter notes): a DIFFERENT_MODEL review of the SAME
curated context pack shares the author's blind spots (REVIEW_ADJUDICATION #2 / REVIEW_V3_COLD §15.3).
This raises the bar over same-model review; it is not a substitute for a human on a genuinely
high-stakes Tier-2 claim.

Reproducibility (global LLM-pipeline discipline): the refuter schema is CLOSED and carries no
model/prompt/temperature slot, so every reproducibility field (model, model version, base_url,
temperature, prompt_version, prompt+response hashes, token usage, code SHA, the raw response) is
written to a git-ignored sidecar run-manifest under `<root>/run_manifests/`. The API key is read from a
git-ignored file and is NEVER placed in the refuter, the run-manifest, a log line, or a command arg.

Network: `_post_chat` is the one seam that touches the network (tests monkeypatch it); the live call
needs the Bash sandbox disabled. `--dry-run` builds + prints the request and writes nothing.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import answer_build as ab  # noqa: E402
import validate_high_impact as v_hi  # noqa: E402
import validate_refuter as v_ref  # noqa: E402
import validate_schema as vs  # noqa: E402
import verify  # noqa: E402

Live = ab.Live

PROMPT_VERSION = "refuter-review-v2-defensibility"
DEFAULT_BASE_URL = "https://api.openai.com/v1"
CHECK_KEYS = ("displacement_check", "independence_check", "freshness_check",
              "observation_check", "reasoning_check")
_CHECK_VALUES = {"PASS", "FAIL", "NOT_APPLICABLE"}
_VERDICT_VALUES = {"SURVIVES", "REVISE", "DOWNGRADE", "REJECT"}
_VERDICT_ADVERSITY = {"REJECT": 0, "DOWNGRADE": 1, "REVISE": 2, "SURVIVES": 3}  # lower = more adverse
# normalize model check values so a mis-cased/synonym FAIL is preserved (never coerced to
# NOT_APPLICABLE, which would mask a failure under a SURVIVES verdict).
_CHECK_SYNONYMS = {"FAILED": "FAIL", "FAILS": "FAIL", "PASSED": "PASS", "PASSES": "PASS", "OK": "PASS",
                   "NA": "NOT_APPLICABLE", "N/A": "NOT_APPLICABLE", "NOT APPLICABLE": "NOT_APPLICABLE"}

SYSTEM_PROMPT = (
    "You are an INDEPENDENT reviewer — a different model from the author — checking whether a private "
    "research answer is DEFENSIBLE as worded. The bar is MATERIAL soundness, NOT perfection. Start from a "
    "presumption that a claim is usable and commit it (SURVIVES) UNLESS you find a MATERIAL problem.\n\n"
    "A claim has a MATERIAL problem (→ REVISE / DOWNGRADE / REJECT) only if it:\n"
    "  - OVER-CLAIMS beyond its cited evidence — asserts as settled fact something the evidence only "
    "reports, attributes, or weakly supports (e.g. states a belligerent or single-relayed claim as "
    "established fact);\n"
    "  - is UNSUPPORTED (not entailed by the cited quote) or CONTRADICTED by a cited source;\n"
    "  - is MIS-ATTRIBUTED — a one-sided/belligerent claim presented as independent fact; or\n"
    "  - is STALE (time-decayed, no longer current).\n"
    "A claim honestly WORDED to the confidence its evidence supports — attributed or hedged ('X reported', "
    "'a fire, satellite-confirmed, amid reported strikes') — is DEFENSIBLE and SHOULD survive, even if the "
    "underlying event is only reported or single-sourced.\n\n"
    "Do NOT block a claim for PRECISION or WORDING that could merely be improved (e.g. 'state-owned' vs "
    "'state-controlled', 'a primary source would strengthen it', 'could be more specific'). Put such "
    "observations in `unresolved_gaps` — they are NEVER by themselves grounds for a non-SURVIVES verdict.\n\n"
    "For each claim report these checks as PASS / FAIL / NOT_APPLICABLE (FAIL only for a MATERIAL problem):\n"
    "  - displacement_check: is the claim superseded or CONTRADICTED by a cited source? (a precision "
    "quibble is not a FAIL)\n"
    "  - independence_check: for a HIGH-IMPACT claim, does its wording assert MORE than its sourcing can "
    "bear (e.g. a belligerent/relayed claim stated as fact)? A well-attributed high-impact claim PASSES.\n"
    "  - freshness_check: is the claim stale / time-decayed? NOT_APPLICABLE for a timeless fact.\n"
    "  - observation_check: if a structured number/observation is cited, does it match the evidence? "
    "NOT_APPLICABLE if none is cited.\n"
    "  - reasoning_check: for an INFERENCE claim, is the inference valid? NOT_APPLICABLE for a direct FACT.\n\n"
    "A SURVIVES verdict may not carry a FAILed check. For a high-impact claim you SURVIVE, still include one "
    "well-formed disconfirming search you would run. You review the SAME curated evidence the author saw, so "
    "record honest residue (what you could not check independently) in unresolved_gaps.\n\n"
    "Respond with STRICT JSON only, no prose outside the JSON object."
)

# Auto-pick the "strongest" reviewer by parsing the version out of the model id, so a newer flagship
# (gpt-5.5 over gpt-5) is chosen even though this code predates it. Non-chat, size-reduced, and
# cost/specialized variants are filtered out; the pick is always logged and an explicit --model
# overrides, so a mis-rank is visible and correctable, never silent.
_NON_CHAT = ("embedding", "whisper", "tts", "dall-e", "dalle", "image", "moderation", "audio",
             "realtime", "transcribe", "-search", "search-api", "davinci", "babbage", "-ada", "curie",
             "codex", "-instruct", "computer-use", "omni-moderation", "sora")
_WEAKER = ("mini", "nano", "lite", "small", "micro")  # size/speed-reduced variants
_AUTO_AVOID = ("pro", "chat-latest", "-preview")  # cost/rolling/specialized — reachable via --model


def _sha(text: str) -> str:
    import hashlib
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _model_rank(name):
    """A sortable capability key parsed from the id: (family_tier, major, minor, is_bare_alias, -len).
    gpt-N.M flagships outrank the o-series for a general analytical review; a bare alias (gpt-5.5)
    outranks its dated snapshot. Returns None for an id that is not a recognizable chat model."""
    low = name.lower()
    gm = re.match(r"gpt-(\d+)(?:\.(\d+))?", low)
    om = re.match(r"o(\d+)", low)
    if gm:
        tier, major, minor = 2, int(gm.group(1)), int(gm.group(2) or 0)
    elif om:
        tier, major, minor = 1, int(om.group(1)), 0
    else:
        return None
    return (tier, major, minor, 0 if re.search(r"20\d\d", low) else 1, -len(name))


def pick_strongest_model(available):
    """Choose the strongest general chat/reasoning model from a live /v1/models id list: drop non-chat
    (embeddings/audio/image/etc.), size-reduced (mini/nano), and cost/specialized (pro/codex/chat-
    latest/preview) variants, then take the highest parsed version. Falls back to relaxing the
    weaker/auto-avoid filters if nothing full remains. Returns None if no chat model qualifies."""
    def strict(m):
        low = m.lower()
        return (isinstance(m, str) and _model_rank(m) is not None
                and not any(b in low for b in _NON_CHAT)
                and not any(b in low for b in _AUTO_AVOID)
                and not any(w in low for w in _WEAKER))
    cands = [m for m in available if strict(m)]
    if not cands:  # relax: only reduced/pro/etc. remain — still avoid the truly non-chat models
        cands = [m for m in available if isinstance(m, str) and _model_rank(m) is not None
                 and not any(b in m.lower() for b in _NON_CHAT)]
    return max(cands, key=_model_rank) if cands else None


# ---- request construction (pure) -------------------------------------------------------------------

def _claim_context(cid: str, live: Live) -> dict:
    """The evidence a reviewer needs for one claim: the claim itself + its active CHECKED assessments
    (stance, the exact supporting quote, credibility, source) — nothing the gate did not already pin."""
    claim = live.claims.get(cid) or {}
    supports = []
    for a in live.cea.values():
        if not isinstance(a, dict) or a.get("claim_id") != cid:
            continue
        sr = a.get("semantic_review")
        if not (isinstance(sr, dict) and sr.get("status") == "CHECKED"):
            continue
        loc = a.get("support_locator") if isinstance(a.get("support_locator"), dict) else {}
        supports.append({
            "assessment_id": a.get("id"), "stance": a.get("stance"),
            "information_credibility": a.get("information_credibility"),
            "quote": loc.get("quote"), "summary": a.get("support_summary"),
            "source_ids": [o.get("source_id") for o in (a.get("origin_chain") or [])
                           if isinstance(o, dict)],
        })
    return {
        "claim_id": cid, "text": claim.get("text"),
        "epistemic_type": claim.get("epistemic_type"), "topics": claim.get("topics"),
        "high_impact": bool(claim.get("high_impact")), "impact_category": claim.get("impact_category"),
        "support_status": claim.get("support_status"), "dispute_status": claim.get("dispute_status"),
        "freshness_status": claim.get("freshness_status"),
        "assessments": sorted(supports, key=lambda s: s.get("assessment_id") or ""),
    }


def build_review_request(ana: dict, live: Live, required_claims, required_ceas, root) -> dict:
    """Return the user-message payload the reviewer sees: the question, the exact reviewed answer text,
    and the pinned evidence for every gate-required claim. Pure (no I/O beyond reading the bound output
    file under `root`, which the manifest already hashes)."""
    root = Path(root)
    op = ana.get("output_path") or ""
    answer_text = None
    out_path = (root / op)
    if op and out_path.is_file():
        answer_text = out_path.read_text(encoding="utf-8")
    claims_ctx = [_claim_context(c, live) for c in sorted(required_claims)]
    return {
        "question": ana.get("question"),
        "answer_text": answer_text,
        "required_claim_ids": sorted(required_claims),
        "required_assessment_ids": sorted(required_ceas),
        "claims": claims_ctx,
        "instructions": {
            "return_json_shape": {
                "verdicts": [{"claim_id": "<one of required_claim_ids>",
                              "verdict": sorted(_VERDICT_VALUES),
                              **{k: sorted(_CHECK_VALUES) for k in CHECK_KEYS},
                              "notes": "<why>"}],
                "alternative_hypotheses": ["<competing explanations you considered>"],
                "disconfirming_searches": [{"query": "<what you would search>",
                                            "result": "<what it would/should show>"}],
                "unresolved_gaps": ["<what you could not verify against independent sources>"],
            },
            "rules": [
                "Return a verdict for EVERY id in required_claim_ids.",
                "SURVIVES requires that no check FAILed.",
                "For any high-impact claim, independence_check may not be NOT_APPLICABLE and you must "
                "include at least one well-formed disconfirming search (query + result).",
            ],
        },
    }


def build_chat_body(request: dict, model: str, temperature) -> dict:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(request, ensure_ascii=False, sort_keys=True)},
        ],
        "response_format": {"type": "json_object"},
    }
    if temperature is not None:
        body["temperature"] = temperature
    return body


# ---- the one network seam (monkeypatched in tests) -------------------------------------------------

class _NoAuthLeakRedirect(urllib.request.HTTPRedirectHandler):
    """Mirror requests' rebuild_auth: DROP the Authorization header when a redirect crosses to a
    different host, so the Bearer key is never forwarded off the endpoint it was issued for. Default
    urllib copies every header (incl. Authorization) onto a cross-host redirect — a key-exfiltration
    path if --base-url points at (or is redirected to) an unexpected host."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            from urllib.parse import urlsplit
            if urlsplit(req.full_url).hostname != urlsplit(newurl).hostname:
                new.remove_header("Authorization")
        return new


_OPENER = urllib.request.build_opener(_NoAuthLeakRedirect())


def _http_json(url: str, key: str, payload, timeout: int = 120):
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    method = "POST" if payload is not None else "GET"
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    # a custom opener that strips auth on a cross-host redirect (default urllib would forward the key)
    with _OPENER.open(req, timeout=timeout) as resp:  # noqa: S310 (host-checked; auth stripped cross-host)
        return json.loads(resp.read().decode("utf-8"))


def _post_chat(base_url: str, key: str, body: dict, timeout: int = 120) -> dict:
    """POST a chat-completions request. The SINGLE network call — tests monkeypatch this."""
    return _http_json(base_url.rstrip("/") + "/chat/completions", key, body, timeout)


def list_models(base_url: str, key: str) -> list:
    resp = _http_json(base_url.rstrip("/") + "/models", key, None)
    return sorted(m.get("id") for m in (resp.get("data") or []) if isinstance(m, dict) and m.get("id"))


def _review_call(post, base_url, key, request, model, temperature):
    """Call the model and parse its review. If the model rejects a non-default temperature (modern
    reasoning models only accept 1), retry ONCE at the model default. Returns
    (response, model_verdicts, residue, temperature_used). Raises urllib.error.URLError on a network
    failure, ValueError on an HTTP error or an unparseable review."""
    for temp in ([temperature, None] if temperature is not None else [None]):
        try:
            response = post(base_url, key, build_chat_body(request, model, temp))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace") if hasattr(e, "read") else str(e)
            if e.code == 400 and "temperature" in detail.lower() and temp is not None:
                continue  # retry at the model default temperature
            raise ValueError(f"OpenAI HTTP {e.code}: {detail}") from e
        return (response, *parse_model_verdicts(_chat_content(response)), temp)
    raise ValueError("temperature retry exhausted (model rejected every temperature tried)")


# ---- response parsing + assembly (pure) ------------------------------------------------------------

def _chat_content(response) -> str:
    """Extract the assistant message text from a chat-completions response (fail loud on shape)."""
    if not isinstance(response, dict):
        raise ValueError("model response is not a JSON object")
    choices = response.get("choices") or []
    if not choices or not isinstance(choices[0], dict):
        raise ValueError("model response has no choices")
    msg = choices[0].get("message") or {}
    content = msg.get("content") if isinstance(msg, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise ValueError("model response message.content is empty")
    return content


def parse_model_verdicts(content: str):
    """Parse the model's STRICT-JSON review into (verdicts_by_claim, residue). Tolerant of a JSON
    object wrapped in ```json fences; strict (isinstance-guarded, ValueError on bad shape) about the
    fields we consume — a non-object top level or a non-list field must not crash run_review. A claim
    with duplicate verdict entries resolves to the MOST ADVERSE (a REJECT is never hidden behind a
    later SURVIVES — the R3-P0-2 concern, enforced here because the wired path collapses to a dict)."""
    text = content.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.lstrip().lower().startswith("json"):
            text = text.lstrip()[4:]
    obj = json.loads(text)
    if not isinstance(obj, dict):
        raise ValueError("model review is not a JSON object")
    verdicts = {}
    vlist = obj.get("verdicts")
    for vd in (vlist if isinstance(vlist, list) else []):
        if not isinstance(vd, dict) or not vd.get("claim_id"):
            continue
        cid = vd["claim_id"]
        entry = {"verdict": vd.get("verdict"),
                 **{k: vd.get(k, "NOT_APPLICABLE") for k in CHECK_KEYS},
                 "notes": str(vd.get("notes") or "").strip() or None}
        prev = verdicts.get(cid)
        if prev is None or (_VERDICT_ADVERSITY.get(entry["verdict"], 99)
                            < _VERDICT_ADVERSITY.get(prev["verdict"], 99)):
            verdicts[cid] = entry  # keep the most adverse verdict for a repeated claim

    def _list(key):
        v = obj.get(key)
        return [x for x in v if x] if isinstance(v, list) else []
    residue = {"alternative_hypotheses": _list("alternative_hypotheses"),
               "disconfirming_searches": _list("disconfirming_searches"),
               "unresolved_gaps": _list("unresolved_gaps")}
    return verdicts, residue


def _norm_check(val) -> str:
    """Normalize a model-returned check to the closed enum; a mis-cased/synonym FAIL stays FAIL so the
    SURVIVES-cannot-carry-FAIL disposition guard still fires. Unrecognized/absent → NOT_APPLICABLE."""
    if not isinstance(val, str):
        return "NOT_APPLICABLE"
    v = val.strip().upper()
    v = _CHECK_SYNONYMS.get(v, v)
    return v if v in _CHECK_VALUES else "NOT_APPLICABLE"


def assemble_refuter(ana: dict, live: Live, as_of: str, model: str, model_verdicts: dict,
                     residue: dict, triggers=None):
    """Build the DIFFERENT_MODEL refuter from the gate-computed scaffold, overwriting only JUDGMENT
    with the model's review. Returns (refuter, floor, unaddressed) where `unaddressed` are required
    claims the model returned no verdict for (they stay REVISE and block the answer). Pure."""
    triggers = triggers if triggers is not None else v_hi.trigger_set()
    refuter, floor = ab.scaffold_refuter(ana, live, as_of, triggers=triggers)
    refuter["reviewer_class"] = "DIFFERENT_MODEL"
    refuter["reviewer"] = f"openai:{model}"
    unaddressed = []
    for vd in refuter["verdicts"]:
        cid = vd["claim_id"]
        mv = model_verdicts.get(cid)
        if not mv or mv.get("verdict") not in _VERDICT_VALUES:
            unaddressed.append(cid)   # no usable model verdict → keep the REVISE placeholder (blocks)
            continue
        vd["verdict"] = mv["verdict"]
        for k in CHECK_KEYS:
            vd[k] = _norm_check(mv.get(k))
        if mv.get("notes"):
            vd["notes"] = mv["notes"]
        # high_impact stays the gate-computed value scaffold_refuter set — never the model's word.
    refuter["alternative_hypotheses"] = [str(x) for x in (residue.get("alternative_hypotheses") or [])]
    refuter["disconfirming_searches"] = list(residue.get("disconfirming_searches") or [])
    refuter["unresolved_gaps"] = [str(x) for x in (residue.get("unresolved_gaps") or [])]
    return refuter, floor, unaddressed


# ---- reproducibility sidecar (pure; MUST NOT contain the key) --------------------------------------

def _code_version() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(Path(__file__).resolve().parent),
                             capture_output=True, text=True, timeout=10)
        if out.returncode == 0:
            return "git:" + out.stdout.strip()
    except Exception:
        pass
    return "git:unknown"


def build_run_manifest(analysis_id, refuter, model, base_url, temperature, request, responses,
                       as_of, votes=None, prompt_version=PROMPT_VERSION) -> dict:
    """The git-ignored reproducibility record for one (multi-sample) live review. Records
    model/version/prompt/temp, request+response hashes, EVERY raw sample response, the per-claim SURVIVES
    vote, and token usage — but NEVER the API key. `responses` may be a single dict (back-compat) or a
    list of the N sample responses."""
    if isinstance(responses, dict):
        responses = [responses]
    req_json = json.dumps(request, ensure_ascii=False, sort_keys=True)
    usages = [r.get("usage") for r in responses if isinstance(r, dict) and r.get("usage")]
    usage = {"total_tokens": sum((u.get("total_tokens") or 0) for u in usages),
             "per_sample": usages} if usages else None
    return {
        "kind": "refuter_review_run",
        "analysis_id": analysis_id,
        "refuter_id": refuter.get("id"),
        "as_of": as_of,
        "reviewer_class": "DIFFERENT_MODEL",
        "provider": "openai",
        "model": model,
        "model_version_reported": (responses[0] if responses else {} or {}).get("model"),
        "base_url": base_url,
        "temperature": temperature,
        "prompt_version": prompt_version,
        "samples": len(responses),
        "survive_votes": votes or {},
        "system_prompt_hash": _sha(SYSTEM_PROMPT),
        "request_hash": _sha(req_json),
        "response_hash": _sha(json.dumps(responses, ensure_ascii=False, sort_keys=True)),
        "response_ids": [(r or {}).get("id") for r in responses],
        "usage": usage,
        "code_version": _code_version(),
        "verdicts": [{"claim_id": v["claim_id"], "verdict": v["verdict"]}
                     for v in refuter.get("verdicts") or []],
        "raw_responses": responses,
    }


# ---- key handling (never logged, never persisted) --------------------------------------------------

def read_key(key_file: str | None) -> str:
    """Read the OpenAI key from a git-ignored file (dotenv `OPENAI_API_KEY=...` or a raw key), falling
    back to the OPENAI_API_KEY env var. Never returned in any artifact; never printed."""
    import os
    if key_file:
        p = Path(key_file)
        if not p.is_file():
            raise FileNotFoundError(f"key file {key_file!r} not found (put OPENAI_API_KEY there; it is "
                                    f"git-ignored under private/)")
        raw = p.read_text(encoding="utf-8")
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("OPENAI_API_KEY"):
                _, _, val = line.partition("=")
                val = val.strip().strip('"').strip("'")
                if val:
                    return val
        stripped = raw.strip()
        if stripped and "\n" not in stripped and "=" not in stripped:
            return stripped
        raise ValueError(f"no OPENAI_API_KEY found in {key_file!r}")
    env = os.environ.get("OPENAI_API_KEY")
    if env:
        return env
    raise ValueError("no key: pass --key-file <git-ignored file> or set OPENAI_API_KEY")


# ---- orchestration ---------------------------------------------------------------------------------

def _synthesize_samples(samples, threshold, hi_claims):
    """Combine N independent review samples into one verdict set, robust to the model's non-determinism.
    `samples`: list of (model_verdicts, residue). Per claim: SURVIVES iff its SURVIVES count >= threshold
    (taking a CLEAN SURVIVES sample's checks — no FAIL, and for a high-impact claim an independence_check
    that actually ran); otherwise the MOST-ADVERSE sample's verdict + aggregated concern notes. Residue
    (alternative_hypotheses / disconfirming_searches / unresolved_gaps) is unioned across samples.
    Returns (synthesized_verdicts, residue, votes) where votes[cid] = {survives, total, verdicts:[...]}."""
    n = len(samples)
    per_claim = {}
    for mv, _res in samples:
        for cid, vd in mv.items():
            per_claim.setdefault(cid, []).append(vd)
    synthesized, votes = {}, {}
    for cid, vds in per_claim.items():
        surv = [vd for vd in vds if vd.get("verdict") == "SURVIVES"]
        votes[cid] = {"survives": len(surv), "total": n, "verdicts": [vd.get("verdict") for vd in vds]}
        if len(surv) >= threshold:
            hi = cid in hi_claims

            def _clean(vd):
                if any(vd.get(k) == "FAIL" for k in CHECK_KEYS):
                    return False
                return not (hi and vd.get("independence_check") == "NOT_APPLICABLE")
            chosen = next((vd for vd in surv if _clean(vd)), surv[0])
            entry = dict(chosen)
            entry["notes"] = (f"survived {len(surv)}/{n} independent refuter samples. "
                              + (chosen.get("notes") or ""))[:2000]
        else:
            chosen = min(vds, key=lambda vd: _VERDICT_ADVERSITY.get(vd.get("verdict"), 99))
            entry = dict(chosen)
            # below threshold ⇒ NOT reliably certified. If the only PRESENT verdicts were SURVIVES (the
            # shortfall was OMISSION across samples, or an unrecognized verdict), still force a BLOCKING
            # verdict — a lucky partial SURVIVE must never slip through the gate (fail-open P0).
            if entry.get("verdict") not in {"REVISE", "DOWNGRADE", "REJECT"}:
                entry["verdict"] = "REVISE"
            concerns = "; ".join(sorted({vd["notes"] for vd in vds if vd.get("notes")}))
            entry["notes"] = (f"survived only {len(surv)}/{n} samples (below the {threshold}-of-{n} "
                              f"threshold; not reliably certified). Concerns: {concerns}")[:2000]
        synthesized[cid] = entry
    residue = {"alternative_hypotheses": [], "disconfirming_searches": [], "unresolved_gaps": []}
    for key in residue:
        seen = set()
        for _mv, r in samples:
            for x in (r.get(key) or []):
                k = json.dumps(x, sort_keys=True) if isinstance(x, (dict, list)) else str(x)
                if k not in seen:
                    seen.add(k)
                    residue[key].append(x)
    return synthesized, residue, votes


def run_review(root: Path, analysis_id: str, as_of: str, model: str, key: str,
               base_url: str = DEFAULT_BASE_URL, temperature=0.0, dry_run: bool = False,
               post=_post_chat, samples: int = 1, survive_threshold: int = 1):
    """Load → build request → (call model) → assemble → validate → persist fail-closed + run-manifest.
    Returns (exit_code, lines). `post` is injectable for tests. dry_run stops before the network call."""
    root = Path(root)
    live = Live(root)
    lines = []
    ana = live.analyses.get(analysis_id)
    if ana is None:
        return 2, [f"[refuter_review] analysis {analysis_id!r} not found — fail closed."]
    if ana.get("lifecycle") != "ANSWER":
        return 2, [f"[refuter_review] analysis lifecycle is {ana.get('lifecycle')!r}; a committed "
                   f"answer requires ANSWER — fail closed."]
    existing = live.refuter_for_analysis(analysis_id)
    required_claims, required_ceas, floor = verify._gate_computed_refuter_scope(ana, live)
    request = build_review_request(ana, live, required_claims, required_ceas, root)
    lines.append(f"[refuter_review] analysis {analysis_id!r}: gate scope = "
                 f"{len(required_claims)} claim(s) / {len(required_ceas)} assessment(s); model={model}")
    if floor:
        lines += [f"[refuter_review] support floor: {x}" for x in floor]

    if dry_run:
        lines.append("[refuter_review] --dry-run: no network call, nothing written. Request follows:")
        lines.append(json.dumps(build_chat_body(request, model, temperature), indent=2,
                                ensure_ascii=False))
        return 0, lines

    # clobber refusal gates only the WRITE path: never overwrite an existing INDEPENDENT review (only
    # the SAME_MODEL_FRESH_CONTEXT scaffold is replaceable).
    if existing is not None and existing.get("reviewer_class") != "SAME_MODEL_FRESH_CONTEXT":
        return 1, lines + [f"[refuter_review] a SIGNED refuter ({existing.get('id')!r}, "
                           f"reviewer_class={existing.get('reviewer_class')!r}) already binds "
                           f"{analysis_id!r}; refusing to clobber an existing independent review."]

    # the support floor is a data precondition independent of the review: an unmet floor means a
    # committed answer can never pass (answer_check re-checks it), so fail closed BEFORE spending a paid
    # call rather than sign a refuter the answer still cannot use (the misleading-OK gap).
    if floor:
        return 1, lines + ["[refuter_review] support floor UNMET — a committed answer cannot pass "
                           "regardless of the review, so no paid call is made. Add a credibility-scored "
                           "SUPPORTS assessment (fact.py) for the floored claim(s), then re-run."]

    # multi-sample: call the model N times and decide per claim by a threshold (robust to the model's
    # non-determinism). N=1 with threshold 1 is the single-shot path. This is the honest opposite of
    # re-rolling — it requires CONSISTENT survival, so a lucky single SURVIVE cannot slip through.
    n = max(1, samples)
    threshold = min(max(1, survive_threshold), n)
    sample_results, raw_responses = [], []
    for i in range(n):
        try:
            response, mv, residue_i, temp_used = _review_call(
                post, base_url, key, request, model, temperature)
        except urllib.error.URLError as e:  # HTTPError → ValueError inside _review_call
            return 2, lines + [f"[refuter_review] network unavailable ({e}); the live call needs the "
                               f"Bash sandbox disabled."]
        except (ValueError, TypeError, AttributeError, json.JSONDecodeError) as e:
            return 2, lines + [f"[refuter_review] sample {i + 1}/{n}: {e}"]
        if temp_used != temperature and i == 0:
            lines.append(f"[refuter_review] model rejected temperature={temperature}; used the model "
                         f"default instead (recorded as temperature={temp_used}).")
        temperature = temp_used
        sample_results.append((mv, residue_i))
        raw_responses.append(response)

    triggers = v_hi.trigger_set()
    hi_claims = {cid for cid in required_claims
                 if v_hi.compute_high_impact(live.claims.get(cid) or {}, triggers)[0]
                 or (live.claims.get(cid) or {}).get("high_impact") is True}
    model_verdicts, residue, votes = _synthesize_samples(sample_results, threshold, hi_claims)
    if n > 1:
        lines.append(f"[refuter_review] {n} samples (threshold {threshold}/{n}); SURVIVES votes: "
                     + ", ".join(f"{c}={v['survives']}/{v['total']}" for c, v in sorted(votes.items())))

    refuter, floor2, unaddressed = assemble_refuter(ana, live, as_of, model, model_verdicts, residue)
    if unaddressed:
        lines.append(f"[refuter_review] model returned no usable verdict for {sorted(unaddressed)} — "
                     f"those stay REVISE and will block the commit (honest: an unaddressed claim is "
                     f"not a certified one).")

    # persist fail-closed + ATOMIC: append the new refuter ALONGSIDE any scaffold, VALIDATE FIRST, and
    # only touch side effects once the refuter state is finalized — so no unvalidated refuter is ever
    # left persisted, a failed review never destroys the scaffold, and a manifest-write failure cannot
    # orphan a refuter.
    rpath = root / "factbase" / "refuters.yaml"
    doc = ab._append_record(rpath, "refuters", refuter)
    sc, sf = vs.validate_file(rpath)
    rc, rf = (0, [])
    if sc == 0:
        rc, rf = v_ref.validate_refuter(refuter, ana, Live(root), answer_mode=True,
                                        required_ceas=required_ceas, required_claims=required_claims)
    if sc != 0 or rc != 0:
        ab._drop_record(rpath, "refuters", refuter["id"], doc)  # scaffold (if any) left intact
        _safe_write_run_manifest(root, analysis_id, refuter, model, base_url, temperature,
                                 request, raw_responses, as_of, lines, votes=votes)  # honest residue
        verdicts = ", ".join(f"{v['claim_id']}={v['verdict']}" for v in refuter["verdicts"])
        why = "the refuter fails schema" if sc != 0 else \
            f"the independent review did NOT certify (verdicts: {verdicts})"
        return (sc or 1), lines + (sf if sc != 0 else [f"  [refuter] {x}" for x in rf]) + [
            f"[refuter_review] NOT persisted — {why}. A committed answer requires every claim to "
            f"SURVIVE the refuter across the sample threshold; this is the control working, not a bug. "
            f"The honest review is recorded in the run-manifest."]
    # certified → reproducibility is REQUIRED before we finalize: if the manifest cannot be written we
    # refuse to persist a certification we cannot reproducibly record (fail closed).
    if _safe_write_run_manifest(root, analysis_id, refuter, model, base_url, temperature,
                                request, raw_responses, as_of, lines, votes=votes) is None:
        ab._drop_record(rpath, "refuters", refuter["id"], doc)
        return 2, lines + ["[refuter_review] could not write the reproducibility run-manifest — "
                           "refusing to persist a certification we cannot reproducibly record."]
    if existing is not None:  # certified → drop the replaceable scaffold so exactly one refuter binds
        _remove_refuter(rpath, existing.get("id"))
    lines.append(f"[refuter_review] OK — {refuter['id']!r} signed DIFFERENT_MODEL ({model}); every "
                 f"required claim SURVIVES across {threshold}/{n} samples. Run `verify.py --mode answer "
                 f"--analysis {analysis_id}` to commit the answer.")
    return 0, lines


def _remove_refuter(rpath: Path, rec_id: str):
    doc = vs.load_yaml_strict(rpath) if rpath.is_file() else None
    if not doc:
        return
    doc["refuters"] = [r for r in doc.get("refuters") or [] if r.get("id") != rec_id]
    import yaml
    rpath.write_text(yaml.safe_dump(doc, sort_keys=False, allow_unicode=True))


def _write_run_manifest(root: Path, analysis_id, refuter, model, base_url, temperature, request,
                        responses, as_of, votes=None) -> Path:
    manifest = build_run_manifest(analysis_id, refuter, model, base_url, temperature, request,
                                  responses, as_of, votes=votes)
    d = root / "run_manifests"
    d.mkdir(parents=True, exist_ok=True)
    safe_as_of = as_of.replace(":", "").replace("/", "")
    # disambiguate by the RESPONSES digest so a re-run at the same --as-of (e.g. a first blocked review
    # then a passing one) writes a distinct file and never overwrites the earlier honest record.
    resp_tag = _sha(json.dumps(responses, ensure_ascii=False, sort_keys=True))[7:15]
    mpath = d / f"refuter-{analysis_id}-{safe_as_of}-{resp_tag}.json"
    mpath.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return mpath


def _is_git_ignored(path: Path) -> bool:
    """True iff `path` is git-ignored (so the manifest's raw model output won't be committed). Best-effort:
    returns False on any error / non-repo, so the caller WARNS rather than falsely reassures."""
    try:
        out = subprocess.run(["git", "check-ignore", "-q", str(path)],
                             cwd=str(Path(path).resolve().parent), capture_output=True, timeout=10)
        return out.returncode == 0
    except Exception:
        return False


def _safe_write_run_manifest(root, analysis_id, refuter, model, base_url, temperature, request,
                             responses, as_of, lines, votes=None):
    """Write the reproducibility sidecar; on any OSError append a warning and return None (never
    crash — the caller decides whether a missing manifest is fatal). Keeps the persist path from
    letting a manifest-write failure orphan a refuter. The 'git-ignored' assurance is CHECKED, not
    assumed — the manifest holds raw model output over private claims and must not be committed."""
    try:
        mpath = _write_run_manifest(root, analysis_id, refuter, model, base_url, temperature,
                                    request, responses, as_of, votes=votes)
        tag = "git-ignored" if _is_git_ignored(mpath) else \
            "WARNING: NOT git-ignored — holds raw model output, do NOT commit it"
        lines.append(f"[refuter_review] run-manifest (no key; {tag}): {mpath}")
        return mpath
    except OSError as e:
        lines.append(f"[refuter_review] WARNING — could not write run-manifest: {e}")
        return None


def _cmd_review(args) -> int:
    if args.list_models:
        try:
            key = read_key(args.key_file)
            for m in list_models(args.base_url, key):
                print(m)
            return 0
        except (urllib.error.URLError, ValueError, FileNotFoundError) as e:
            print(f"[refuter_review] --list-models failed: {e}", file=sys.stderr)
            return 2
    key, model = "", args.model
    if not args.dry_run:
        try:
            key = read_key(args.key_file)
        except (ValueError, FileNotFoundError) as e:
            print(f"[refuter_review] {e}", file=sys.stderr)
            return 2
        if model is None:  # owner chose "strongest automatically"
            try:
                available = list_models(args.base_url, key)
            except urllib.error.URLError as e:
                print(f"[refuter_review] could not list models to auto-pick ({e}); pass --model <id>.",
                      file=sys.stderr)
                return 2
            model = pick_strongest_model(available)
            if model is None:
                print(f"[refuter_review] no chat model among {len(available)} available; pass --model.",
                      file=sys.stderr)
                return 2
            print(f"[refuter_review] auto-selected strongest model {model!r} from {len(available)} "
                  f"available: {', '.join(sorted(available))}", file=sys.stderr)
        print(f"[refuter_review] COST: this makes {args.samples} paid OpenAI API call(s) (multi-sample "
              f"gate, ~a few US cents each). Token usage is written to the run-manifest.", file=sys.stderr)
    else:
        model = model or "<auto: strongest at run time>"
    temperature = None if args.no_temperature else args.temperature
    code, lines = run_review(Path(args.root), args.analysis, args.as_of, model, key,
                             base_url=args.base_url, temperature=temperature, dry_run=args.dry_run,
                             samples=args.samples, survive_threshold=args.survive_threshold)
    print("\n".join(lines))
    return code


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="wired DIFFERENT_MODEL refuter review (OpenAI) — AL.7")
    p.add_argument("--analysis", required=True)
    p.add_argument("--root", default=".")
    p.add_argument("--as-of", required=True)
    p.add_argument("--model", default=None,
                   help="OpenAI model id; omit to auto-pick the strongest available (--list-models to see)")
    p.add_argument("--key-file", default="private/.env",
                   help="git-ignored file holding OPENAI_API_KEY (dotenv or raw). Never logged.")
    p.add_argument("--base-url", default=DEFAULT_BASE_URL)
    p.add_argument("--temperature", type=float, default=0.0)
    p.add_argument("--no-temperature", action="store_true",
                   help="omit temperature (some models reject a non-default value)")
    p.add_argument("--samples", type=int, default=5,
                   help="independent review samples for the majority-vote gate (default 5)")
    p.add_argument("--survive-threshold", type=int, default=3, dest="survive_threshold",
                   help="a claim must SURVIVE in >= this many of --samples to commit (default 3 of 5, a "
                        "majority — inclusive bar; raise for stricter)")
    p.add_argument("--dry-run", action="store_true", help="build+print the request; no call, no write")
    p.add_argument("--list-models", action="store_true", help="list models the key can access, then exit")
    p.set_defaults(fn=_cmd_review)
    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())

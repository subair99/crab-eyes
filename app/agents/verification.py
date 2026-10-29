"""Verification: a deterministic date filter, then a Super pass for entity match and contradictions.

Findings that fail are kept and marked (rejected_reason), never silently dropped.
"""
from __future__ import annotations

import json

from app.agents._prompts import prompt
from app.config import get_settings
from app.gate.dates import after_cutoff
from app.llm.router import chat_json, items
from app.llm.trace import Trace
from app.schemas import Claims, Finding


async def verify(claims: Claims, findings: list[Finding], trace: Trace) -> list[Finding]:
    cutoff = get_settings().evidence_end_date
    for f in findings:
        if f.source and not f.self_evident and after_cutoff(
                f.source.published_date, cutoff, f.source.snippet + " " + f.summary):
            f.rejected_reason = f"published after cutoff {cutoff}"

    candidates = [(i, f) for i, f in enumerate(findings)
                  if f.rejected_reason is None and f.source and not f.self_evident]
    if candidates:
        payload = {
            "claims": claims.model_dump(exclude={"raw_text"}),
            "findings": [{"index": i, "check": f.check, "summary": f.summary,
                          "url": f.source.url, "snippet": f.source.snippet} for i, f in candidates],
        }
        data = await chat_json("verifier", [{"role": "system", "content": prompt("verification")},
                                            {"role": "user", "content": json.dumps(payload)}], trace, temperature=0)
        results = [r for r in items(data, "results")
                   if isinstance(r, dict) and isinstance(r.get("index"), int) and 0 <= r["index"] < len(findings)]
        # Pass 1: wrong company or out of date.
        for r in results:
            f = findings[r["index"]]
            f.entity_match = r.get("entity_match", "uncertain")
            if f.entity_match == "mismatch":
                f.rejected_reason = "about a different company"
            elif r.get("still_current") is False:
                f.rejected_reason = "no longer current"
        # Pass 2: contradictions count only if the contradicting finding survived pass 1 and actually says something.
        for r in results:
            f = findings[r["index"]]
            if f.rejected_reason or f.kind == "neutral":
                continue
            live = [j for j in (r.get("contradicted_by") or [])
                    if isinstance(j, int) and 0 <= j < len(findings) and j != r["index"]
                    and findings[j].rejected_reason is None and findings[j].kind != "neutral"]
            if live:
                f.rejected_reason = f"contradicted by finding(s) {live}"

    for f in findings:
        f.verified = f.rejected_reason is None and (
            f.self_evident or f.source is not None or f.check in ("ponzi_maths", "user_evidence"))
    return findings
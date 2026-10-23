"""Verification: a deterministic date filter, then a Super pass for entity match and contradictions.

Findings that fail are kept and marked (rejected_reason), never silently dropped.
"""
from __future__ import annotations

import json

from app.agents._prompts import prompt
from app.config import get_settings
from app.gate.dates import after_cutoff
from app.llm.router import chat_json
from app.llm.trace import Trace
from app.schemas import Claims, Finding


async def verify(claims: Claims, findings: list[Finding], trace: Trace) -> list[Finding]:
    cutoff = get_settings().evidence_end_date
    for f in findings:
        if f.source and after_cutoff(f.source.published_date, cutoff):
            f.rejected_reason = f"published after cutoff {cutoff}"

    candidates = [(i, f) for i, f in enumerate(findings) if f.rejected_reason is None and f.source]
    if candidates:
        payload = {
            "claims": claims.model_dump(exclude={"raw_text"}),
            "findings": [{"index": i, "check": f.check, "summary": f.summary,
                          "url": f.source.url, "snippet": f.source.snippet} for i, f in candidates],
        }
        data = await chat_json("verifier", [{"role": "system", "content": prompt("verification")},
                                            {"role": "user", "content": json.dumps(payload)}], trace, temperature=0)
        for r in data.get("results", []):
            f = findings[r["index"]]
            f.entity_match = r.get("entity_match", "uncertain")
            if f.entity_match == "mismatch":
                f.rejected_reason = "about a different company"
            elif r.get("still_current") is False:
                f.rejected_reason = "no longer current"
            elif r.get("contradicted_by"):
                f.rejected_reason = f"contradicted by finding(s) {r['contradicted_by']}"

    for f in findings:
        # Maths and user-supplied evidence have no web source; they are verified by construction.
        f.verified = f.rejected_reason is None and (f.source is not None or f.check in ("ponzi_maths", "user_evidence"))
    return findings

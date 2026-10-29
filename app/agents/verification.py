"""Verification: a deterministic date filter, a company-name check, then a Super pass for entity match
and contradictions.

Findings that fail are kept and marked (rejected_reason), never silently dropped.
"""
from __future__ import annotations

import json
import re

from app.agents._prompts import prompt
from app.config import get_settings
from app.gate.dates import after_cutoff
from app.llm.router import chat_json, items
from app.llm.trace import Trace
from app.schemas import Claims, Finding

# Words too common in company names to identify one on their own.
GENERIC = {
    "limited", "ltd", "plc", "nig", "nigeria", "nigerian", "the", "and", "for", "of",
    "fund", "funds", "investment", "investments", "invest", "capital", "asset", "assets", "wealth",
    "management", "managers", "manager", "finance", "financial", "services", "service", "bank", "trust",
    "holdings", "group", "company", "partners", "ventures", "solutions", "technologies", "technology",
    "global", "international", "africa", "office", "federal", "government", "exchange", "trading",
    "digital", "platform", "cooperative", "society", "network", "club", "plan", "scheme",
}


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def mentions_company(f: Finding, names: list[str]) -> bool:
    """True if the source names the company: its full name, or a distinctive word from it as a whole word."""
    if not names:
        return True  # nothing to match against (e.g. a pitch with only a link)
    text = " ".join([f.summary, f.source.snippet if f.source else "", f.source.title if f.source else ""]).lower()
    text_words = set(_words(text))
    for name in names:
        if name.lower().strip() and name.lower().strip() in text:
            return True
        distinctive = [w for w in _words(name) if len(w) >= 3 and w not in GENERIC]
        if distinctive and any(w in text_words for w in distinctive):
            return True
    return False


async def verify(claims: Claims, findings: list[Finding], trace: Trace) -> list[Finding]:
    cutoff = get_settings().evidence_end_date
    for f in findings:
        if f.source and not f.self_evident and after_cutoff(
                f.source.published_date, cutoff, f.source.snippet + " " + f.summary):
            f.rejected_reason = f"published after cutoff {cutoff}"

    # Complaints and footprint red flags must actually be about this company.
    for f in findings:
        if (f.rejected_reason is None and f.kind == "red_flag" and not f.official and not f.self_evident
                and f.check in ("voices", "people", "footprint") and not mentions_company(f, claims.company_names)):
            f.rejected_reason = "does not mention the company"

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
            if f.rejected_reason or f.self_evident:
                continue
            f.entity_match = r.get("entity_match", "uncertain")
            if f.entity_match == "mismatch":
                f.rejected_reason = "about a different company"
            elif r.get("still_current") is False:
                f.rejected_reason = "no longer current"
        # Pass 2: contradictions count only if the contradicting finding survived pass 1 and actually says something.
        for r in results:
            f = findings[r["index"]]
            if f.rejected_reason or f.kind == "neutral" or f.self_evident:
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
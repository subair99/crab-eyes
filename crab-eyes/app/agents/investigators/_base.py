"""Shared helper: search with Tavily, then ask Super to turn results into findings."""
from __future__ import annotations

import json
from urllib.parse import urlparse

from app.agents._prompts import prompt
from app.llm.router import chat_json
from app.llm.trace import Trace
from app.schemas import Finding, Source
from app.tools import tavily

OFFICIAL_DOMAINS = ("sec.gov.ng", "cbn.gov.ng", "fccpc.gov.ng", "cac.gov.ng", "sec.gov", "fca.org.uk")


def is_official(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return any(host == d or host.endswith("." + d) for d in OFFICIAL_DOMAINS)


async def search_and_judge(check: str, prompt_name: str, queries: list[str], trace: Trace, **search_kw) -> list[Finding]:
    results: list[dict] = []
    for q in queries:
        results.extend(await tavily.search(q, trace=trace, **search_kw))
    if not results:
        return []
    by_url = {r["url"]: r for r in results}
    payload = [{"url": r["url"], "title": r.get("title", ""), "content": r.get("content", "")[:1500],
                "published_date": r.get("published_date")} for r in by_url.values()]
    data = await chat_json("investigator", [{"role": "system", "content": prompt(prompt_name)},
                                            {"role": "user", "content": json.dumps(payload)}], trace, temperature=0)
    findings = []
    for item in data.get("findings", []):
        url = item.get("url", "")
        r = by_url.get(url, {})
        findings.append(Finding(
            check=check,
            kind=item.get("kind", "neutral"),
            summary=item.get("summary", ""),
            source=Source(url=url, title=r.get("title", ""), published_date=r.get("published_date"),
                          snippet=r.get("content", "")[:300]) if url else None,
            official=is_official(url),
            independence_key=urlparse(url).netloc.lower(),
            details_match=item.get("details_match"),
        ))
    return findings

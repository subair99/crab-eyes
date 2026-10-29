"""Thin async wrappers around Tavily. Every call is logged in the trace.

Search options used: include_domains, start_date / end_date (YYYY-MM-DD). EVIDENCE_END_DATE applies to all searches.
"""
from __future__ import annotations

from functools import lru_cache

from tavily import AsyncTavilyClient

from app.config import get_settings
from app.llm.trace import Trace


@lru_cache
def _client() -> AsyncTavilyClient:
    return AsyncTavilyClient(api_key=get_settings().tavily_api_key)


async def search(query: str, trace: Trace, max_results: int = 5, **kwargs) -> list[dict]:
    end_date = get_settings().evidence_end_date
    if end_date and "end_date" not in kwargs:
        kwargs["end_date"] = end_date
        kwargs.setdefault("topic", "news")  # news results carry publication dates, which the cut-off needs
    resp = await _client().search(query, max_results=max_results, **kwargs)
    results = resp.get("results", [])
    trace.add_tool("tavily.search", query=query, results=len(results), **{k: v for k, v in kwargs.items()
                                                                          if k in ("end_date", "include_domains")})
    return results


async def extract(urls: list[str], trace: Trace) -> list[dict]:
    resp = await _client().extract(urls)
    results = resp.get("results", [])
    trace.add_tool("tavily.extract", urls=urls, results=len(results))
    return results


async def crawl(url: str, trace: Trace, **kwargs) -> list[dict]:
    resp = await _client().crawl(url, **kwargs)
    results = resp.get("results", [])
    trace.add_tool("tavily.crawl", url=url, results=len(results))
    return results

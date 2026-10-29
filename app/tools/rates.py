"""Live benchmark rates for the Ponzi maths.

TODO: fetch the latest Nigerian T-bill stop rates with tools.tavily.search (e.g. include_domains=["cbn.gov.ng"])
and parse the 364-day rate. Until then, set BENCHMARK_ANNUAL_RATE in .env from a source you checked that day.
Never hard-code a rate in the repo.
"""
from __future__ import annotations

from app.tools.calculator import benchmark


async def current_tbill_rate() -> float | None:
    return benchmark()

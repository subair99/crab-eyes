"""Ponzi maths in code, so a model's arithmetic never reaches the screen."""
from __future__ import annotations

import os

from app.gate.policy import load_thresholds


def annualise(rate: float, period_months: float) -> float:
    """Compound a return of `rate` per `period_months` into a yearly rate. 0.30 monthly -> ~22.30 (2,230%)."""
    if period_months <= 0:
        raise ValueError("period_months must be positive")
    return (1 + rate) ** (12 / period_months) - 1


def benchmark() -> float | None:
    value = os.environ.get("BENCHMARK_ANNUAL_RATE", "").strip()
    return float(value) if value else None


def fails(rate: float, period_months: float, thresholds: dict | None = None, bench: float | None = None) -> bool:
    t = (thresholds or load_thresholds())["maths"]
    yearly = annualise(rate, period_months)
    bench = benchmark() if bench is None else bench
    over_cap = yearly > t["max_plausible_annual_return"]
    over_bench = bench is None or yearly > t["benchmark_multiple"] * bench
    return over_cap and over_bench


def maths_fails(claims) -> bool:
    rate = getattr(claims, "promised_return", None)
    months = getattr(claims, "return_period_months", None)
    return bool(rate is not None and months and fails(rate, months))


def describe(rate: float, period_months: float, bench: float | None = None) -> str:
    yearly = annualise(rate, period_months)
    bench = benchmark() if bench is None else bench
    period = "a month" if period_months == 1 else f"every {period_months:g} months"
    text = f"{rate:.0%} {period} compounds to {yearly:,.0%} a year."
    if bench is not None:
        text += f" Nigerian T-bills currently pay about {bench:.0%} a year."
    return text

"""The policy gate: rules in code decide which verdict may be shown. The model never does.

High risk        : >= 2 independent verified red flags incl. one official with a confirmed entity match;
                   or the maths fails plus >= 1 other independent verified red flag.
Looks legitimate : a verified, confirmed register match whose details match the site and contacts,
                   and no verified official red flag.
Check first      : verified red flags, but neither rule above holds (and enough sources).
Not enough       : too few verified sources, or nothing else applies.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

THRESHOLDS = Path(__file__).with_name("thresholds.yaml")


def load_thresholds() -> dict:
    return yaml.safe_load(THRESHOLDS.read_text())


@dataclass
class GateInput:
    findings: list[Any]                 # app.schemas.Finding, or any object with the same attributes
    maths_failed: bool = False
    thresholds: dict = field(default_factory=load_thresholds)


def _get(f, name, default=None):
    return getattr(f, name, default) if not isinstance(f, dict) else f.get(name, default)


def _verdict(value: str):
    try:
        from app.schemas import Verdict
        return Verdict(value)
    except ImportError:  # lets the gate run without pydantic installed
        return value


def decide(inp: GateInput):
    t = inp.thresholds
    verified = [f for f in inp.findings if _get(f, "verified")]
    sources = {_get(f, "independence_key") or id(f) for f in verified}
    red = [f for f in verified if _get(f, "kind") == "red_flag"]
    red_non_maths = [f for f in red if _get(f, "check") != "ponzi_maths"]
    independent_red = {_get(f, "independence_key") or id(f) for f in red}
    official_red = [f for f in red if _get(f, "official") and _get(f, "entity_match") == "confirmed"]
    register_ok = [
        f for f in verified
        if _get(f, "kind") == "register_match" and _get(f, "official")
        and _get(f, "entity_match") == "confirmed" and _get(f, "details_match") is True
    ]

    reasons: list[str] = []
    if len(independent_red) >= t["min_independent_red_flags"] and official_red:
        reasons = [_get(f, "summary") for f in official_red[:1]] + [
            _get(f, "summary") for f in red if f not in official_red[:1]][:2]
        return _verdict("high_risk"), reasons
    if inp.maths_failed and red_non_maths:
        reasons = [_get(f, "summary") for f in red if _get(f, "check") == "ponzi_maths"][:1] + [
            _get(f, "summary") for f in red_non_maths][:2]
        return _verdict("high_risk"), reasons
    if register_ok and not official_red:
        return _verdict("looks_legitimate"), [_get(register_ok[0], "summary")]
    if len(sources) < t["min_verified_sources"]:
        return _verdict("not_enough_evidence"), ["Too few verified sources to judge."]
    if red:
        return _verdict("check_first"), [_get(f, "summary") for f in red][:3]
    return _verdict("not_enough_evidence"), ["No verified red flags and no confirmed register entry."]

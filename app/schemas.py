"""Shared data shapes passed between pipeline stages and returned by the API."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Claims(BaseModel):
    company_names: list[str] = []
    promised_return: float | None = None        # decimal, e.g. 0.40 for 40%
    return_period_months: float | None = None   # e.g. 1 for "every month"
    regulator_claims: list[str] = []            # e.g. ["SEC approved"]
    people: list[str] = []
    urls: list[str] = []
    other_claims: list[str] = []
    language: str | None = None                 # e.g. "pcm" for Nigerian Pidgin
    raw_text: str = ""


class Source(BaseModel):
    url: str
    title: str = ""
    published_date: str | None = None           # YYYY-MM-DD when known
    snippet: str = ""


class Finding(BaseModel):
    check: Literal["regulator", "ponzi_maths", "footprint", "people", "voices", "user_evidence"]
    kind: Literal["red_flag", "register_match", "neutral"]
    summary: str
    source: Source | None = None
    official: bool = False                      # from a regulator or official register
    independence_key: str = ""                  # findings sharing a key are not independent (e.g. same domain)
    entity_match: Literal["confirmed", "uncertain", "mismatch", "n/a"] = "n/a"
    details_match: bool | None = None           # register entry matches site and contacts
    verified: bool = False                      # set by the verification step
    rejected_reason: str | None = None          # set when verification rejects it
    self_evident: bool = False 


class Explanation(BaseModel):
    label: Literal["licensed_legitimate", "real_but_unlicensed", "ponzi_or_fraud", "impersonation"]
    probability: float
    distinguishing_evidence: str = ""


class ClaimVsRecord(BaseModel):
    claim: str
    record: str
    source_url: str | None = None
    mismatch: bool = False


class Verdict(str, Enum):
    HIGH_RISK = "high_risk"
    CHECK_FIRST = "check_first"
    LOOKS_LEGITIMATE = "looks_legitimate"
    NOT_ENOUGH_EVIDENCE = "not_enough_evidence"


class Dossier(BaseModel):
    id: str
    claims: Claims
    plan: list[str] = []
    findings: list[Finding] = []
    explanations: list[Explanation] = []
    claims_vs_records: list[ClaimVsRecord] = []
    verdict: Verdict
    reasons: list[str] = []
    what_would_change_my_mind: list[str] = []
    trace: list[dict] = []
    cost_usd: float = 0.0
    disclaimer: str = Field(
        default="Crab Eyes shows evidence, not financial advice. 'High risk' is a rating, not a legal finding."
    )

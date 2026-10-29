"""Deterministic date checks used by the verification step and the CBEX re-run."""
from __future__ import annotations

import re
from datetime import date
from email.utils import parsedate_to_datetime


def parse_date(value: str | None) -> date | None:
    """Accept ISO dates ('2024-11-02', '2024-11-02T10:00:00Z') and RFC 2822 dates ('Sat, 02 Nov 2024 00:00:00 GMT')."""
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(value).date()
    except (TypeError, ValueError, IndexError):
        return None


def after_cutoff(published: str | None, cutoff: str | None, text: str = "") -> bool:
    """True when a source must be rejected for a re-run with this cutoff.

    Rejected when: it is undated; it is dated after the cutoff; or its text mentions a later year
    (living pages, such as a list of circulars, keep an old date but gain new content).
    """
    if not cutoff:
        return False
    cut = parse_date(cutoff)
    if cut is None:
        raise ValueError(f"Bad cutoff date: {cutoff!r}")
    pub = parse_date(published)
    if pub is None or pub > cut:
        return True
    later_years = {int(y) for y in re.findall(r"\b(20\d\d)\b", text or "") if int(y) > cut.year}
    return bool(later_years)
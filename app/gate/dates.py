"""Deterministic date checks used by the verification step and the CBEX re-run."""
from __future__ import annotations

from datetime import date


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def after_cutoff(published: str | None, cutoff: str | None) -> bool:
    """True when a source must be rejected for being published after the cutoff.

    Undated sources are rejected when a cutoff is set: for a re-run we cannot prove they are old enough.
    """
    if not cutoff:
        return False
    cut = parse_date(cutoff)
    pub = parse_date(published)
    if cut is None:
        raise ValueError(f"Bad cutoff date: {cutoff!r}")
    return pub is None or pub > cut

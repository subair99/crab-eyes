from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DossierRow(Base):
    __tablename__ = "dossiers"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    input_fingerprint: Mapped[str] = mapped_column(String(32), index=True)
    verdict: Mapped[str] = mapped_column(String(32), index=True)
    company: Mapped[str | None] = mapped_column(Text, index=True)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    body: Mapped[dict] = mapped_column(JSON)           # the full Dossier as JSON
    gallery: Mapped[bool] = mapped_column(default=False)


class SchemeRow(Base):
    """One row per scheme in the public ledger, updated by the nightly job."""
    __tablename__ = "schemes"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)   # normalised name
    display_name: Mapped[str] = mapped_column(Text)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reports_7d: Mapped[int] = mapped_column(default=0)
    reports_prev_7d: Mapped[int] = mapped_column(default=0)
    latest_verdict: Mapped[str] = mapped_column(String(32))
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)

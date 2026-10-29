from fastapi import APIRouter
from sqlalchemy import select

from app.db.models import SchemeRow
from app.db.session import SessionLocal

router = APIRouter()


@router.get("/ledger")
async def ledger() -> list[dict]:
    async with SessionLocal() as s:
        rows = (await s.scalars(select(SchemeRow))).all()
    rows = sorted(rows, key=lambda r: r.reports_7d - r.reports_prev_7d, reverse=True)
    return [{"scheme": r.display_name, "first_seen": r.first_seen.isoformat(), "reports_7d": r.reports_7d,
             "growth": r.reports_7d - r.reports_prev_7d, "verdict": r.latest_verdict} for r in rows]

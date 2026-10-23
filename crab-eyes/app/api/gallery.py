"""Real, anonymised cases judges can open with one click. Mark a dossier as gallery=True after a good run."""
from fastapi import APIRouter
from sqlalchemy import select

from app.db.models import DossierRow
from app.db.session import SessionLocal

router = APIRouter()


@router.get("/gallery")
async def gallery() -> list[dict]:
    async with SessionLocal() as s:
        rows = (await s.scalars(select(DossierRow).where(DossierRow.gallery.is_(True)))).all()
    return [{"id": r.id, "company": r.company, "verdict": r.verdict} for r in rows]

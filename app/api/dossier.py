from fastapi import APIRouter, HTTPException

from app.db.models import DossierRow
from app.db.session import SessionLocal

router = APIRouter()


@router.get("/dossier/{dossier_id}")
async def get_dossier(dossier_id: str) -> dict:
    async with SessionLocal() as s:
        row = await s.get(DossierRow, dossier_id)
    if row is None:
        raise HTTPException(404, "Dossier not found")
    return row.body

"""POST /api/investigate - streams progress as newline-delimited JSON, ending with the dossier."""
from __future__ import annotations

import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.db.models import DossierRow
from app.db.session import SessionLocal
from app.memory.seen_before import fingerprint
from app.pipeline import investigate

router = APIRouter()


class InvestigateRequest(BaseModel):
    text: str = ""
    image_b64: str | None = None


async def save(dossier: dict, text: str) -> None:
    async with SessionLocal() as s:
        names = dossier["claims"].get("company_names") or [None]
        s.add(DossierRow(id=dossier["id"], input_fingerprint=fingerprint(text), verdict=dossier["verdict"],
                         company=names[0], cost_usd=dossier["cost_usd"], body=dossier))
        await s.commit()


@router.post("/investigate")
async def run(req: InvestigateRequest):
    # TODO: return a cached dossier when the same fingerprint was investigated recently (saves credits).
    async def stream():
        async for event in investigate(text=req.text, image_b64=req.image_b64):
            if event["type"] == "dossier":
                await save(event["dossier"], req.text)
            yield json.dumps(event) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")

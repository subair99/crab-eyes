"""POST /api/dossier/{id}/evidence - the user supplies evidence; the investigation reruns with it."""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.investigate import save  # same saving code as a normal investigation
from app.db.models import DossierRow
from app.db.session import SessionLocal
from app.pipeline import investigate
from app.schemas import Finding

router = APIRouter()


class Evidence(BaseModel):
    text: str                    # e.g. "SEC registration number: ..."
    url: str | None = None       # e.g. a link to the register entry


@router.post("/dossier/{dossier_id}/evidence")
async def prove_me_wrong(dossier_id: str, ev: Evidence):
    async with SessionLocal() as s:
        row = await s.get(DossierRow, dossier_id)
    if row is None:
        raise HTTPException(404, "Dossier not found")
    original = row.body["claims"]["raw_text"]
    # The user's evidence is a lead, not proof: the planner is told about it and the regulator check re-runs,
    # so a registration number only counts once the official register confirms it.
    lead = Finding(check="user_evidence", kind="neutral", summary=f"User says: {ev.text}",
                   independence_key="user")

    async def stream():
        try:
            async for event in investigate(text=original + "\n\nUser-supplied evidence: " + ev.text,
                                           extra_findings=[lead]):
                if event["type"] == "dossier":
                    await save(event["dossier"])
                yield json.dumps(event) + "\n"
        except Exception as exc:  # show the problem on the page; the full traceback stays in the terminal
            logging.exception("Prove-me-wrong re-run failed")
            yield json.dumps({"type": "progress", "line": f"Error: {exc}"}) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")
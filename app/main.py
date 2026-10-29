"""FastAPI entry point. Run locally with: uv run uvicorn app.main:app --reload"""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import dossier, gallery, investigate, ledger, prove_me_wrong
from app.db.session import init_db
from app.llm.client import check_models


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await check_models()  # warns if a routing.yaml model ID is not in /v1/models
    yield


app = FastAPI(title="Crab Eyes", version="0.1.0", lifespan=lifespan)

app.include_router(investigate.router, prefix="/api")
app.include_router(dossier.router, prefix="/api")
app.include_router(prove_me_wrong.router, prefix="/api")
app.include_router(gallery.router, prefix="/api")
app.include_router(ledger.router, prefix="/api")


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True}


app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent.parent / "web", html=True), name="web")

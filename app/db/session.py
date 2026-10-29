from __future__ import annotations

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import get_settings
from app.db.models import Base

engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def init_db() -> None:
    # Fine for the hackathon; switch to Alembic migrations (app/db/migrations) if the schema starts changing.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

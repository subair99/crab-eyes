"""Nightly job: refresh regulator warnings, group the day's dossiers into schemes, rank the ledger."""
from __future__ import annotations

import asyncio
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.db.models import DossierRow, SchemeRow
from app.db.session import SessionLocal, init_db
from app.llm.trace import Trace
from app.tools import tavily

REGULATOR_PAGES = [
    "https://www.sec.gov.ng/for-investors/keep-track-of-circulars/",
    # TODO: add CBN and FCCPC warning pages once checked
]


def scheme_key(name: str) -> str:
    # TODO: replace with Nano clustering (routing role "clustering") so "CBEX" and "ST Technologies" group together
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:64]


async def main() -> None:
    await init_db()
    trace = Trace()
    for page in REGULATOR_PAGES:
        await tavily.crawl(page, trace=trace)  # TODO: store notices for the regulator check to use

    now = datetime.now(timezone.utc)
    week, prev = now - timedelta(days=7), now - timedelta(days=14)
    async with SessionLocal() as s:
        rows = (await s.scalars(select(DossierRow).where(DossierRow.created_at >= prev))).all()
        grouped: dict[str, list[DossierRow]] = {}
        for r in rows:
            if r.company:
                grouped.setdefault(scheme_key(r.company), []).append(r)
        for key, items in grouped.items():
            items.sort(key=lambda r: r.created_at)
            scheme = await s.get(SchemeRow, key) or SchemeRow(
                id=key, display_name=items[0].company, first_seen=items[0].created_at, latest_verdict=items[-1].verdict)
            scheme.reports_7d = sum(r.created_at >= week for r in items)
            scheme.reports_prev_7d = sum(r.created_at < week for r in items)
            scheme.latest_verdict = items[-1].verdict
            scheme.evidence = {"dossiers": [r.id for r in items[-5:]]}
            s.add(scheme)
        await s.commit()
    print(f"Ledger updated: {len(grouped)} schemes; tool calls: {len(trace.tool_calls)}")


if __name__ == "__main__":
    asyncio.run(main())

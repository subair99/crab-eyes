from app.agents.investigators._base import search_and_judge
from app.llm.trace import Trace
from app.schemas import Claims, Finding


async def run(claims: Claims, trace: Trace) -> list[Finding]:
    queries = [f'"{person}" investment scheme' for person in claims.people[:2]]
    return await search_and_judge("people", "investigator_people", queries, trace)

from app.agents.investigators._base import search_and_judge
from app.llm.trace import Trace
from app.schemas import Claims, Finding


async def run(claims: Claims, trace: Trace) -> list[Finding]:
    queries = [f"{name} withdrawal problem OR scam OR complaint" for name in claims.company_names[:1]]
    return await search_and_judge("voices", "investigator_voices", queries, trace)

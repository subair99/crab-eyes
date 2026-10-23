from app.agents.investigators._base import search_and_judge
from app.llm.trace import Trace
from app.schemas import Claims, Finding


async def run(claims: Claims, trace: Trace) -> list[Finding]:
    queries = [f"{name} SEC Nigeria registered OR warning OR public notice" for name in claims.company_names[:2]]
    return await search_and_judge(
        "regulator", "investigator_regulator", queries, trace,
        include_domains=["sec.gov.ng", "cbn.gov.ng", "fccpc.gov.ng"],
    )

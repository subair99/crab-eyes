from app.agents.investigators._base import search_and_judge
from app.llm.trace import Trace
from app.schemas import Claims, Finding
from app.tools import tavily


async def run(claims: Claims, trace: Trace) -> list[Finding]:
    # Scheme sites are fetched by Tavily Extract, never opened from our server.
    if claims.urls:
        await tavily.extract(claims.urls[:2], trace=trace)  # TODO: feed extracted text into the judge step
    queries = [f'"{name}" company registration CAC Nigeria website' for name in claims.company_names[:1]]
    return await search_and_judge("footprint", "investigator_footprint", queries, trace)

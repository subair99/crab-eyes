from app.agents.investigators._base import search_and_judge
from app.llm.trace import Trace
from app.schemas import Claims, Finding

TITLES = {"mr", "mrs", "ms", "miss", "dr", "chief", "prof", "pastor", "alhaji", "engr", "barr", "ceo", "coach"}


def full_name(person: str) -> bool:
    words = [w.strip(".,").lower() for w in person.split()]
    return len([w for w in words if w and w not in TITLES]) >= 2


async def run(claims: Claims, trace: Trace) -> list[Finding]:
    names = [p for p in claims.people if full_name(p)][:2]
    if not names:
        return []
    queries = [f'"{p}" {claims.company_names[0] if claims.company_names else "investment"}' for p in names]
    return await search_and_judge("people", "investigator_people", queries, trace)
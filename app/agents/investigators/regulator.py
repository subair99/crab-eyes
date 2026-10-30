from app.agents.investigators._base import search_and_judge
from app.llm.trace import Trace
from app.schemas import Claims, Finding, Source

LICENCE_WORDS = ("sec", "licen", "regist", "approved", "cbn", "regulat")
# Claims about someone else's licence ("buy through registered stockbrokers") are not the scheme claiming one.
THIRD_PARTY = ("broker", "dealer", "agent", "bank", "through", "via")


async def run(claims: Claims, trace: Trace) -> list[Finding]:
    queries = []
    for name in claims.company_names[:2]:
        queries += [
            f'"{name}" SEC Nigeria registered',
            f'"{name}" fund manager capital market operator',
            f'"{name}" SEC Nigeria find a registered operator',
        ]
    findings = await search_and_judge(
        "regulator", "investigator_regulator", queries, trace,
        include_domains=["sec.gov.ng", "cbn.gov.ng", "fccpc.gov.ng"],
    )
    claims_licence = any(
        any(w in c.lower() for w in LICENCE_WORDS) and not any(t in c.lower() for t in THIRD_PARTY)
        for c in claims.regulator_claims
    )
    on_register = any(f.kind == "register_match" for f in findings)
    if claims_licence and claims.company_names and not on_register:
        name = claims.company_names[0]
        findings.append(Finding(
            check="regulator",
            kind="red_flag",
            summary=f"The pitch claims regulatory approval, but no SEC Nigeria registration for \"{name}\" "
                    f"was found in searches of sec.gov.ng, cbn.gov.ng and fccpc.gov.ng.",
            source=Source(url="https://www.sec.gov.ng/", title="SEC Nigeria",
                          snippet=f"Searched for: {name}"),
            official=True,
            entity_match="confirmed",   # the record checked is for the exact name the pitch itself uses
            independence_key="regulator-absence",
            self_evident=True,
        ))
    return findings
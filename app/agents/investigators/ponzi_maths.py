"""Pure code: no model call. The calculator decides; the dossier shows the numbers."""
from app.llm.trace import Trace
from app.schemas import Claims, Finding
from app.tools.calculator import annualise, maths_fails, describe


async def run(claims: Claims, trace: Trace) -> list[Finding]:
    if claims.promised_return is None or not claims.return_period_months:
        return []
    yearly = annualise(claims.promised_return, claims.return_period_months)
    trace.add_tool("calculator", promised=claims.promised_return, months=claims.return_period_months, yearly=yearly)
    return [Finding(
        check="ponzi_maths",
        kind="red_flag" if maths_fails(claims) else "neutral",
        summary=describe(claims.promised_return, claims.return_period_months),
        independence_key="calculator",
    )]

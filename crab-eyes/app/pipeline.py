"""Runs one investigation end to end and yields progress events for streaming.

intake -> planner -> investigators (parallel, up to 2 rounds) -> verification -> reasoning (Ultra, once)
-> policy gate (code) -> dossier
"""
from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator

from app.agents import intake, planner, reasoning, verification
from app.agents.investigators import REGISTRY
from app.config import load_routing
from app.gate.policy import GateInput, decide
from app.llm.trace import Trace
from app.schemas import Dossier, Finding
from app.tools.calculator import maths_fails


async def investigate(
    text: str = "",
    image_b64: str | None = None,
    extra_findings: list[Finding] | None = None,
) -> AsyncIterator[dict]:
    trace = Trace()
    limits = load_routing().get("limits", {})

    yield {"type": "progress", "line": "Reading the pitch..."}
    claims = await intake.extract_claims(text=text, image_b64=image_b64, trace=trace)
    yield {"type": "claims", "claims": claims.model_dump()}

    findings: list[Finding] = list(extra_findings or [])
    plan: list[str] = []
    for round_no in range(limits.get("planner_rounds", 2)):
        checks = await planner.choose_checks(claims, findings, round_no=round_no, trace=trace)
        checks = [c for c in checks if c in REGISTRY]
        if not checks:
            break
        plan.extend(checks)
        yield {"type": "plan", "round": round_no + 1, "checks": checks}
        results = await asyncio.gather(*(REGISTRY[c].run(claims, trace) for c in checks))
        for check, found in zip(checks, results):
            findings.extend(found)
            yield {"type": "progress", "line": f"{check}: {len(found)} finding(s)"}

    yield {"type": "progress", "line": "Verifying sources..."}
    findings = await verification.verify(claims, findings, trace=trace)

    yield {"type": "progress", "line": "Weighing the evidence..."}
    explanations, cvr, change_mind = await reasoning.reason(claims, findings, trace=trace)

    verdict, reasons = decide(
        GateInput(findings=findings, maths_failed=maths_fails(claims)),
    )

    dossier = Dossier(
        id=uuid.uuid4().hex[:12],
        claims=claims,
        plan=plan,
        findings=findings,
        explanations=explanations,
        claims_vs_records=cvr,
        verdict=verdict,
        reasons=reasons,
        what_would_change_my_mind=change_mind,
        trace=trace.as_list(),
        cost_usd=trace.total_cost(),
    )
    yield {"type": "dossier", "dossier": dossier.model_dump(mode="json")}

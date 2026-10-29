"""Super: choose which checks to run, then chase the evidence still missing."""
from __future__ import annotations

import json

from app.agents._prompts import prompt
from app.llm.router import chat_json, items
from app.llm.trace import Trace
from app.schemas import Claims, Finding


async def choose_checks(claims: Claims, findings: list[Finding], round_no: int, trace: Trace) -> list[str]:
    summary = [{"check": f.check, "kind": f.kind, "summary": f.summary} for f in findings]
    user = json.dumps({"round": round_no + 1, "claims": claims.model_dump(exclude={"raw_text"}), "findings": summary})
    data = await chat_json("planner", [{"role": "system", "content": prompt("planner")},
                                       {"role": "user", "content": user}], trace, temperature=0)
    return [c for c in dict.fromkeys(items(data, "checks")) if isinstance(c, str)]
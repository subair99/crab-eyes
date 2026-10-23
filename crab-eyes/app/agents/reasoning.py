"""Ultra, once per dossier: competing explanations, claims vs. records, and what would change its mind."""
from __future__ import annotations

import json

from app.agents._prompts import prompt
from app.llm.router import chat_json
from app.llm.trace import Trace
from app.schemas import ClaimVsRecord, Claims, Explanation, Finding


async def reason(claims: Claims, findings: list[Finding], trace: Trace):
    verified = [f.model_dump(include={"check", "kind", "summary", "official", "source"}) for f in findings if f.verified]
    user = json.dumps({"claims": claims.model_dump(exclude={"raw_text"}), "verified_findings": verified})
    data = await chat_json("reasoner", [{"role": "system", "content": prompt("reasoning")},
                                        {"role": "user", "content": user}], trace, temperature=0)
    explanations = [Explanation(**e) for e in data.get("explanations", [])]
    cvr = [ClaimVsRecord(**c) for c in data.get("claims_vs_records", [])]
    return explanations, cvr, list(data.get("what_would_change_my_mind", []))

"""Ultra, once per dossier: competing explanations, claims vs. records, and what would change its mind."""
from __future__ import annotations

import json

from app.agents._prompts import prompt
from app.llm.router import chat_json
from app.llm.trace import Trace
from app.schemas import ClaimVsRecord, Claims, Explanation, Finding

LABELS = {"licensed_legitimate", "real_but_unlicensed", "ponzi_or_fraud", "impersonation"}


async def reason(claims: Claims, findings: list[Finding], trace: Trace):
    verified = [f.model_dump(include={"check", "kind", "summary", "official", "source"}) for f in findings if f.verified]
    user = json.dumps({"claims": claims.model_dump(exclude={"raw_text"}), "verified_findings": verified})
    data = await chat_json("reasoner", [{"role": "system", "content": prompt("reasoning")},
                                        {"role": "user", "content": user}], trace, temperature=0)
    if not isinstance(data, dict):
        data = {}

    explanations = []
    for e in data.get("explanations") or []:
        if isinstance(e, dict) and e.get("label") in LABELS:
            try:
                explanations.append(Explanation(label=e["label"], probability=float(e.get("probability", 0)),
                                                distinguishing_evidence=str(e.get("distinguishing_evidence", ""))))
            except (TypeError, ValueError):
                continue

    real_urls = {f.source.url for f in findings if f.verified and f.source}
    cvr = []
    for c in data.get("claims_vs_records") or []:
        if not isinstance(c, dict) or not c.get("claim"):
            continue
        cvr.append(ClaimVsRecord(
            claim=str(c["claim"]),
            record=str(c.get("record", "")),
            source_url=c.get("source_url") if c.get("source_url") in real_urls else None,  # drop invented links
            mismatch=bool(c.get("mismatch", False)),
        ))

    change_mind = [str(x) for x in (data.get("what_would_change_my_mind") or []) if x]
    return explanations, cvr, change_mind
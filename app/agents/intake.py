"""Nano (text) or Nemotron 3.5 Super VL (images): pull the claims out of a pitch."""
from __future__ import annotations

import base64

from app.agents._prompts import prompt
from app.llm.router import chat_json
from app.llm.trace import Trace
from app.schemas import Claims

SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF8", "image/gif"),
    (b"RIFF", "image/webp"),
]


def sniff_mime(image_b64: str) -> str:
    """Read the file's first bytes to find its real type (PNG, JPEG, GIF or WebP)."""
    head = base64.b64decode(image_b64[:64] + "=" * (-len(image_b64[:64]) % 4))
    for magic, mime in SIGNATURES:
        if head.startswith(magic):
            return mime
    raise ValueError("Unsupported image type: please upload a PNG, JPEG, GIF or WebP screenshot.")


def describe_claims(data: dict) -> str:
    """Turn claims read from a screenshot back into text, for 'Prove me wrong' and fingerprints."""
    parts = [", ".join(data.get("company_names") or [])]
    if data.get("promised_return") is not None:
        parts.append(f"promises {data['promised_return']:.0%} every {data.get('return_period_months') or '?'} month(s)")
    for key in ("regulator_claims", "other_claims", "people", "urls"):
        parts += data.get(key) or []
    return "Pitch read from a screenshot: " + "; ".join(p for p in parts if p)


async def extract_claims(text: str = "", image_b64: str | None = None, trace: Trace | None = None) -> Claims:
    trace = trace or Trace()
    content: list[dict] | str
    role = "intake_text"
    if image_b64:
        role = "intake_media"
        content = [
            {"type": "text", "text": text or "Extract the claims from this screenshot."},
            {"type": "image_url", "image_url": {"url": f"data:{sniff_mime(image_b64)};base64,{image_b64}"}},
        ]
    else:
        content = text
    data = await chat_json(role, [{"role": "system", "content": prompt("intake")},
                                  {"role": "user", "content": content}], trace, temperature=0)
    if isinstance(data, list):  # some replies come back as a bare list holding one object
        data = data[0] if data else {}
    return Claims(**data, raw_text=text or describe_claims(data))
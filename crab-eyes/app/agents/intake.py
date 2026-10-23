"""Nano (text) or Nano Omni (images, voice notes): pull the claims out of a pitch."""
from __future__ import annotations

from app.agents._prompts import prompt
from app.llm.router import chat_json
from app.llm.trace import Trace
from app.schemas import Claims


async def extract_claims(text: str = "", image_b64: str | None = None, trace: Trace | None = None) -> Claims:
    trace = trace or Trace()
    content: list[dict] | str
    role = "intake_text"
    if image_b64:
        role = "intake_media"
        content = [
            {"type": "text", "text": text or "Extract the claims from this screenshot."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
        ]
    else:
        content = text
    # TODO: voice notes - convert Telegram .oga with ffmpeg, then send as audio input if Nano Omni supports it.
    data = await chat_json(role, [{"role": "system", "content": prompt("intake")},
                                  {"role": "user", "content": content}], trace, temperature=0)
    return Claims(**data, raw_text=text)

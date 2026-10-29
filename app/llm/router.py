"""Sends each call to the model routing.yaml assigns to its role, and records it in the trace."""
from __future__ import annotations

import json
import re
import time

from app.config import load_routing
from app.llm.client import get_client
from app.llm.trace import Trace


def model_for(role: str) -> tuple[str, dict]:
    routing = load_routing()
    name = routing["roles"][role]
    cfg = routing["models"][name]
    if not cfg.get("id") and role == "intake_media":
        return model_for("intake_text")
    return name, cfg


async def chat(role: str, messages: list[dict], trace: Trace, **kwargs) -> str:
    name, cfg = model_for(role)
    started = time.perf_counter()
    resp = await get_client().chat.completions.create(model=cfg["id"], messages=messages, **kwargs)
    usage = resp.usage
    trace.add(
        role=role,
        model=cfg["id"],
        tokens_in=getattr(usage, "prompt_tokens", 0) or 0,
        tokens_out=getattr(usage, "completion_tokens", 0) or 0,
        price_in=cfg["price_in"],
        price_out=cfg["price_out"],
        seconds=time.perf_counter() - started,
    )
    return resp.choices[0].message.content or ""


async def chat_json(role: str, messages: list[dict], trace: Trace, **kwargs) -> dict | list:
    """Ask for JSON and parse it, tolerating code fences or reasoning text around the object."""
    text = await chat(role, messages, trace, **kwargs)
    return parse_json(text)


def parse_json(text: str) -> dict | list:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)
    match = re.search(r"```(?:json)?\s*(.*?)```", text, flags=re.S)
    if match:
        text = match.group(1)
    start = min([i for i in (text.find("{"), text.find("[")) if i != -1], default=-1)
    if start == -1:
        raise ValueError(f"No JSON in model output: {text[:200]!r}")
    return json.JSONDecoder().raw_decode(text[start:])[0]


def items(data: dict | list, key: str) -> list:
    """Return data[key] when the model returned an object, or the list itself when it returned a bare list."""
    if isinstance(data, list):
        return data
    return data.get(key, []) or []
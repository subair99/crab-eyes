"""Nebius Token Factory client (OpenAI-compatible)."""
from __future__ import annotations

import logging
from functools import lru_cache

from openai import AsyncOpenAI

from app.config import get_settings, load_routing

log = logging.getLogger(__name__)


@lru_cache
def get_client() -> AsyncOpenAI:
    s = get_settings()
    return AsyncOpenAI(api_key=s.token_factory_api_key, base_url=s.token_factory_base_url)


async def check_models() -> None:
    """Warn at start-up if a model ID in routing.yaml is not served by Token Factory."""
    if not get_settings().token_factory_api_key:
        log.warning("TOKEN_FACTORY_API_KEY is not set")
        return
    try:
        served = {m.id async for m in get_client().models.list()}
    except Exception as exc:  # network or auth problem: report, don't crash
        log.warning("Could not list Token Factory models: %s", exc)
        return
    for name, cfg in load_routing()["models"].items():
        if cfg.get("id") and cfg["id"] not in served:
            log.warning("routing.yaml model %s (%s) is not in /v1/models", name, cfg["id"])

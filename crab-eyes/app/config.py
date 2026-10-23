"""Settings from the environment, plus routing.yaml."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


@dataclass
class Settings:
    token_factory_api_key: str = field(default_factory=lambda: _env("TOKEN_FACTORY_API_KEY"))
    token_factory_base_url: str = field(
        default_factory=lambda: _env("TOKEN_FACTORY_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")
    )
    tavily_api_key: str = field(default_factory=lambda: _env("TAVILY_API_KEY"))
    database_url: str = field(
        default_factory=lambda: _env("DATABASE_URL", "postgresql+psycopg://crab:crab@localhost:5432/crabeyes")
    )
    telegram_bot_token: str = field(default_factory=lambda: _env("TELEGRAM_BOT_TOKEN"))
    benchmark_annual_rate: float | None = field(
        default_factory=lambda: float(_env("BENCHMARK_ANNUAL_RATE")) if _env("BENCHMARK_ANNUAL_RATE") else None
    )
    evidence_end_date: str | None = field(default_factory=lambda: _env("EVIDENCE_END_DATE") or None)
    routing_path: Path = ROOT / "routing.yaml"
    thresholds_path: Path = ROOT / "app" / "gate" / "thresholds.yaml"


@lru_cache
def get_settings() -> Settings:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    return Settings()


@lru_cache
def load_routing() -> dict:
    return yaml.safe_load(get_settings().routing_path.read_text())

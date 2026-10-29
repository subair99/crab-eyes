from functools import lru_cache
from pathlib import Path

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


@lru_cache
def prompt(name: str) -> str:
    return (PROMPTS / f"{name}.md").read_text()

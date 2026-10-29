"""The five checks. Each module exposes `async def run(claims, trace) -> list[Finding]`."""
from app.agents.investigators import footprint, people, ponzi_maths, regulator, voices

REGISTRY = {
    "regulator": regulator,
    "ponzi_maths": ponzi_maths,
    "footprint": footprint,
    "people": people,
    "voices": voices,
}

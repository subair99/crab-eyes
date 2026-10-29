"""Per-dossier record of every model and tool call: tokens, cost and time."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Call:
    role: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    seconds: float


@dataclass
class Trace:
    calls: list[Call] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)

    def add(self, *, role, model, tokens_in, tokens_out, price_in, price_out, seconds) -> None:
        cost = tokens_in / 1e6 * price_in + tokens_out / 1e6 * price_out
        self.calls.append(Call(role, model, tokens_in, tokens_out, round(cost, 6), round(seconds, 2)))

    def add_tool(self, tool: str, **detail) -> None:
        self.tool_calls.append({"tool": tool, **detail})

    def total_cost(self) -> float:
        return round(sum(c.cost_usd for c in self.calls), 6)

    def as_list(self) -> list[dict]:
        return [asdict(c) for c in self.calls] + self.tool_calls

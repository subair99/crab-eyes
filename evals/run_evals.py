"""Run every case in cases.csv and report precision, recall, false alarms, the share of 'not enough evidence',
median time and average cost per dossier. Run twice to compare routed vs Ultra-only:

    uv run --env-file .env python -m evals.run_evals
    uv run --env-file .env python -m evals.run_evals --ultra-only
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import statistics
import time
from pathlib import Path

from app.config import load_routing
from app.pipeline import investigate

HERE = Path(__file__).resolve().parent


async def run_case(text: str) -> tuple[dict, float]:
    started = time.perf_counter()
    dossier = None
    async for event in investigate(text=text):
        if event["type"] == "dossier":
            dossier = event["dossier"]
    if dossier is None:
        raise RuntimeError("investigation ended without a dossier")
    return dossier, time.perf_counter() - started


def metrics(rows: list[dict]) -> dict:
    flagged = [r for r in rows if r["predicted"] == "high_risk"]
    scams = [r for r in rows if r["expected"] == "high_risk"]
    not_scams = [r for r in rows if r["expected"] != "high_risk"]
    tp = sum(r["expected"] == "high_risk" for r in flagged)
    return {
        "cases": len(rows),
        "precision_high_risk": round(tp / len(flagged), 3) if flagged else None,
        "recall_high_risk": round(tp / len(scams), 3) if scams else None,
        "false_alarms": sum(r["predicted"] == "high_risk" for r in not_scams),
        "share_not_enough_evidence": round(sum(r["predicted"] == "not_enough_evidence" for r in rows) / len(rows), 3),
        "median_seconds": round(statistics.median(r["seconds"] for r in rows), 1),
        "avg_cost_usd": round(statistics.mean(r["cost"] for r in rows), 5),
    }


async def main(ultra_only: bool) -> None:
    if ultra_only:
        routing = load_routing()
        for role in routing["roles"]:
            if role != "intake_media":
                routing["roles"][role] = "ultra"
    with open(HERE / "cases.csv", newline="") as fh:
        cases = list(csv.DictReader(fh))
    if not cases:
        raise SystemExit("evals/cases.csv has no cases yet")

    rows = []
    for case in cases:
        try:
            dossier, seconds = await run_case(case["input_text"])
        except Exception as exc:  # record the failure and keep going
            print(case["id"], "FAILED:", type(exc).__name__, exc)
            continue
        rows.append({"id": case["id"], "expected": case["expected_verdict"], "predicted": dossier["verdict"],
                     "seconds": seconds, "cost": dossier["cost_usd"]})
        print(case["id"], case["expected_verdict"], "->", dossier["verdict"])
    if not rows:
        raise SystemExit("Every case failed - check the errors above.")

    out = {"mode": "ultra_only" if ultra_only else "routed", **metrics(rows), "rows": rows}
    (HERE / "results").mkdir(exist_ok=True)
    path = HERE / "results" / f"{out['mode']}.json"
    path.write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
    print(f"Saved {path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--ultra-only", action="store_true")
    asyncio.run(main(p.parse_args().ultra_only))
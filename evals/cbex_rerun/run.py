"""CBEX re-run: investigate CBEX using only sources published before withdrawals froze (10 April 2025).

    uv run python -m evals.cbex_rerun.run --pitch-file evals/cbex_rerun/pitch.txt

Every Tavily search gets end_date=2025-04-09, and the verification step rejects any source dated later
(or undated). Publish the dossier as it comes out, including any miss.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path

CUTOFF = "2025-04-09"
HERE = Path(__file__).resolve().parent


async def main(pitch_file: Path) -> None:
    os.environ["EVIDENCE_END_DATE"] = CUTOFF
    from app.config import get_settings
    get_settings.cache_clear()
    from app.pipeline import investigate

    dossier = None
    async for event in investigate(text=pitch_file.read_text()):
        if event["type"] == "progress":
            print(event["line"])
        if event["type"] == "dossier":
            dossier = event["dossier"]
    (HERE / "dossier.json").write_text(json.dumps(dossier, indent=2))
    lines = [f"# CBEX re-run (sources published on or before {CUTOFF})", "",
             f"**Verdict:** {dossier['verdict']}", "", "## Reasons", *[f"- {r}" for r in dossier["reasons"]],
             "", "## Every source and its date"]
    for f in dossier["findings"]:
        if f.get("source"):
            status = "used" if f["verified"] else f"set aside ({f['rejected_reason']})"
            lines.append(f"- {f['source'].get('published_date') or 'undated'} | {f['source']['url']} | {status}")
    (HERE / "dossier.md").write_text("\n".join(lines) + "\n")
    print("Wrote evals/cbex_rerun/dossier.md")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pitch-file", type=Path, default=HERE / "pitch.txt")
    asyncio.run(main(p.parse_args().pitch_file))

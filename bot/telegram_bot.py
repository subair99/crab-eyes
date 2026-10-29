"""Telegram bot: forward a pitch, watch live progress, get the verdict card.

Run: uv run python -m bot.telegram_bot   (uses polling; no public URL needed while testing)
"""
from __future__ import annotations

import base64
import json
import os

import httpx
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

API = os.environ.get("CRAB_EYES_API_URL", "http://localhost:8000")
LABELS = {
    "high_risk": "HIGH RISK",
    "check_first": "CHECK FIRST",
    "looks_legitimate": "LOOKS LEGITIMATE",
    "not_enough_evidence": "NOT ENOUGH EVIDENCE",
}


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    payload = {"text": msg.text or msg.caption or ""}
    if msg.photo:
        file = await msg.photo[-1].get_file()
        payload["image_b64"] = base64.b64encode(bytes(await file.download_as_bytearray())).decode()

    status = await msg.reply_text("Investigating...")
    lines: list[str] = []
    async with httpx.AsyncClient(timeout=300) as client:
        async with client.stream("POST", f"{API}/api/investigate", json=payload) as resp:
            async for raw in resp.aiter_lines():
                if not raw:
                    continue
                event = json.loads(raw)
                if event["type"] == "progress":
                    lines.append(event["line"])
                    await status.edit_text("Investigating...\n" + "\n".join(lines[-6:]))
                elif event["type"] == "dossier":
                    d = event["dossier"]
                    card = [LABELS[d["verdict"]], *[f"- {r}" for r in d["reasons"][:3]],
                            f"Full dossier: {API}/dossier.html?id={d['id']}", d["disclaimer"]]
                    await msg.reply_text("\n".join(card))


def main() -> None:
    app = Application.builder().token(os.environ["TELEGRAM_BOT_TOKEN"]).build()
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle))
    app.run_polling()


if __name__ == "__main__":
    main()

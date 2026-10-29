"""Check whether Nemotron 3 Nano Omni on Token Factory can read a screenshot.

Usage: uv run --env-file .env python scripts/test_omni.py path/to/screenshot.png [model-id]
"""
import base64
import mimetypes
import os
import sys

from openai import OpenAI

client = OpenAI(
    api_key=os.environ["TOKEN_FACTORY_API_KEY"],
    base_url=os.environ.get("TOKEN_FACTORY_BASE_URL", "https://api.tokenfactory.nebius.com/v1/"),
)

# 1. Find the Omni model ID
omni = [m.id for m in client.models.list() if "omni" in m.id.lower()]
print("Omni models available:", omni or "none found")
model = sys.argv[2] if len(sys.argv) > 2 else (omni[0] if omni else None)
if not model:
    sys.exit("No Omni model on your account -> switch to text-only intake.")

# 2. Send the screenshot
path = sys.argv[1]
mime = mimetypes.guess_type(path)[0] or "image/png"
data = base64.b64encode(open(path, "rb").read()).decode()

resp = client.chat.completions.create(
    model=model,
    temperature=0,
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": (
                "This is a screenshot of an investment pitch. Copy out, exactly: the company name, "
                "the promised return and its period, any regulator or licence claims, any people named, "
                "and any website or phone number. Write 'not shown' for anything missing.")},
            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}},
        ],
    }],
)
print(f"\nModel: {model}\n")
print(resp.choices[0].message.content)
print(f"\nTokens in/out: {resp.usage.prompt_tokens}/{resp.usage.completion_tokens}")
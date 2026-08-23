import asyncio
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.core.config import get_settings  # noqa: E402


async def main() -> None:
    settings = get_settings()
    if not settings.groq_api_key:
        print("GROQ_API_KEY missing")
        return

    async with httpx.AsyncClient(timeout=45) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.groq_api_key}"},
            json={
                "model": settings.groq_model,
                "messages": [{"role": "user", "content": "Reply with ok."}],
                "temperature": 0,
            },
        )
    print("groq_model", settings.groq_model)
    print("status", response.status_code)
    print(response.text[:1000])


if __name__ == "__main__":
    asyncio.run(main())

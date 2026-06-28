from __future__ import annotations

import asyncio
import random

import httpx

from app.modules.logger import get_logger
from app.modules.openai_client.models import CompletionRequest

logger = get_logger(__name__)


class OpenRouterClient:
    """OpenRouter API client (OpenAI-compatible endpoint)."""

    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            base_url="https://openrouter.ai/api/v1",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=180.0,
        )

    async def chat_completion(self, request: CompletionRequest, max_retries: int = 3):
        payload = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "messages": request.messages,
        }

        for attempt in range(max_retries + 1):
            try:
                response = await self.client.post("/chat/completions", json=payload)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 429 and attempt < max_retries:
                    wait = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Rate limited (429). Retrying in {wait:.1f}s... "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    await asyncio.sleep(wait)
                else:
                    raise

    async def close(self):
        await self.client.aclose()

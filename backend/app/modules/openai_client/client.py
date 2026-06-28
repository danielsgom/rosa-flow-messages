from openai import AsyncOpenAI

from app.modules.logger import get_logger
from app.config import Settings

logger = get_logger(__name__)


class OpenAIClient:
    """Wrapper around the AsyncOpenAI client."""

    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        logger.info("OpenAI client initialized")

    async def chat_completion(self, model: str, messages: list, **kwargs) -> str:
        """Send a chat completion request and return the response text."""
        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                **kwargs,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            logger.error(f"OpenAI API error: {exc}")
            raise

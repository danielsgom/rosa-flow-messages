from typing import List, Dict

from app.modules.logger import get_logger
from .client import OpenRouterClient
from .models import CompletionRequest

logger = get_logger(__name__)


class ResponseGenerator:
    """Generates AI responses using the OpenRouter client."""

    def __init__(self, client: OpenRouterClient, model: str):
        self.client = client
        self.model = model

    async def generate(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a response from OpenRouter.

        Args:
            messages: The full message context (system + history + user).

        Returns:
            The generated response text.
        """
        logger.debug(f"Generating response with {len(messages)} messages")
        request = CompletionRequest(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=500,
        )
        response = await self.client.chat_completion(request)
        content = response["choices"][0]["message"]["content"]
        logger.debug(f"Generated response: {content[:50]}...")
        return content

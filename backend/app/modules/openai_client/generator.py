from typing import List, Dict

from app.modules.logger import get_logger
from .client import OpenAIClient

logger = get_logger(__name__)


class ResponseGenerator:
    """Generates AI responses using the OpenAI client."""

    def __init__(self, client: OpenAIClient, model: str):
        self.client = client
        self.model = model

    async def generate(self, messages: List[Dict[str, str]]) -> str:
        """
        Generate a response from OpenAI.

        Args:
            messages: The full message context (system + history + user).

        Returns:
            The generated response text.
        """
        logger.debug(f"Generating response with {len(messages)} messages")
        response = await self.client.chat_completion(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_completion_tokens=500,
        )
        logger.debug(f"Generated response: {response[:50]}...")
        return response

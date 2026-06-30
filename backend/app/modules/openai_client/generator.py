from typing import List, Dict, Optional

from app.modules.logger import get_logger
from .client import OpenRouterClient
from .models import CompletionRequest

logger = get_logger(__name__)


class ResponseGenerator:
    """Generates AI responses using the OpenRouter client."""

    def __init__(self, client: OpenRouterClient, model: str, max_tokens: int = 8000):
        self.client = client
        self.model = model
        self.max_tokens = max_tokens

    async def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        reasoning_effort: Optional[str] = None,
    ) -> str:
        """
        Generate a response from OpenRouter.

        Args:
            messages: The full message context (system + history + user).
            max_tokens: Override default max_tokens (e.g. lower for farewell).
            reasoning_effort: Reasoning effort level for reasoning models.

        Returns:
            The generated response text.
        """
        logger.debug(f"Generating response with {len(messages)} messages")
        request = CompletionRequest(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=max_tokens or self.max_tokens,
            reasoning_effort=reasoning_effort,
        )
        response = await self.client.chat_completion(request)

        if not response:
            raise ValueError("OpenRouter returned an empty response")

        if "error" in response:
            err = response["error"]
            raise ValueError(f"OpenRouter error: {err.get('message', err)}")

        choices = response.get("choices")
        if not choices:
            raise ValueError(f"OpenRouter response missing 'choices': {response}")

        content = choices[0].get("message", {}).get("content")
        if not content:
            raise ValueError(f"OpenRouter response missing content: {choices[0]}")

        logger.debug(f"Generated response: {content[:50]}...")
        return content

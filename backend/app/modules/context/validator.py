from typing import List

from app.modules.logger import get_logger, PromptValidationError

logger = get_logger(__name__)


class PromptValidator:
    """Validates the system prompt content."""

    def __init__(self, max_tokens: int = 2000):
        self.max_tokens = max_tokens

    def validate(self, content: str) -> None:
        """Validate the prompt content. Raises PromptValidationError if invalid."""
        if not content or not content.strip():
            raise PromptValidationError("Prompt content is empty")

        text = content.lower()

        # Check core persona identifiers are present
        required_keywords = ["rosa", "nombre"]
        missing = [kw for kw in required_keywords if kw not in text]

        if missing:
            raise PromptValidationError(
                f"Missing required keywords: {', '.join(missing)}"
            )

        # Rough token estimation (1 token ≈ 4 chars for English/Spanish)
        estimated_tokens = len(content) / 4
        if estimated_tokens > self.max_tokens:
            raise PromptValidationError(
                f"Prompt too long. Estimated: {estimated_tokens:.0f} tokens. "
                f"Max allowed: {self.max_tokens}"
            )

        logger.info(f"Prompt validation passed. Estimated tokens: {estimated_tokens:.0f}")

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

        # Extract all headings from the document
        headings = [
            line.strip().lower()
            for line in content.split("\n")
            if line.strip().startswith("#")
        ]
        headings_text = " ".join(headings)

        # Check required keywords are present in headings
        required_keywords = [
            "identidad",
            "bio",
            "límite",
            "instruccion",
        ]
        missing = []
        for kw in required_keywords:
            if not any(kw in h for h in headings):
                missing.append(kw)

        if missing:
            raise PromptValidationError(
                f"Missing required sections: {', '.join(missing)}"
            )

        # Rough token estimation (1 token ≈ 4 chars for English/Spanish)
        estimated_tokens = len(content) / 4
        if estimated_tokens > self.max_tokens:
            raise PromptValidationError(
                f"Prompt too long. Estimated: {estimated_tokens:.0f} tokens. "
                f"Max allowed: {self.max_tokens}"
            )

        logger.info(f"Prompt validation passed. Estimated tokens: {estimated_tokens:.0f}")

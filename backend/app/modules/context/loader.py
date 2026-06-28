from pathlib import Path
from typing import Optional

from app.modules.logger import get_logger, ContextLoadError

logger = get_logger(__name__)


class PromptLoader:
    """Loads the system prompt from a markdown file."""

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self._content: Optional[str] = None

    def load(self) -> str:
        """Load and return the system prompt content."""
        if not self.file_path.exists():
            logger.error(f"System prompt file not found: {self.file_path}")
            raise ContextLoadError(f"System prompt file not found: {self.file_path}")

        content = self.file_path.read_text(encoding="utf-8").strip()
        if not content:
            logger.error("System prompt file is empty")
            raise ContextLoadError("System prompt file is empty")

        self._content = content
        logger.info(f"Loaded system prompt from {self.file_path}")
        return content

    def reload(self) -> str:
        """Reload the system prompt from disk."""
        self._content = None
        return self.load()

    @property
    def content(self) -> Optional[str]:
        """Get cached content without reloading."""
        return self._content

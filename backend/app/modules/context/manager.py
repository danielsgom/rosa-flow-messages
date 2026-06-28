from typing import List, Optional

from .loader import PromptLoader
from .validator import PromptValidator
from .history import ConversationHistory
from .models import Message


class ContextManager:
    """Manages the full conversation context for OpenAI API."""

    def __init__(
        self,
        prompt_loader: PromptLoader,
        prompt_validator: PromptValidator,
        history: ConversationHistory,
    ):
        self.prompt_loader = prompt_loader
        self.prompt_validator = prompt_validator
        self.history = history
        self._system_prompt: str = ""

    def initialize(self) -> None:
        """Load and validate the system prompt."""
        content = self.prompt_loader.load()
        self.prompt_validator.validate(content)
        self._system_prompt = content

    def build_context(self, chat_id: int, new_message: Optional[str] = None) -> List[dict]:
        """Build the full messages array for OpenAI API."""
        messages = [{"role": "system", "content": self._system_prompt}]

        # Add conversation history
        history_messages = self.history.get_for_openai(chat_id)
        messages.extend(history_messages)

        # Add new user message if provided
        if new_message:
            messages.append({"role": "user", "content": new_message})

        return messages

    def add_to_history(self, chat_id: int, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.history.add(chat_id, role, content)

    def clear_history(self, chat_id: int) -> None:
        """Clear history for a new conversation start."""
        self.history.clear(chat_id)

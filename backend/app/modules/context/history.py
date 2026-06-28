from collections import deque
from typing import Dict, List, Optional, Deque

from .models import Message


class ConversationHistory:
    """Manages in-memory conversation history per chat."""

    def __init__(self, max_messages: int = 20):
        self._history: Dict[int, Deque[Message]] = {}
        self._max_messages = max_messages

    def add(self, chat_id: int, role: str, content: str) -> None:
        """Add a message to the chat history."""
        if chat_id not in self._history:
            self._history[chat_id] = deque(maxlen=self._max_messages)

        self._history[chat_id].append(Message(role=role, content=content))

    def get(self, chat_id: int) -> List[Message]:
        """Get all messages for a chat."""
        if chat_id not in self._history:
            return []
        return list(self._history[chat_id])

    def clear(self, chat_id: int) -> None:
        """Clear history for a specific chat."""
        if chat_id in self._history:
            self._history[chat_id].clear()

    def get_for_openai(self, chat_id: int) -> List[dict]:
        """Get messages formatted for OpenAI API."""
        messages = self.get(chat_id)
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    def has_messages(self, chat_id: int) -> bool:
        """Check if chat has any message history."""
        return chat_id in self._history and len(self._history[chat_id]) > 0

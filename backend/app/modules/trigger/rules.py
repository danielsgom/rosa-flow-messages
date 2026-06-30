from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from app.modules.logger import get_logger

logger = get_logger(__name__)


class TriggerRules:
    """Rules that govern when the bot should respond."""

    def __init__(self, cooldown_seconds: float = 5.0):
        self._cooldown_seconds = cooldown_seconds
        self._last_bot_message: Dict[int, datetime] = {}

    def is_in_cooldown(self, chat_id: int) -> bool:
        """Check if we're still in cooldown period after last bot message."""
        if chat_id not in self._last_bot_message:
            return False

        elapsed = (datetime.now(timezone.utc) - self._last_bot_message[chat_id]).total_seconds()
        return elapsed < self._cooldown_seconds

    def record_bot_message(self, chat_id: int) -> None:
        """Record that bot sent a message to this chat."""
        self._last_bot_message[chat_id] = datetime.now(timezone.utc)

    def is_message_from_me(self, sender_id: int, my_id: int) -> bool:
        """Check if message is from ourselves (outbound)."""
        return sender_id == my_id

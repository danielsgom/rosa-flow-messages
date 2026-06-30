from enum import Enum
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class ConversationStatus(str, Enum):
    """Status of a conversation lifecycle."""
    ACTIVE = "active"
    CLOSED = "closed"


class ChatInfo(BaseModel):
    """Information about a chat contact."""
    chat_id: int
    name: str                       # Display name (first_name or title)
    full_name: Optional[str] = None # first_name + last_name
    username: Optional[str] = None  # @username (no including @)
    last_message_preview: str = ""
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    auto_enabled: bool = False
    conversation_status: ConversationStatus = ConversationStatus.ACTIVE

    # Session tracking for conversation time/turn limits
    session_started_at: Optional[datetime] = None
    turn_count: int = 0

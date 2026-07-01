from enum import Enum
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, Field


class ConversationStatus(str, Enum):
    """Status of a conversation lifecycle."""
    ACTIVE = "active"
    CLOSING = "closing"   # farewell sent, accepting 1-2 more turns
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

    # Session tracking for conversation turn limits
    session_started_at: Optional[datetime] = None
    turn_count: int = 0
    session_max_turns: Optional[int] = None  # randomized per session (15-20)
    photos_sent: int = 0
    photos_sent_filenames: List[str] = Field(default_factory=list)
    closing_turns_left: int = 0
    last_photo_turn: int = 0

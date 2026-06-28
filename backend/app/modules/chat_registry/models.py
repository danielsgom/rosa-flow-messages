from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class ConversationStatus(str, Enum):
    """Status of a conversation lifecycle."""
    ACTIVE = "active"
    CLOSED = "closed"


class ChatInfo(BaseModel):
    """Information about a chat contact."""
    chat_id: int
    name: str
    last_message_preview: str = ""
    last_message_at: datetime = Field(default_factory=datetime.now)
    auto_enabled: bool = False
    conversation_status: ConversationStatus = ConversationStatus.ACTIVE

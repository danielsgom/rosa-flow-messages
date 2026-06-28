from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TelegramMessage(BaseModel):
    """Represents a Telegram message."""
    chat_id: int
    sender_id: int
    text: str
    date: datetime
    is_outgoing: bool = False


class ChatInfo(BaseModel):
    """Basic chat information."""
    id: int
    name: str
    username: Optional[str] = None

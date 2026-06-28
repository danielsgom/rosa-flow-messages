from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class ChatResponse(BaseModel):
    """Schema for chat list response."""
    chat_id: int
    name: str
    full_name: Optional[str] = None
    username: Optional[str] = None
    last_message_preview: str
    last_message_at: datetime
    auto_enabled: bool
    conversation_status: str


class ToggleRequest(BaseModel):
    """Schema for toggle auto-response request."""
    enabled: bool


class ToggleResponse(BaseModel):
    """Schema for toggle response."""
    chat_id: int
    auto_enabled: bool
    conversation_status: str


class SyncResponse(BaseModel):
    """Schema for Telegram sync response."""
    synced: int
    total: int
    chats: List[ChatResponse]

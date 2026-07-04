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
    # Enriched fields from DB
    is_vip: bool = False
    total_conversations: int = 0
    total_cost_usd: float = 0.0
    current_session_photos: List[str] = []


class ToggleRequest(BaseModel):
    enabled: bool


class ToggleResponse(BaseModel):
    chat_id: int
    auto_enabled: bool
    conversation_status: str


class VipRequest(BaseModel):
    is_vip: bool


class SyncResponse(BaseModel):
    synced: int
    total: int
    chats: List[ChatResponse]


class PhotoResponse(BaseModel):
    filename: str
    size_bytes: int
    enabled: bool
    url: str
    caption: Optional[str] = None


class PhotoListResponse(BaseModel):
    total: int
    photos: List[PhotoResponse]


class PhotoToggleRequest(BaseModel):
    enabled: bool


class PhotoCaptionRequest(BaseModel):
    caption: Optional[str] = None


# ---------------------------------------------------------------------------
# Chat photo assignment
# ---------------------------------------------------------------------------

class ChatPhotosResponse(BaseModel):
    chat_id: int
    assigned_filenames: List[str]


class ChatPhotosUpdate(BaseModel):
    filenames: List[str]


# ---------------------------------------------------------------------------
# Conversation history
# ---------------------------------------------------------------------------

class ConversationHistoryItem(BaseModel):
    id: int
    started_at: datetime
    ended_at: Optional[datetime] = None
    turn_count: int
    max_turns: Optional[int] = None
    status: str
    photos: List[str] = []
    cost_usd: float = 0.0


class ChatHistoryResponse(BaseModel):
    chat_id: int
    total_conversations: int
    conversations: List[ConversationHistoryItem]


# ---------------------------------------------------------------------------
# Cost tracking
# ---------------------------------------------------------------------------

class CostEntryResponse(BaseModel):
    chat_id: int
    chat_name: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    timestamp: datetime


class CostSummaryResponse(BaseModel):
    total_calls: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost_usd: float


class ChatCostResponse(BaseModel):
    chat_id: int
    chat_name: str
    calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float

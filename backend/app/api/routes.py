from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.modules.logger import get_logger
from app.modules.chat_registry import ChatRegistry, ConversationStatus
from app.api.schemas import ChatResponse, ToggleRequest, ToggleResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/api")


class ChatRegistryDep:
    """Simple dependency container for shared state."""
    registry: Optional[ChatRegistry] = None


async def get_chat_registry() -> ChatRegistry:
    if ChatRegistryDep.registry is None:
        raise HTTPException(status_code=500, detail="Chat registry not initialized")
    return ChatRegistryDep.registry


@router.get("/chats", response_model=List[ChatResponse])
async def list_chats(registry: ChatRegistry = Depends(get_chat_registry)):
    """List all discovered chats."""
    chats = await registry.list_chats()
    return [
        ChatResponse(
            chat_id=c.chat_id,
            name=c.name,
            full_name=c.full_name,
            username=c.username,
            last_message_preview=c.last_message_preview,
            last_message_at=c.last_message_at,
            auto_enabled=c.auto_enabled,
            conversation_status=c.conversation_status.value,
        )
        for c in chats
    ]


@router.patch("/chats/{chat_id}/toggle", response_model=ToggleResponse)
async def toggle_chat(
    chat_id: int,
    request: ToggleRequest,
    registry: ChatRegistry = Depends(get_chat_registry),
):
    """Toggle auto-response for a chat."""
    chat = await registry.toggle_auto(chat_id, request.enabled)
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")

    return ToggleResponse(
        chat_id=chat.chat_id,
        auto_enabled=chat.auto_enabled,
        conversation_status=chat.conversation_status.value,
    )

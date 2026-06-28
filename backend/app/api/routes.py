from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.modules.logger import get_logger
from app.modules.chat_registry import ChatRegistry, ConversationStatus
from app.modules.telegram import TelegramClientWrapper
from app.api.schemas import ChatResponse, ToggleRequest, ToggleResponse, SyncResponse

logger = get_logger(__name__)
router = APIRouter(prefix="/api")


class ChatRegistryDep:
    """Simple dependency container for shared state."""
    registry: Optional[ChatRegistry] = None


class TelegramClientDep:
    """Simple dependency container for Telegram client."""
    client: Optional[TelegramClientWrapper] = None


async def get_chat_registry() -> ChatRegistry:
    if ChatRegistryDep.registry is None:
        raise HTTPException(status_code=500, detail="Chat registry not initialized")
    return ChatRegistryDep.registry


async def get_telegram_client() -> TelegramClientWrapper:
    if TelegramClientDep.client is None:
        raise HTTPException(status_code=500, detail="Telegram client not initialized")
    return TelegramClientDep.client


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


@router.post("/chats/sync", response_model=SyncResponse)
async def sync_chats(
    registry: ChatRegistry = Depends(get_chat_registry),
    telegram: TelegramClientWrapper = Depends(get_telegram_client),
):
    """Sync all existing Telegram dialogs into the chat registry."""
    try:
        dialogs = await telegram.get_dialogs()
    except Exception as exc:
        logger.error(f"Failed to fetch Telegram dialogs: {exc}")
        raise HTTPException(status_code=502, detail=f"Telegram API error: {exc}")

    synced_count = 0
    for dialog in dialogs:
        await registry.register_or_update(
            chat_id=dialog["chat_id"],
            name=dialog["name"],
            full_name=dialog["full_name"],
            username=dialog["username"],
            last_message=dialog["last_message_preview"],
            last_date=dialog["last_message_at"],
        )
        synced_count += 1

    logger.info(f"Synced {synced_count} dialogs from Telegram")

    # Return the updated list
    chats = await registry.list_chats()
    return SyncResponse(
        synced=synced_count,
        total=synced_count,
        chats=[
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
        ],
    )


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

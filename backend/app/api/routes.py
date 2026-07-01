from typing import List, Optional
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.modules.logger import get_logger
from app.modules.chat_registry import ChatRegistry, ConversationStatus
from app.modules.photo_registry import PhotoRegistry
from app.modules.telegram import TelegramClientWrapper
from app.api.schemas import (
    ChatResponse, ToggleRequest, ToggleResponse, SyncResponse,
    PhotoResponse, PhotoListResponse, PhotoToggleRequest,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api")

_SAFE_FILENAME_RE = re.compile(r'^[a-zA-Z0-9_\-\.]+$')
_ALLOWED_MIME_PREFIXES = ("image/",)
_MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


class ChatRegistryDep:
    """Simple dependency container for shared state."""
    registry: Optional[ChatRegistry] = None


class TelegramClientDep:
    """Simple dependency container for Telegram client."""
    client: Optional[TelegramClientWrapper] = None


class PhotoRegistryDep:
    """Simple dependency container for photo registry."""
    registry: Optional[PhotoRegistry] = None


async def get_chat_registry() -> ChatRegistry:
    if ChatRegistryDep.registry is None:
        raise HTTPException(status_code=500, detail="Chat registry not initialized")
    return ChatRegistryDep.registry


async def get_telegram_client() -> TelegramClientWrapper:
    if TelegramClientDep.client is None:
        raise HTTPException(status_code=500, detail="Telegram client not initialized")
    return TelegramClientDep.client


async def get_photo_registry() -> PhotoRegistry:
    if PhotoRegistryDep.registry is None:
        raise HTTPException(status_code=500, detail="Photo registry not initialized")
    return PhotoRegistryDep.registry


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


# ---------------------------------------------------------------------------
# Photo endpoints
# ---------------------------------------------------------------------------

@router.get("/photos", response_model=PhotoListResponse)
async def list_photos(registry: PhotoRegistry = Depends(get_photo_registry)):
    """List all photos with enabled status."""
    photos = registry.list_photos()
    return PhotoListResponse(
        total=len(photos),
        photos=[PhotoResponse(**p.model_dump()) for p in photos],
    )


@router.post("/photos", response_model=PhotoResponse, status_code=201)
async def upload_photo(
    file: UploadFile = File(...),
    registry: PhotoRegistry = Depends(get_photo_registry),
):
    """Upload a new photo to the pool."""
    content_type = file.content_type or ""
    if not any(content_type.startswith(p) for p in _ALLOWED_MIME_PREFIXES):
        raise HTTPException(status_code=415, detail="Only image files are allowed")

    data = await file.read()
    if len(data) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 20 MB limit")

    filename = file.filename or "upload.jpg"
    if not _SAFE_FILENAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")

    photo = registry.save_photo(filename, data)
    return PhotoResponse(**photo.model_dump())


@router.delete("/photos/{filename}", status_code=204)
async def delete_photo(
    filename: str,
    registry: PhotoRegistry = Depends(get_photo_registry),
):
    """Delete a photo from the pool."""
    if not _SAFE_FILENAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not registry.delete_photo(filename):
        raise HTTPException(status_code=404, detail="Photo not found")


@router.patch("/photos/{filename}/toggle", response_model=PhotoResponse)
async def toggle_photo(
    filename: str,
    request: PhotoToggleRequest,
    registry: PhotoRegistry = Depends(get_photo_registry),
):
    """Enable or disable a photo for sending."""
    if not _SAFE_FILENAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    photo = registry.set_enabled(filename, request.enabled)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo not found")
    return PhotoResponse(**photo.model_dump())


@router.get("/photos/{filename}/file")
async def serve_photo(
    filename: str,
    registry: PhotoRegistry = Depends(get_photo_registry),
):
    """Serve the actual image file."""
    if not _SAFE_FILENAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    path: Path = registry.photos_dir / filename
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Photo not found")
    # Ensure the resolved path is still inside photos_dir (extra safety)
    if not str(path.resolve()).startswith(str(registry.photos_dir.resolve())):
        raise HTTPException(status_code=403, detail="Forbidden")
    return FileResponse(str(path))

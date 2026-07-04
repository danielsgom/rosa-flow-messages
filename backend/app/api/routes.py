from typing import List, Optional
import re
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.modules.logger import get_logger
from app.modules.chat_registry import ChatRegistry, ConversationStatus
from app.modules.photo_registry import PhotoRegistry
from app.modules.telegram import TelegramClientWrapper
from app.modules.cost_tracker import CostTracker
from app.modules.database.repositories import ConversationRepository, CostRepository
from app.api.schemas import (
    ChatResponse, ToggleRequest, ToggleResponse, SyncResponse,
    VipRequest,
    PhotoResponse, PhotoListResponse, PhotoToggleRequest, PhotoCaptionRequest,
    ChatPhotosResponse, ChatPhotosUpdate,
    ConversationHistoryItem, ChatHistoryResponse,
    CostEntryResponse, CostSummaryResponse, ChatCostResponse,
)
from app.modules.chat_registry.models import ChatInfo

logger = get_logger(__name__)
router = APIRouter(prefix="/api")

_SAFE_FILENAME_RE = re.compile(r'^[a-zA-Z0-9_\-\.]+$')
_ALLOWED_MIME_PREFIXES = ("image/",)
_MAX_UPLOAD_BYTES = 20 * 1024 * 1024  # 20 MB


# ---------------------------------------------------------------------------
# Dependency containers (populated by main.py at startup)
# ---------------------------------------------------------------------------

class ChatRegistryDep:
    registry: Optional[ChatRegistry] = None


class TelegramClientDep:
    client: Optional[TelegramClientWrapper] = None


class PhotoRegistryDep:
    registry: Optional[PhotoRegistry] = None


class CostTrackerDep:
    tracker: Optional[CostTracker] = None


class ConvRepoDep:
    repo: Optional[ConversationRepository] = None


class CostRepoDep:
    repo: Optional[CostRepository] = None


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


async def get_cost_tracker() -> CostTracker:
    if CostTrackerDep.tracker is None:
        raise HTTPException(status_code=500, detail="Cost tracker not initialized")
    return CostTrackerDep.tracker


async def get_conv_repo() -> Optional[ConversationRepository]:
    return ConvRepoDep.repo


async def get_db_cost_repo() -> Optional[CostRepository]:
    return CostRepoDep.repo


# ---------------------------------------------------------------------------
# Helper: build ChatResponse from in-memory ChatInfo + DB aggregates
# ---------------------------------------------------------------------------

def _chat_to_response(
    chat: ChatInfo,
    total_conversations: int = 0,
    total_cost_usd: float = 0.0,
) -> ChatResponse:
    return ChatResponse(
        chat_id=chat.chat_id,
        name=chat.name,
        full_name=chat.full_name,
        username=chat.username,
        last_message_preview=chat.last_message_preview,
        last_message_at=chat.last_message_at,
        auto_enabled=chat.auto_enabled,
        conversation_status=chat.conversation_status.value,
        is_vip=chat.is_vip,
        total_conversations=total_conversations,
        total_cost_usd=total_cost_usd,
        current_session_photos=list(chat.photos_sent_filenames),
    )


@router.get("/chats", response_model=List[ChatResponse])
async def list_chats(
    registry: ChatRegistry = Depends(get_chat_registry),
    conv_repo: Optional[ConversationRepository] = Depends(get_conv_repo),
    cost_repo: Optional[CostRepository] = Depends(get_db_cost_repo),
):
    """List all discovered chats with enriched DB stats."""
    chats = await registry.list_chats()
    conv_counts = await conv_repo.count_all_by_chat() if conv_repo else {}
    cost_totals = await cost_repo.total_all_by_chat() if cost_repo else {}
    return [
        _chat_to_response(c, conv_counts.get(c.chat_id, 0), cost_totals.get(c.chat_id, 0.0))
        for c in chats
    ]


@router.post("/chats/sync", response_model=SyncResponse)
async def sync_chats(
    registry: ChatRegistry = Depends(get_chat_registry),
    telegram: TelegramClientWrapper = Depends(get_telegram_client),
    conv_repo: Optional[ConversationRepository] = Depends(get_conv_repo),
    cost_repo: Optional[CostRepository] = Depends(get_db_cost_repo),
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

    chats = await registry.list_chats()
    conv_counts = await conv_repo.count_all_by_chat() if conv_repo else {}
    cost_totals = await cost_repo.total_all_by_chat() if cost_repo else {}
    return SyncResponse(
        synced=synced_count,
        total=synced_count,
        chats=[
            _chat_to_response(c, conv_counts.get(c.chat_id, 0), cost_totals.get(c.chat_id, 0.0))
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


@router.put("/chats/{chat_id}/vip", response_model=ChatResponse)
async def set_chat_vip(
    chat_id: int,
    body: VipRequest,
    registry: ChatRegistry = Depends(get_chat_registry),
):
    """Set or unset VIP status for a chat."""
    chat = await registry.set_vip(chat_id, body.is_vip)
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
    return _chat_to_response(chat)


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


@router.patch("/photos/{filename}/caption", response_model=PhotoResponse)
async def update_photo_caption(
    filename: str,
    request: PhotoCaptionRequest,
    registry: PhotoRegistry = Depends(get_photo_registry),
):
    """Set or clear the caption for a photo."""
    if not _SAFE_FILENAME_RE.match(filename):
        raise HTTPException(status_code=400, detail="Invalid filename")
    photo = registry.set_caption(filename, request.caption)
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


# ---------------------------------------------------------------------------
# Chat photo assignment endpoints
# ---------------------------------------------------------------------------

@router.get("/chats/{chat_id}/photos", response_model=ChatPhotosResponse)
async def get_chat_photos(
    chat_id: int,
    registry: ChatRegistry = Depends(get_chat_registry),
):
    """Get the photos assigned to a specific chat."""
    filenames = await registry.get_assigned_photos(chat_id)
    return ChatPhotosResponse(chat_id=chat_id, assigned_filenames=filenames)


@router.put("/chats/{chat_id}/photos", response_model=ChatPhotosResponse)
async def set_chat_photos(
    chat_id: int,
    body: ChatPhotosUpdate,
    registry: ChatRegistry = Depends(get_chat_registry),
    photo_registry: PhotoRegistry = Depends(get_photo_registry),
):
    """Set the photos assigned to a chat (replaces the full list)."""
    known = {p.filename for p in photo_registry.list_photos()}
    invalid = [f for f in body.filenames if f not in known]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Unknown photo(s): {invalid}")

    chat = await registry.set_assigned_photos(chat_id, body.filenames)
    if chat is None:
        raise HTTPException(status_code=404, detail=f"Chat {chat_id} not found")
    return ChatPhotosResponse(chat_id=chat_id, assigned_filenames=chat.assigned_photo_filenames)


@router.get("/chats/{chat_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    chat_id: int,
    conv_repo: Optional[ConversationRepository] = Depends(get_conv_repo),
    cost_repo: Optional[CostRepository] = Depends(get_db_cost_repo),
):
    """Full conversation history for a chat with per-session photos and cost."""
    if conv_repo is None:
        raise HTTPException(status_code=503, detail="Database not available")

    conversations = await conv_repo.list_by_chat(chat_id)
    items: List[ConversationHistoryItem] = []
    for conv in conversations:
        photos = await conv_repo.get_photos(conv.id)
        cost = await cost_repo.total_by_conversation(conv.id) if cost_repo else 0.0
        items.append(
            ConversationHistoryItem(
                id=conv.id,
                started_at=conv.started_at,
                ended_at=conv.ended_at,
                turn_count=conv.turn_count,
                max_turns=conv.max_turns,
                status=conv.status,
                photos=photos,
                cost_usd=cost,
            )
        )

    return ChatHistoryResponse(
        chat_id=chat_id,
        total_conversations=len(items),
        conversations=items,
    )


@router.get("/costs/summary", response_model=CostSummaryResponse)
async def get_cost_summary(tracker: CostTracker = Depends(get_cost_tracker)):
    """Overall token usage and cost summary."""
    summary = await tracker.get_summary()
    return CostSummaryResponse(**summary.model_dump())


@router.get("/costs/by-chat", response_model=List[ChatCostResponse])
async def get_cost_by_chat(tracker: CostTracker = Depends(get_cost_tracker)):
    """Cost breakdown per chat, sorted by highest spend."""
    items = await tracker.get_by_chat()
    return [ChatCostResponse(**i.model_dump()) for i in items]


@router.get("/costs/recent", response_model=List[CostEntryResponse])
async def get_recent_costs(
    n: int = Query(default=50, ge=1, le=500),
    tracker: CostTracker = Depends(get_cost_tracker),
):
    """Most recent N cost entries (newest first)."""
    entries = await tracker.get_recent(n)
    return [CostEntryResponse(**e.model_dump()) for e in entries]


# ---------------------------------------------------------------------------
# Diagnostic endpoint
# ---------------------------------------------------------------------------

@router.get("/debug/db")
async def debug_db(
    registry: ChatRegistry = Depends(get_chat_registry),
    conv_repo: Optional[ConversationRepository] = Depends(get_conv_repo),
):
    """Returns in-memory registry state and DB stats for debugging."""
    chats_in_memory = await registry.list_chats()
    db_conv_counts = await conv_repo.count_all_by_chat() if conv_repo else {}
    return {
        "chats_in_memory": len(chats_in_memory),
        "vip_count": sum(1 for c in chats_in_memory if c.is_vip),
        "db_conversations_count": sum(db_conv_counts.values()),
        "sample": [
            {
                "chat_id": c.chat_id,
                "name": c.name,
                "is_vip": c.is_vip,
                "last_message_at": c.last_message_at.isoformat(),
            }
            for c in chats_in_memory[:5]
        ],
    }

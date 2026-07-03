import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, TYPE_CHECKING

from app.modules.logger import get_logger
from .models import ChatInfo, ConversationStatus

if TYPE_CHECKING:
    from app.modules.database.repositories import UserRepository, ConversationRepository

logger = get_logger(__name__)


def _ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure a datetime is UTC-aware. Naive datetimes (from SQLite) are assumed UTC."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


class ChatRegistry:
    """In-memory registry of discovered chats, with optional DB persistence."""

    def __init__(
        self,
        user_repo: Optional["UserRepository"] = None,
        conv_repo: Optional["ConversationRepository"] = None,
    ):
        self._chats: Dict[int, ChatInfo] = {}
        self._lock = asyncio.Lock()
        self._user_repo = user_repo
        self._conv_repo = conv_repo
        # Maps chat_id → current active DB conversation id
        self._active_conv_id: Dict[int, int] = {}

    # ------------------------------------------------------------------
    # Startup hydration
    # ------------------------------------------------------------------

    async def load_from_db(self) -> None:
        """Hydrate in-memory state from DB.  Call once at application startup."""
        if self._user_repo is None:
            logger.warning("⚠️ load_from_db called but user_repo is None — skipping")
            return

        try:
            users = await self._user_repo.get_all()
        except Exception as exc:
            logger.error(f"❌ Failed to read users from DB: {exc}", exc_info=True)
            return

        logger.info(f"💾 Found {len(users)} users in DB, loading into memory…")

        for user in users:
            try:
                filenames = json.loads(user.assigned_photo_filenames or "[]")
            except (ValueError, TypeError):
                filenames = []

            active_conv = None
            photos_in_session: List[str] = []
            if self._conv_repo:
                try:
                    active_conv = await self._conv_repo.get_active(user.chat_id)
                    if active_conv:
                        photos_in_session = await self._conv_repo.get_photos(active_conv.id)
                except Exception as exc:
                    logger.warning(f"⚠️ Failed to load conv for chat {user.chat_id}: {exc}")
                    active_conv = None

            # Normalize to UTC-aware to avoid naive/aware sort errors later
            last_at = _ensure_utc(user.updated_at) or datetime.now(timezone.utc)

            chat_info = ChatInfo(
                chat_id=user.chat_id,
                name=user.name,
                full_name=user.full_name,
                username=user.username,
                is_vip=user.is_vip,
                auto_enabled=user.auto_enabled,
                assigned_photo_filenames=filenames,
                last_message_at=last_at,
            )

            # Restore active-session state so the bot can resume after a restart
            if active_conv:
                chat_info.session_started_at = _ensure_utc(active_conv.started_at)
                chat_info.session_max_turns = active_conv.max_turns
                chat_info.turn_count = active_conv.turn_count
                chat_info.photos_sent_filenames = photos_in_session
                chat_info.photos_sent = len(photos_in_session)

            async with self._lock:
                self._chats[user.chat_id] = chat_info
                if active_conv:
                    self._active_conv_id[user.chat_id] = active_conv.id

        logger.info(
            f"💾 Loaded {len(users)} users from DB "
            f"(VIP: {sum(1 for u in users if u.is_vip)})"
        )

    # ------------------------------------------------------------------
    # Core chat management
    # ------------------------------------------------------------------

    async def register_or_update(
        self,
        chat_id: int,
        name: str = "",
        full_name: Optional[str] = None,
        username: Optional[str] = None,
        last_message: str = "",
        last_date: Optional[datetime] = None,
    ) -> ChatInfo:
        """Register a new chat or update an existing one."""
        is_new_in_memory = False
        async with self._lock:
            if chat_id in self._chats:
                chat = self._chats[chat_id]
                if name:
                    chat.name = name
                if full_name:
                    chat.full_name = full_name
                if username:
                    chat.username = username
                if last_message:
                    chat.last_message_preview = last_message
                chat.last_message_at = _ensure_utc(last_date) or datetime.now(timezone.utc)
            else:
                is_new_in_memory = True
                chat = ChatInfo(
                    chat_id=chat_id,
                    name=name or str(chat_id),
                    full_name=full_name,
                    username=username,
                    last_message_preview=last_message,
                    last_message_at=_ensure_utc(last_date) or datetime.now(timezone.utc),
                )
                self._chats[chat_id] = chat

        # Persist identity fields (awaited to avoid FK races with cost entries)
        if self._user_repo:
            try:
                db_user = await self._user_repo.upsert(chat_id, name, full_name, username)
            except Exception as exc:
                logger.error(f"❌ upsert failed for chat {chat_id}: {exc}", exc_info=True)
                db_user = None
            if is_new_in_memory and db_user:
                # User existed in DB but wasn't in memory (e.g. after restart without
                # load_from_db completing). Restore persistent state from DB so that
                # is_vip, auto_enabled and assigned photos are not silently reset.
                try:
                    filenames = json.loads(db_user.assigned_photo_filenames or "[]")
                except (ValueError, TypeError):
                    filenames = []
                async with self._lock:
                    if chat_id in self._chats:
                        self._chats[chat_id].is_vip = db_user.is_vip
                        self._chats[chat_id].auto_enabled = db_user.auto_enabled
                        self._chats[chat_id].assigned_photo_filenames = filenames

        async with self._lock:
            return self._chats[chat_id]

    async def get(self, chat_id: int) -> Optional[ChatInfo]:
        async with self._lock:
            return self._chats.get(chat_id)

    async def get_or_create(self, chat_id: int) -> ChatInfo:
        chat = await self.get(chat_id)
        if chat is None:
            chat = await self.register_or_update(chat_id)
        return chat

    async def list_chats(self) -> List[ChatInfo]:
        async with self._lock:
            return sorted(
                self._chats.values(),
                key=lambda c: c.last_message_at,
                reverse=True,
            )

    async def toggle_auto(self, chat_id: int, enabled: bool) -> Optional[ChatInfo]:
        async with self._lock:
            if chat_id not in self._chats:
                return None
            self._chats[chat_id].auto_enabled = enabled

        if self._user_repo:
            await self._user_repo.set_auto_enabled(chat_id, enabled)

        async with self._lock:
            return self._chats.get(chat_id)

    async def set_vip(self, chat_id: int, is_vip: bool) -> Optional[ChatInfo]:
        """Set VIP status for a chat."""
        async with self._lock:
            if chat_id not in self._chats:
                return None
            self._chats[chat_id].is_vip = is_vip

        if self._user_repo:
            await self._user_repo.set_vip(chat_id, is_vip)

        async with self._lock:
            return self._chats.get(chat_id)

    # ------------------------------------------------------------------
    # Conversation status
    # ------------------------------------------------------------------

    async def set_conversation_status(
        self, chat_id: int, status: ConversationStatus
    ) -> Optional[ChatInfo]:
        async with self._lock:
            if chat_id in self._chats:
                self._chats[chat_id].conversation_status = status
                return self._chats[chat_id]
            return None

    async def get_conversation_status(self, chat_id: int) -> ConversationStatus:
        async with self._lock:
            chat = self._chats.get(chat_id)
            return chat.conversation_status if chat else ConversationStatus.ACTIVE

    async def start_conversation(
        self, chat_id: int, max_turns: int = 15
    ) -> Optional[ChatInfo]:
        """Start a new conversation session for a chat."""
        async with self._lock:
            if chat_id not in self._chats:
                return None
            self._chats[chat_id].session_started_at = datetime.now(timezone.utc)
            self._chats[chat_id].turn_count = 0
            self._chats[chat_id].session_max_turns = max_turns

        if self._conv_repo:
            conv_id = await self._conv_repo.start(chat_id, max_turns)
            async with self._lock:
                self._active_conv_id[chat_id] = conv_id

        async with self._lock:
            return self._chats.get(chat_id)

    async def increment_turn(self, chat_id: int) -> Optional[ChatInfo]:
        async with self._lock:
            if chat_id not in self._chats:
                return None
            self._chats[chat_id].turn_count += 1
            return self._chats[chat_id]

    async def should_end_conversation(self, chat_id: int) -> tuple:
        async with self._lock:
            chat = self._chats.get(chat_id)
            if not chat or not chat.session_started_at:
                return False, ""
            max_turns = chat.session_max_turns or 15
            if chat.turn_count >= max_turns:
                return True, f"turns ({chat.turn_count} >= {max_turns})"
            return False, ""

    async def get_conversation_phase(self, chat_id: int) -> str:
        """
        Return the current conversation phase based on remaining turns.
        Phases: "normal", "winding_down", "farewell"
        """
        async with self._lock:
            chat = self._chats.get(chat_id)
            if not chat or not chat.session_started_at:
                return "normal"
            max_turns = chat.session_max_turns or 15
            turns_remaining = max_turns - chat.turn_count
            if turns_remaining <= 1:
                return "farewell"
            if turns_remaining <= 3:
                return "winding_down"
            return "normal"

    async def get_active_conversation_id(self, chat_id: int) -> Optional[int]:
        """Return the DB id of the current active conversation, or None."""
        async with self._lock:
            return self._active_conv_id.get(chat_id)

    async def enter_closing(self, chat_id: int, turns: int = 2) -> None:
        async with self._lock:
            if chat_id in self._chats:
                self._chats[chat_id].conversation_status = ConversationStatus.CLOSING
                self._chats[chat_id].closing_turns_left = turns

    async def decrement_closing(self, chat_id: int) -> int:
        async with self._lock:
            if chat_id not in self._chats:
                return 0
            self._chats[chat_id].closing_turns_left = max(
                0, self._chats[chat_id].closing_turns_left - 1
            )
            return self._chats[chat_id].closing_turns_left

    async def reset_conversation(self, chat_id: int) -> Optional[ChatInfo]:
        """Reset session tracking. Closes the active DB conversation if present."""
        turn_count = 0
        conv_id = None
        async with self._lock:
            if chat_id not in self._chats:
                return None
            turn_count = self._chats[chat_id].turn_count
            conv_id = self._active_conv_id.pop(chat_id, None)
            self._chats[chat_id].session_started_at = None
            self._chats[chat_id].turn_count = 0
            self._chats[chat_id].photos_sent = 0
            self._chats[chat_id].photos_sent_filenames = []
            self._chats[chat_id].closing_turns_left = 0
            self._chats[chat_id].last_photo_turn = 0

        if self._conv_repo and conv_id:
            await self._conv_repo.close(conv_id, turn_count)

        async with self._lock:
            return self._chats.get(chat_id)

    # ------------------------------------------------------------------
    # Photo tracking
    # ------------------------------------------------------------------

    async def update_last_photo_turn(self, chat_id: int, turn: int) -> None:
        async with self._lock:
            if chat_id in self._chats:
                self._chats[chat_id].last_photo_turn = turn

    async def set_assigned_photos(
        self, chat_id: int, filenames: List[str]
    ) -> Optional[ChatInfo]:
        async with self._lock:
            if chat_id not in self._chats:
                return None
            self._chats[chat_id].assigned_photo_filenames = list(filenames)

        if self._user_repo:
            await self._user_repo.set_assigned_photos(chat_id, filenames)

        async with self._lock:
            return self._chats.get(chat_id)

    async def get_assigned_photos(self, chat_id: int) -> List[str]:
        async with self._lock:
            chat = self._chats.get(chat_id)
            return list(chat.assigned_photo_filenames) if chat else []

    async def increment_photos_sent(
        self, chat_id: int, filename: str = ""
    ) -> Optional[ChatInfo]:
        conv_id = None
        async with self._lock:
            if chat_id not in self._chats:
                return None
            self._chats[chat_id].photos_sent += 1
            if filename:
                self._chats[chat_id].photos_sent_filenames.append(filename)
            conv_id = self._active_conv_id.get(chat_id)

        if self._conv_repo and conv_id and filename:
            await self._conv_repo.add_photo(conv_id, filename)

        async with self._lock:
            return self._chats.get(chat_id)

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    async def get_last_message_at(self, chat_id: int) -> Optional[datetime]:
        async with self._lock:
            chat = self._chats.get(chat_id)
            return chat.last_message_at if chat else None

    async def get_or_create(self, chat_id: int) -> ChatInfo:
        """Get existing chat or create a new one."""
        chat = await self.get(chat_id)
        if chat is None:
            chat = await self.register_or_update(chat_id)
        return chat

    async def list_chats(self) -> List[ChatInfo]:
        """List all discovered chats, sorted by last message descending."""
        async with self._lock:
            return sorted(
                self._chats.values(),
                key=lambda c: c.last_message_at,
                reverse=True,
            )

    async def toggle_auto(self, chat_id: int, enabled: bool) -> Optional[ChatInfo]:
        """Toggle auto-response for a chat."""
        async with self._lock:
            if chat_id in self._chats:
                self._chats[chat_id].auto_enabled = enabled
                return self._chats[chat_id]
            return None

    async def set_conversation_status(
        self, chat_id: int, status: ConversationStatus
    ) -> Optional[ChatInfo]:
        """Set the conversation status for a chat."""
        async with self._lock:
            if chat_id in self._chats:
                self._chats[chat_id].conversation_status = status
                return self._chats[chat_id]
            return None

    async def get_conversation_status(self, chat_id: int) -> ConversationStatus:
        """Get the conversation status for a chat."""
        async with self._lock:
            chat = self._chats.get(chat_id)
            return chat.conversation_status if chat else ConversationStatus.ACTIVE

    async def start_conversation(self, chat_id: int, max_turns: int = 15) -> Optional[ChatInfo]:
        """Start a new conversation session for a chat."""
        async with self._lock:
            if chat_id not in self._chats:
                return None
            self._chats[chat_id].session_started_at = datetime.now(timezone.utc)
            self._chats[chat_id].turn_count = 0
            self._chats[chat_id].session_max_turns = max_turns
            return self._chats[chat_id]

    async def increment_turn(self, chat_id: int) -> Optional[ChatInfo]:
        """Increment the turn count for a chat."""
        async with self._lock:
            if chat_id not in self._chats:
                return None
            self._chats[chat_id].turn_count += 1
            return self._chats[chat_id]

    async def should_end_conversation(self, chat_id: int) -> tuple[bool, str]:
        """
        Check if a conversation should end based on turn limit.
        Returns (should_end, reason).
        """
        async with self._lock:
            chat = self._chats.get(chat_id)
            if not chat or not chat.session_started_at:
                return False, ""

            max_turns = chat.session_max_turns or 15
            if chat.turn_count >= max_turns:
                return True, f"turns ({chat.turn_count} >= {max_turns})"

            return False, ""

    async def get_conversation_phase(self, chat_id: int) -> str:
        """
        Return the current conversation phase based on remaining turns.
        Phases: "normal", "winding_down", "farewell"
        """
        async with self._lock:
            chat = self._chats.get(chat_id)
            if not chat or not chat.session_started_at:
                return "normal"
            max_turns = chat.session_max_turns or 15
            turns_remaining = max_turns - chat.turn_count
            if turns_remaining <= 1:
                return "farewell"
            if turns_remaining <= 3:
                return "winding_down"
            return "normal"

    async def enter_closing(self, chat_id: int, turns: int = 2) -> None:
        """Transition conversation to CLOSING state after farewell is sent."""
        async with self._lock:
            if chat_id in self._chats:
                self._chats[chat_id].conversation_status = ConversationStatus.CLOSING
                self._chats[chat_id].closing_turns_left = turns

    async def decrement_closing(self, chat_id: int) -> int:
        """Decrement closing turns counter. Returns remaining turns."""
        async with self._lock:
            if chat_id not in self._chats:
                return 0
            self._chats[chat_id].closing_turns_left = max(
                0, self._chats[chat_id].closing_turns_left - 1
            )
            return self._chats[chat_id].closing_turns_left

    async def update_last_photo_turn(self, chat_id: int, turn: int) -> None:
        """Record the turn at which a photo was last sent."""
        async with self._lock:
            if chat_id in self._chats:
                self._chats[chat_id].last_photo_turn = turn

    async def set_assigned_photos(self, chat_id: int, filenames: List[str]) -> Optional[ChatInfo]:
        """Set the list of photos assigned to this chat (empty = use all enabled)."""
        async with self._lock:
            if chat_id not in self._chats:
                return None
            self._chats[chat_id].assigned_photo_filenames = list(filenames)
            return self._chats[chat_id]

    async def get_assigned_photos(self, chat_id: int) -> List[str]:
        """Return the filenames assigned to this chat."""
        async with self._lock:
            chat = self._chats.get(chat_id)
            return list(chat.assigned_photo_filenames) if chat else []

    async def increment_photos_sent(self, chat_id: int, filename: str = "") -> Optional[ChatInfo]:
        """Increment the photos sent count for a chat, optionally recording the filename."""
        async with self._lock:
            if chat_id not in self._chats:
                return None
            self._chats[chat_id].photos_sent += 1
            if filename:
                self._chats[chat_id].photos_sent_filenames.append(filename)
            return self._chats[chat_id]

    async def reset_conversation(self, chat_id: int) -> Optional[ChatInfo]:
        """Reset session tracking for a chat."""
        async with self._lock:
            if chat_id not in self._chats:
                return None
            self._chats[chat_id].session_started_at = None
            self._chats[chat_id].turn_count = 0
            self._chats[chat_id].photos_sent = 0
            self._chats[chat_id].photos_sent_filenames = []
            self._chats[chat_id].closing_turns_left = 0
            self._chats[chat_id].last_photo_turn = 0
            return self._chats[chat_id]

    async def get_last_message_at(self, chat_id: int) -> Optional[datetime]:
        """Get the timestamp of the last message in a chat."""
        async with self._lock:
            chat = self._chats.get(chat_id)
            return chat.last_message_at if chat else None

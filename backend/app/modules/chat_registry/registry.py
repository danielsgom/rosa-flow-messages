import asyncio
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from .models import ChatInfo, ConversationStatus


class ChatRegistry:
    """In-memory registry of discovered chats."""

    def __init__(self):
        self._chats: Dict[int, ChatInfo] = {}
        self._lock = asyncio.Lock()

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
                chat.last_message_at = last_date or datetime.now(timezone.utc)
            else:
                chat = ChatInfo(
                    chat_id=chat_id,
                    name=name or str(chat_id),
                    full_name=full_name,
                    username=username,
                    last_message_preview=last_message,
                    last_message_at=last_date or datetime.now(timezone.utc),
                )
                self._chats[chat_id] = chat
            return chat

    async def get(self, chat_id: int) -> Optional[ChatInfo]:
        """Get a chat by ID."""
        async with self._lock:
            return self._chats.get(chat_id)

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

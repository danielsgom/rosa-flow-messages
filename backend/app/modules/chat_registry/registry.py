import asyncio
from datetime import datetime
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
        last_message: str = "",
        last_date: Optional[datetime] = None,
    ) -> ChatInfo:
        """Register a new chat or update an existing one."""
        async with self._lock:
            if chat_id in self._chats:
                chat = self._chats[chat_id]
                chat.name = name or chat.name
                chat.last_message_preview = last_message or chat.last_message_preview
                chat.last_message_at = last_date or datetime.now()
            else:
                chat = ChatInfo(
                    chat_id=chat_id,
                    name=name or str(chat_id),
                    last_message_preview=last_message,
                    last_message_at=last_date or datetime.now(),
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

from telethon import TelegramClient
from telethon.sessions import StringSession
from pathlib import Path
from typing import Optional

from app.modules.logger import get_logger

logger = get_logger(__name__)


class TelegramClientWrapper:
    """Wrapper around Telethon's TelegramClient."""

    def __init__(self, api_id: int, api_hash: str, session_name: str = "rosa_session"):
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.session_path = f"sessions/{session_name}"
        Path("sessions").mkdir(exist_ok=True)
        self.client: Optional[TelegramClient] = None

    async def connect(self) -> None:
        """Initialize and connect the Telegram client."""
        self.client = TelegramClient(self.session_path, self.api_id, self.api_hash)
        await self.client.connect()
        logger.info("Telegram client connected")

    async def authorize(self, phone: str) -> bool:
        """Authorize the client, requesting code if needed."""
        if not self.client:
            await self.connect()

        if not await self.client.is_user_authorized():
            await self.client.start(phone=phone)
            logger.info("Telegram client authenticated")
            return True
        else:
            logger.info("Telegram client already authorized")
            return True

    def is_authorized(self) -> bool:
        """Check if user is authorized (non-blocking, sync wrapper)."""
        if not self.client:
            return False
        return self.client.is_connected() and self.client.session is not None

    async def start(self, phone: str) -> None:
        """Start the client with authentication."""
        if not self.client:
            await self.connect()

        if not await self.client.is_user_authorized():
            await self.client.start(phone=phone)
            logger.info("Telegram client authenticated")
        else:
            logger.info("Telegram client already authorized")

    async def disconnect(self) -> None:
        """Disconnect the client."""
        if self.client:
            await self.client.disconnect()
            logger.info("Telegram client disconnected")

    def get_client(self) -> TelegramClient:
        """Get the underlying TelegramClient."""
        if not self.client:
            raise RuntimeError("Client not connected")
        return self.client

    async def get_me(self) -> dict:
        """Get information about the current user."""
        return await self.client.get_me()

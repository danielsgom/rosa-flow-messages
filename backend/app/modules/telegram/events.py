from telethon import events
from telethon.tl.types import User

from app.modules.logger import get_logger
from .models import TelegramMessage

logger = get_logger(__name__)


class MessageEventHandler:
    """Handles incoming Telegram message events."""

    def __init__(self, client_wrapper, trigger_engine):
        self.client_wrapper = client_wrapper
        self.trigger_engine = trigger_engine
        self._my_id: int = 0

    async def setup(self):
        """Register event handlers and get our own user ID."""
        client = self.client_wrapper.get_client()

        me = await client.get_me()
        self._my_id = me.id
        logger.info(f"Logged in as {me.first_name} (ID: {self._my_id})")

        @client.on(events.NewMessage(incoming=True))
        async def _handler(event):
            await self._handle_message(event)

    async def _handle_message(self, event):
        """Process a single incoming message event."""
        message = event.message

        if not message.text:
            return

        # Get sender info
        sender = await event.get_sender()
        chat = await event.get_chat()

        chat_id = chat.id
        sender_id = sender.id if sender else 0

        # Get display name
        name = getattr(chat, 'first_name', '') or getattr(chat, 'title', '')
        if not name and sender:
            name = f"{getattr(sender, 'first_name', '')} {getattr(sender, 'last_name', '')}".strip()

        logger.info(f"Message from {name} (chat {chat_id}): {message.text[:50]}")

        tg_message = TelegramMessage(
            chat_id=chat_id,
            sender_id=sender_id,
            text=message.text,
            date=message.date,
            is_outgoing=False,
        )

        # Process through trigger engine
        await self.trigger_engine.process_message(
            chat_id=chat_id,
            sender_id=sender_id,
            text=message.text,
            my_id=self._my_id,
        )

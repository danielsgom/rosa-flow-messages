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
        self._setup_done: bool = False

    async def setup(self):
        """Register event handlers and get our own user ID."""
        if self._setup_done:
            return
        self._setup_done = True

        client = self.client_wrapper.get_client()

        me = await client.get_me()
        self._my_id = me.id
        logger.info(f"Logged in as {me.first_name} (ID: {self._my_id})")

        @client.on(events.NewMessage(incoming=True))
        async def _handler(event):
            await self._handle_message(event)

    async def _handle_message(self, event):
        """Process a single incoming message event."""
        try:
            await self._process_message_event(event)
        except Exception as exc:
            logger.error(f"Error handling message event: {exc}", exc_info=True)
            raise

    @staticmethod
    def _detect_media_type(message) -> str:
        """
        Return 'audio', 'image', 'video', or '' based on message media.
        Voice notes and audio files → 'audio'.
        Photos and stickers        → 'image'.
        Videos, GIFs, video notes  → 'video'.
        """
        if message.voice or message.audio:
            return "audio"
        if message.photo or message.sticker:
            return "image"
        if message.video or message.gif or message.video_note:
            return "video"
        return ""

    async def _process_message_event(self, event):
        """Internal message processing logic."""
        message = event.message

        media_type = self._detect_media_type(message)
        text = message.text or ""

        # Ignore messages with no text AND no recognised media
        if not text and not media_type:
            return

        # Get sender info (User entity)
        sender = await event.get_sender()
        chat = await event.get_chat()

        chat_id = chat.id
        sender_id = sender.id if sender else 0

        # Get display name
        name = getattr(chat, 'first_name', '') or getattr(chat, 'title', '')
        if not name and sender:
            name = getattr(sender, 'first_name', '') or str(chat_id)

        # Get full name (first + last)
        full_name = None
        username = None
        if isinstance(sender, User):
            first = getattr(sender, 'first_name', '') or ''
            last = getattr(sender, 'last_name', '') or ''
            full_name = f"{first} {last}".strip()
            username = getattr(sender, 'username', None)
            if not name:
                name = first or str(chat_id)

        preview = text[:50] if text else f"[{media_type}]"
        logger.info(
            f"Message from {full_name or name} (@{username or 'N/A'}) [chat {chat_id}]: {preview}")

        tg_message = TelegramMessage(
            chat_id=chat_id,
            sender_id=sender_id,
            text=text,
            date=message.date,
            is_outgoing=False,
        )

        # Process through trigger engine
        await self.trigger_engine.process_message(
            chat_id=chat_id,
            sender_id=sender_id,
            text=text,
            my_id=self._my_id,
            name=name,
            full_name=full_name,
            username=username,
            date=message.date,
            media_type=media_type,
        )

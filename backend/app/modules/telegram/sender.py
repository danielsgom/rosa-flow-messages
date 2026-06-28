import asyncio
import random

from app.modules.logger import get_logger

logger = get_logger(__name__)


class TelegramSender:
    """Sends messages through Telegram."""

    def __init__(self, client_wrapper):
        self.client_wrapper = client_wrapper

    async def send_message(self, entity, text: str) -> None:
        """
        Send a message to a Telegram entity.
        If the text contains double newlines (\n\n), splits into multiple
        messages to emulate WhatsApp multi-message behavior.
        A small random delay (1-3s) is added between consecutive messages.
        """
        client = self.client_wrapper.get_client()

        # Split by double newline to separate independent messages
        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not parts:
            parts = [text.strip()]

        for idx, msg_text in enumerate(parts):
            # Small delay between consecutive messages (natural typing time)
            delay = 0.0
            if idx > 0:
                delay = random.uniform(1.0, 3.0)
                await asyncio.sleep(delay)

            try:
                await client.send_message(entity, msg_text)
                if idx > 0:
                    logger.info(f"Message sent to {entity} (+{delay:.1f}s delay)")
                else:
                    logger.info(f"Message sent to {entity}")
            except Exception as exc:
                logger.error(f"Failed to send message to {entity}: {exc}")
                raise

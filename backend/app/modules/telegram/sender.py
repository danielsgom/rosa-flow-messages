import asyncio
import random
from pathlib import Path

from app.modules.logger import get_logger

logger = get_logger(__name__)


class TelegramSender:
    """Sends messages through Telegram with realistic human-like presence."""

    def __init__(self, client_wrapper):
        self.client_wrapper = client_wrapper

    async def send_message(self, entity, text: str) -> None:
        """
        Send a message (or split messages) to a Telegram entity.

        For each message part:
          1. Mark the conversation as read (clears unread badge).
          2. Show the “typing…” indicator while simulating reading + composing time.
          3. Send the message.

        Timing: base reading/thinking delay + proportional typing time.
        """
        client = self.client_wrapper.get_client()

        # Mark conversation as read so the unread badge clears before typing appears
        try:
            await client.send_read_acknowledge(entity)
        except Exception:
            pass  # non-critical — never block sending because of this

        parts = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not parts:
            parts = [text.strip()]

        for idx, msg_text in enumerate(parts):
            chars = len(msg_text)
            # First message: shorter reading pause (already waited the debounce delay).
            # Subsequent parts: inter-message gap as if finishing one thought and starting next.
            if idx == 0:
                base = random.uniform(0.4, 1.2)
            else:
                base = random.uniform(0.8, 1.8)
            typing_time = min(chars * random.uniform(0.035, 0.055), 12.0)
            total_delay = base + typing_time

            # Show “typing…” indicator while composing; fall back to plain sleep on error
            try:
                async with client.action(entity, 'typing'):
                    await asyncio.sleep(total_delay)
            except Exception:
                await asyncio.sleep(total_delay)

            try:
                await client.send_message(entity, msg_text)
                logger.info(f"Message sent to {entity} (typed {total_delay:.1f}s)")
            except Exception as exc:
                logger.error(f"Failed to send message to {entity}: {exc}")
                raise

    async def send_photo(self, entity, photo_path: Path, caption: str = "") -> None:
        """Send a photo file to a Telegram entity."""
        client = self.client_wrapper.get_client()
        try:
            await client.send_file(entity, str(photo_path), caption=caption)
            logger.info(f"Photo sent to {entity}: {photo_path.name}")
        except Exception as exc:
            logger.error(f"Failed to send photo to {entity}: {exc}")
            raise

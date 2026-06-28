from app.modules.logger import get_logger

logger = get_logger(__name__)


class TelegramSender:
    """Sends messages through Telegram."""

    def __init__(self, client_wrapper):
        self.client_wrapper = client_wrapper

    async def send_message(self, entity, text: str) -> None:
        """
        Send a message to a Telegram entity.

        Args:
            entity: Chat ID, username, or entity object.
            text: The message text to send.
        """
        client = self.client_wrapper.get_client()
        try:
            await client.send_message(entity, text)
            logger.info(f"Message sent to {entity}")
        except Exception as exc:
            logger.error(f"Failed to send message to {entity}: {exc}")
            raise

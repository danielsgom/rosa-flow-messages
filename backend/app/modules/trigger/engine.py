import asyncio
from datetime import datetime

from app.modules.logger import get_logger
from app.config import Settings
from app.modules.chat_registry import ChatRegistry, ConversationStatus
from app.modules.context import ContextManager
from app.modules.openai_client import ResponseGenerator
from app.modules.telegram import TelegramSender
from .models import TriggerResult
from .delay import calculate_delay
from .farewell_detector import is_farewell
from .rules import TriggerRules

logger = get_logger(__name__)


class TriggerEngine:
    """Orchestrates the decision flow for automatic responses."""

    def __init__(
        self,
        chat_registry: ChatRegistry,
        context_manager: ContextManager,
        generator: ResponseGenerator,
        sender: TelegramSender,
        settings: Settings,
    ):
        self.chat_registry = chat_registry
        self.context_manager = context_manager
        self.generator = generator
        self.sender = sender
        self.settings = settings
        self.rules = TriggerRules()

    async def process_message(
        self,
        chat_id: int,
        sender_id: int,
        text: str,
        my_id: int = 0,
    ) -> TriggerResult:
        """
        Process an incoming message and decide whether to respond.

        Args:
            chat_id: The chat ID.
            sender_id: The sender's ID.
            text: The message text.
            my_id: Our own Telegram ID to detect outbound messages.

        Returns:
            TriggerResult with decision details.
        """
        # 1. Register the chat
        chat = await self.chat_registry.register_or_update(
            chat_id=chat_id,
            last_message=text,
            last_date=datetime.now(),
        )

        # 2. Ignore our own outbound messages
        if self.rules.is_message_from_me(sender_id, my_id):
            logger.debug(f"Ignoring outbound message from chat {chat_id}")
            return TriggerResult(should_respond=False, reason="outbound_message")

        # 3. Detect farewell → close conversation
        if is_farewell(text):
            logger.info(f"Farewell detected in chat {chat_id}. Closing conversation.")
            await self.chat_registry.set_conversation_status(
                chat_id, ConversationStatus.CLOSED
            )
            # Optional: send a brief farewell back
            return TriggerResult(should_respond=False, reason="farewell_detected")

        # 4. Reactivate if conversation was closed and new message arrives
        status = await self.chat_registry.get_conversation_status(chat_id)
        if status == ConversationStatus.CLOSED:
            logger.info(f"Reactivating conversation for chat {chat_id}")
            await self.chat_registry.set_conversation_status(
                chat_id, ConversationStatus.ACTIVE
            )
            # Optionally reset history for a "fresh start" feel
            # self.context_manager.clear_history(chat_id)

        # 5. Check if auto-response is enabled
        if not chat.auto_enabled:
            logger.debug(f"Auto-response disabled for chat {chat_id}")
            # Still record the message for context if they enable it later
            self.context_manager.add_to_history(chat_id, "user", text)
            return TriggerResult(should_respond=False, reason="auto_disabled")

        # 6. Check cooldown
        if self.rules.is_in_cooldown(chat_id):
            logger.debug(f"Cooldown active for chat {chat_id}")
            self.context_manager.add_to_history(chat_id, "user", text)
            return TriggerResult(should_respond=False, reason="cooldown")

        # 7. Build context and generate response
        self.context_manager.add_to_history(chat_id, "user", text)
        messages = self.context_manager.build_context(chat_id, text)

        try:
            response_text = await self.generator.generate(messages)
        except Exception as exc:
            logger.error(f"Failed to generate response: {exc}")
            return TriggerResult(should_respond=False, reason="generation_error")

        # 8. Apply delay
        delay = calculate_delay(
            self.settings.response_delay_seconds_min,
            self.settings.response_delay_seconds_max,
            self.settings.response_delay_enabled,
        )

        if delay > 0:
            logger.info(f"Waiting {delay:.2f}s before responding to chat {chat_id}")
            await asyncio.sleep(delay)

        # 9. Send response
        try:
            await self.sender.send_message(chat_id, response_text)
            self.rules.record_bot_message(chat_id)
            self.context_manager.add_to_history(chat_id, "assistant", response_text)
            logger.info(f"Sent response to chat {chat_id}")
            return TriggerResult(
                should_respond=True,
                reason="success",
                delay_seconds=delay,
            )
        except Exception as exc:
            logger.error(f"Failed to send message: {exc}")
            return TriggerResult(should_respond=False, reason="send_error")

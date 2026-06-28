import asyncio
from datetime import datetime
from typing import Optional, Dict, List

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
    """Orchestrates the decision flow for automatic responses with debounce."""

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
        
        # Debounce state per chat
        self._pending_tasks: Dict[int, asyncio.Task] = {}
        self._pending_messages: Dict[int, List[str]] = {}
        self._lock = asyncio.Lock()

    async def process_message(
        self,
        chat_id: int,
        sender_id: int,
        text: str,
        my_id: int = 0,
        name: str = "",
        full_name: Optional[str] = None,
        username: Optional[str] = None,
        date: Optional[datetime] = None,
    ) -> TriggerResult:
        """
        Process an incoming message with debounce.
        
        Messages are accumulated during the delay window. If a new message
        arrives before the timer expires, the timer resets and messages
        are batched into a single OpenAI call.
        """
        # 1. Register the chat
        chat = await self.chat_registry.register_or_update(
            chat_id=chat_id,
            name=name,
            full_name=full_name,
            username=username,
            last_message=text,
            last_date=date or datetime.now(),
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
            return TriggerResult(should_respond=False, reason="farewell_detected")

        # 4. Reactivate if conversation was closed and new message arrives
        status = await self.chat_registry.get_conversation_status(chat_id)
        if status == ConversationStatus.CLOSED:
            logger.info(f"Reactivating conversation for chat {chat_id}")
            await self.chat_registry.set_conversation_status(
                chat_id, ConversationStatus.ACTIVE
            )

        # 5. Check if auto-response is enabled
        if not chat.auto_enabled:
            logger.debug(f"Auto-response disabled for chat {chat_id}")
            self.context_manager.add_to_history(chat_id, "user", text)
            return TriggerResult(should_respond=False, reason="auto_disabled")

        # 6. Check cooldown
        if self.rules.is_in_cooldown(chat_id):
            logger.debug(f"Cooldown active for chat {chat_id}")
            self.context_manager.add_to_history(chat_id, "user", text)
            return TriggerResult(should_respond=False, reason="cooldown")

        # 7. DEBOUNCE: Accumulate message and (re)start timer
        async with self._lock:
            # Cancel existing timer for this chat
            if chat_id in self._pending_tasks:
                self._pending_tasks[chat_id].cancel()
                try:
                    await self._pending_tasks[chat_id]
                except asyncio.CancelledError:
                    pass
                logger.debug(f"Debounce timer reset for chat {chat_id}")
            
            # Add message to pending buffer
            if chat_id not in self._pending_messages:
                self._pending_messages[chat_id] = []
            self._pending_messages[chat_id].append(text)
            
            # Calculate delay
            delay = calculate_delay(
                self.settings.response_delay_seconds_min,
                self.settings.response_delay_seconds_max,
                self.settings.response_delay_enabled,
            )
            
            logger.info(
                f"⏳ Debounce started for chat {chat_id}: "
                f"{len(self._pending_messages[chat_id])} message(s), "
                f"waiting {delay:.1f}s..."
            )
            
            # Start new timer
            task = asyncio.create_task(
                self._process_after_delay(chat_id, delay)
            )
            self._pending_tasks[chat_id] = task
            
            return TriggerResult(
                should_respond=False,
                reason="debounce_waiting",
                delay_seconds=delay,
            )

    async def _process_after_delay(self, chat_id: int, delay: float):
        """Process accumulated messages after the debounce delay expires."""
        try:
            await asyncio.sleep(delay)
            
            async with self._lock:
                # Get accumulated messages
                messages = self._pending_messages.get(chat_id, [])
                if not messages:
                    return
                
                # Clear state
                self._pending_messages.pop(chat_id, None)
                self._pending_tasks.pop(chat_id, None)
            
            logger.info(
                f"⏰ Debounce expired for chat {chat_id}. "
                f"Processing {len(messages)} accumulated message(s)."
            )
            
            # Add ALL accumulated messages to history individually
            for msg in messages:
                self.context_manager.add_to_history(chat_id, "user", msg)
            
            # Build context: history already contains all messages.
            # Pass the last message as 'new_message' so build_context includes it properly
            last_message = messages[-1]
            context_messages = self.context_manager.build_context(chat_id, last_message)
            
            # Generate single response for all messages
            try:
                response_text = await self.generator.generate(context_messages)
            except Exception as exc:
                logger.error(f"Failed to generate response: {exc}")
                return
            
            # Send response
            try:
                await self.sender.send_message(chat_id, response_text)
                self.rules.record_bot_message(chat_id)
                self.context_manager.add_to_history(chat_id, "assistant", response_text)
                logger.info(
                    f"✅ Sent batched response to chat {chat_id} "
                    f"({len(messages)} msg → 1 response, {len(response_text)} chars)"
                )
            except Exception as exc:
                logger.error(f"Failed to send message: {exc}")
                
        except asyncio.CancelledError:
            logger.debug(f"Debounce timer cancelled for chat {chat_id}")
            raise

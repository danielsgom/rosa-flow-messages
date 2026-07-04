import asyncio
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from app.modules.logger import get_logger
from app.config import Settings
from app.modules.chat_registry import ChatRegistry, ConversationStatus
from app.modules.context import ContextManager
from app.modules.context.manager import _detect_heat
from app.modules.openai_client import ResponseGenerator
from app.modules.photo_registry import PhotoRegistry
from app.modules.telegram import TelegramSender
from .models import TriggerResult
from .delay import calculate_delay
from .farewell_detector import is_farewell
from .photo_request_detector import is_photo_request
from .rules import TriggerRules

logger = get_logger(__name__)

_ASTERISK_RE = re.compile(r'\*[^*\n]+\*')
_PARENTHETICAL_RE = re.compile(r'\*?\(.{5,}?\)', re.DOTALL)
_OPEN_PAREN_RE = re.compile(r'\s*\*?\([^)]{5,}$', re.DOTALL)
_MARKDOWN_IMAGE_RE = re.compile(r'!\[[^\]]*\]\([^)]*\)')  # ![alt](url)
_MARKDOWN_IMAGE_BARE_RE = re.compile(r'!\[[^\]]{5,}\]')   # ![long description] without url

# Fixed replies for audio messages — no AI needed
_AUDIO_REPLIES = [
    "amor, no me mandes audios 🙈 escríbeme mejor",
    "ayyy no puedo escucharlo ahora mismo, cuéntamelo por aquí 😘",
    "prefiero que me lo escribas, así lo saboreo más 🥷",
    "no puedo poner el audio ahora, escríbeme lo que ibas a decir 💛",
]

# Farewell messages — warm/neutral (calm conversations or user-initiated goodbye)
_FAREWELL_MESSAGES = [
    "jooo bonito mío tengo que irme ya, me espera una cosa y no puedo más 😅 estate pendiente del canal que te dejo algo para ti 🔥 luego hablamos?",
    "mi rey me piro ya, que tengo el gym esperándome y no puedo faltar más 😅 te dejo algo en el canal para que sigas calentito, besos 💋",
    "ufff cariño se me acaba el tiempo, tengo que salir corriendo 🙈 ya sabes dónde encontrarme, te dejo algo rico en el canal 😏 mañana seguimos?",
    "ay mi amor me voy ya, que me llama mi amiga y lleva esperando un rato 😩 pero te dejo una sorpresita en el canal 🔥 cuídate bonito",
    "cariño me tengo que escapar, que tengo una sesión de fotos ahora y se me hace tarde 📸 te dejo algo del shooting en el canal para ti 😏 hasta luego mi rey",
    "amore se ha acabado el tiempo y me tengo que ir ya 🙏 te dejo algo rico en el canal para que sigas tú solo 🔥 mañana te escribo?",
    "me llaman y debo salir, qué pena porque estaba muy a gusto contigo 😘 estate pendiente del canal que te dejo algo 🔥 luego seguimos?",
]

# Farewell messages — HOT (turn limit hit mid-sexting; no VIP push, leaves them wanting more)
_FAREWELL_MESSAGES_HOT = [
    "joder mi rey, me tienes al límite y justo ahora me llaman 😩 te lo cobro mañana eh 😈",
    "ay que rabia, estaba tan a gusto contigo y me tengo que ir ya 🙈 mañana seguimos donde lo dejamos mi rey 🔥",
    "nooo que me tengo que ir ahora 😩 me vas a tener pensando en esto toda la tarde... te escribo luego mi rey?",
    "ufff me pilla en el peor momento 😈 no te enfrí­es que en nada vuelvo 🔥",
    "me están llamando y no puedo no coger 😩 pero mi rey, hoy me has puesto... ya te cuento luego todo 😈",
    "jooo me tengo que escapar ya 🙈 pero esto no queda así, eh? mañana seguimos donde lo dejamos 🔥",
    "qué mala suerte mi rey, justo ahora... voy a ir pensando en ti mientras 😏 hablamos luego?",
]

# Closing replies — warm (user keeps messaging while Rosa is already leaving)
_CLOSING_MESSAGES = [
    "jajaj ay bonito mío, me voy ya en serio 😘",
    "cuídate mucho mi rey 💋",
    "dale, hasta luego guapo 🫶",
    "jajaja que cabezón eres, venga me voy ya eh 😏",
    "besitos mi amor, hasta la próxima 😘",
    "venga que me piro de verdad ahora 🏃‍♀️💨",
    "mi rey ya me voy, portate bien 😈",
]

# Closing replies — HOT (leave them wanting more, no VIP push)
_CLOSING_MESSAGES_HOT = [
    "ya me fui mi rey, en serio 🙈 pero mañana seguimos 🔥",
    "dale bonito, te escribo 😈",
    "jajaj para ya que me pones 😏 luego hablamos",
    "venga mi rey, hasta mañana 💋",
    "me voy ya en serio... pero te tengo muy presente 🔥",
    "sí sí, hasta luego guapo 😈",
    "dale, mañana me lo cobras 😏",
]

# Grace turns allowed when the turn limit is hit in the middle of hot sexting
_GRACE_MAX = 2

# Trivial replies — for very short acks ("si", "ok", single emoji) that need no LLM
_TRIVIAL_REPLIES = [
    "jajaj 😘",
    "😏",
    "🔥",
    "qué rico mi rey 😈",
    "jajaj ay bonito 💋",
    "sí mi rey 😈",
    "eso sí que me gusta 🔥",
    "qué cosas tienes mi rey 😏",
    "me encanta cuando dices eso 😈",
    "jajaj 💋",
]

# Fixed teaser messages that accompany a photo Rosa is sending RIGHT NOW.
# Generated WITHOUT the LLM so Rosa can never contradict herself with excuses
# ("ya te he mandado bastante") or VIP/canal mentions while actually sending one.
# No body-part descriptions, no promises, no channel references.
_PHOTO_TEASERS = [
    "mira lo que te acabo de hacer 🔥",
    "toma, solo para ti 😏",
    "esto para que no te olvides de mí 😈",
    "para que te pongas más a tono 🔥",
    "mira bien lo que te mando 👀",
    "toma bonito, disfrútalo 😈",
    "aquí tienes, para ti 💦",
    "que lo disfrutes mi rey 🔥",
    "mira lo que tengo para ti 😏",
    "toma, que te lo has ganado 😈",
]


def _sanitize_response(text: str) -> str:
    """Remove asterisk-wrapped text, parentheticals, and markdown image tags."""
    text = _ASTERISK_RE.sub('', text)
    text = _PARENTHETICAL_RE.sub('', text)
    text = _OPEN_PAREN_RE.sub('', text)
    text = _MARKDOWN_IMAGE_RE.sub('', text)
    text = _MARKDOWN_IMAGE_BARE_RE.sub('', text)
    text = re.sub(r'  +', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _enforce_message_limit(text: str, max_blocks: int = 2) -> str:
    """Hard-truncate to at most max_blocks double-newline-separated messages."""
    blocks = [b.strip() for b in text.split('\n\n') if b.strip()]
    return '\n\n'.join(blocks[:max_blocks])


_TRIVIAL_RE = re.compile(
    r'^(?:'
    r'[\U0001F300-\U0001FFFF\u2600-\u27BF\uFE00-\uFE0F]+|'  # only emojis
    r'(?:s[ií]|no|ok|vale|claro|dale|venga|bien|bueno|exacto|perfecto|'
    r'genial|brutal|guay|hola|ola|hey|ey|buenas?|gracias?|'
    r'ja(?:ja)+j*|je(?:je)+|ji(?:ji)+|lol|xd|uff+|mm+m|ahhh*|ohhh*|woww*|wow|ohh*|aha+)'
    r')$',
    re.IGNORECASE | re.UNICODE,
)


def _is_trivial_message(text: str) -> bool:
    """Return True for very short acks that need no LLM (saves cost)."""
    text = text.strip()
    if len(text) > 20:
        return False
    return bool(_TRIVIAL_RE.match(text))


def _calc_max_tokens(user_message: str, context_type: str) -> int:
    if context_type == 'media_reaction':
        return 80
    if context_type == 'winding_down':
        return 120
    length = len(user_message)
    if length < 15:
        return 80
    if length < 80:
        return 130
    return 200


class TriggerEngine:
    """Orchestrates the decision flow for automatic responses with debounce."""

    def __init__(
        self,
        chat_registry: ChatRegistry,
        context_manager: ContextManager,
        generator: ResponseGenerator,
        sender: TelegramSender,
        settings: Settings,
        photo_registry: Optional[PhotoRegistry] = None,
    ):
        self.chat_registry = chat_registry
        self.context_manager = context_manager
        self.generator = generator
        self.sender = sender
        self.settings = settings
        self.photo_registry = photo_registry
        self.rules = TriggerRules()
        
        # Debounce state per chat
        self._pending_tasks: Dict[int, asyncio.Task] = {}
        self._pending_messages: Dict[int, List[str]] = {}
        self._pending_media_type: Dict[int, str] = {}  # tracks media type through debounce
        self._pending_farewell: set = set()  # chats where user said goodbye
        self._grace_remaining: Dict[int, int] = {}  # grace turns left when hitting turn-limit mid-hot-sexting
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
        media_type: str = "",
    ) -> TriggerResult:
        """
        Process an incoming message with debounce and session lifecycle.
        media_type: 'audio', 'image', 'video', or '' for plain text.
        """
        # 1. Register the chat
        chat = await self.chat_registry.register_or_update(
            chat_id=chat_id,
            name=name,
            full_name=full_name,
            username=username,
            last_message=text,
            last_date=date or datetime.now(timezone.utc),
        )

        # 2. Ignore our own outbound messages
        if self.rules.is_message_from_me(sender_id, my_id):
            logger.debug(f"Ignoring outbound message from chat {chat_id}")
            return TriggerResult(should_respond=False, reason="outbound_message")

        # 3. Handle audio immediately — fixed reply, no AI, no debounce
        if media_type == "audio":
            reply = random.choice(_AUDIO_REPLIES)
            try:
                await self.sender.send_message(chat_id, reply)
                self.context_manager.add_to_history(chat_id, "user", "[audio]")
                self.context_manager.add_to_history(chat_id, "assistant", reply)
                logger.info(f"🎧 Audio message from chat {chat_id} — sent fixed reply")
            except Exception as exc:
                logger.error(f"Failed to send audio reply to chat {chat_id}: {exc}")
            return TriggerResult(should_respond=True, reason="audio_fixed_reply")

        # 4. Detect farewell → mark for farewell response (don't close yet — AI must say goodbye first)
        if is_farewell(text):
            logger.info(f"Farewell detected in chat {chat_id}. Will generate goodbye before closing.")
            async with self._lock:
                self._pending_farewell.add(chat_id)

        # 4. Session lifecycle: closed or new session
        status = await self.chat_registry.get_conversation_status(chat_id)

        if status == ConversationStatus.CLOSED:
            # Session closed after farewell — ignore all further messages until restart
            logger.debug(f"Chat {chat_id} session is closed. Ignoring message.")
            return TriggerResult(should_respond=False, reason="session_closed")
        elif not chat.session_started_at:
            # First ever session — assign random turn limit
            max_turns = random.randint(
                self.settings.conversation_max_turns_min,
                self.settings.conversation_max_turns_max,
            )
            logger.info(f"Starting first conversation session for chat {chat_id} (max {max_turns} turns)")
            await self.chat_registry.start_conversation(chat_id, max_turns=max_turns)

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

            # Track media type (latest media wins; plain text clears it)
            if media_type in ("image", "video"):
                self._pending_media_type[chat_id] = media_type
            elif not media_type:
                self._pending_media_type.pop(chat_id, None)

            # Add message to pending buffer
            if chat_id not in self._pending_messages:
                self._pending_messages[chat_id] = []
            display_text = text if text else f"[{media_type}]"
            self._pending_messages[chat_id].append(display_text)

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

    def _check_photo(
        self, turn_count: int, photos_sent: int, last_photo_turn: int,
        sent_filenames: list, assigned_filenames: list,
        force_explicit: bool = False, heat_hot: bool = False
    ) -> Tuple[bool, Optional[Path], bool, Optional[str]]:
        """
        Decide whether to send a photo this turn.
        Returns (will_send, photo_path, limit_reached, caption).
        force_explicit: user explicitly requested a photo → skip gap + probability.
        heat_hot: sexting heat is high → skip probability but KEEP gap (prevents back-to-back).
        """
        if self.photo_registry is None:
            return False, None, False, None

        if photos_sent >= self.settings.photo_max_per_session:
            return False, None, True, None

        gap = getattr(self.settings, 'photo_min_turns_gap', 8)

        if force_explicit:
            # Explicit request: bypass gap and probability
            pass
        else:
            if turn_count < 3:
                return False, None, False, None
            if last_photo_turn > 0:
                # Enforce the gap only BETWEEN actual photo sends.
                if turn_count - last_photo_turn < gap:
                    return False, None, False, None
            elif not heat_hot:
                # No photo sent yet: warm chats wait out the gap, but when the
                # sexting is hot Rosa takes the initiative and can send earlier.
                if turn_count < gap:
                    return False, None, False, None
            if not heat_hot and random.random() >= self.settings.photo_send_probability:
                return False, None, False, None

        photo_path = self.photo_registry.get_random_enabled_photo(
            exclude=sent_filenames, allowed=assigned_filenames or None
        )
        if photo_path is None:
            return False, None, False, None

        caption = self.photo_registry.get_caption(photo_path.name)
        return True, photo_path, False, caption

    async def _process_after_delay(self, chat_id: int, delay: float):
        """Process accumulated messages after the debounce delay expires."""
        try:
            await asyncio.sleep(delay)

            async with self._lock:
                messages = self._pending_messages.get(chat_id, [])
                if not messages:
                    return
                self._pending_messages.pop(chat_id, None)
                self._pending_tasks.pop(chat_id, None)
                pending_media = self._pending_media_type.pop(chat_id, None)
                is_farewell_pending = chat_id in self._pending_farewell
                if is_farewell_pending:
                    self._pending_farewell.discard(chat_id)

            logger.info(
                f"⏰ Debounce expired for chat {chat_id}. "
                f"Processing {len(messages)} accumulated message(s)."
                + (f" [media={pending_media}]" if pending_media else "")
            )

            for msg in messages:
                self.context_manager.add_to_history(chat_id, "user", msg)

            last_message = messages[-1]

            # --- Chat state ---
            chat = await self.chat_registry.get(chat_id)
            turn_count = chat.turn_count if chat else 0
            photos_sent = chat.photos_sent if chat else 0
            last_photo_turn = chat.last_photo_turn if chat else 0
            sent_filenames = list(chat.photos_sent_filenames) if chat else []
            assigned_filenames = list(chat.assigned_photo_filenames) if chat else []
            status = chat.conversation_status if chat else None
            chat_name = chat.name if chat else str(chat_id)

            # Set cost tracking context (including active conversation id for DB)
            conv_id = await self.chat_registry.get_active_conversation_id(chat_id)
            self.generator.set_chat_context(chat_id, chat_name, conversation_id=conv_id)

            # --- CLOSING state: fixed template — no AI, no history, guaranteed goodbye ---
            if status and status == ConversationStatus.CLOSING:
                _close_recent = self.context_manager.history.get_for_openai(chat_id, limit=6)
                _close_pool = (
                    _CLOSING_MESSAGES_HOT
                    if _detect_heat(_close_recent) == "hot"
                    else _CLOSING_MESSAGES
                )
                closing_text = random.choice(_close_pool)
                try:
                    await self.sender.send_message(chat_id, closing_text)
                    self.rules.record_bot_message(chat_id)
                    self.context_manager.add_to_history(chat_id, "assistant", closing_text)

                    remaining = await self.chat_registry.decrement_closing(chat_id)
                    if remaining <= 0:
                        logger.info(f"Closing sequence done for chat {chat_id}. Shutting session.")
                        self._grace_remaining.pop(chat_id, None)
                        await self.chat_registry.set_conversation_status(
                            chat_id, ConversationStatus.CLOSED
                        )
                        self.context_manager.clear_history(chat_id)
                        await self.chat_registry.reset_conversation(chat_id)
                    else:
                        logger.info(f"Closing turn sent to chat {chat_id} ({remaining} left).")
                except Exception as exc:
                    logger.error(f"Failed to send closing message: {exc}")
                return

            # --- Normal / phase-based flow ---
            # User-initiated farewell overrides phase and always fires immediately.
            # System-initiated farewell (turn limit) respects grace turns when hot.
            if is_farewell_pending:
                phase = "farewell"
            else:
                phase = await self.chat_registry.get_conversation_phase(chat_id)

            # Compute farewell heat (used for pool selection AND grace logic)
            farewell_heat = "warm"
            if phase == "farewell":
                _f_recent = self.context_manager.history.get_for_openai(chat_id, limit=6)
                farewell_heat = _detect_heat(_f_recent)
                # Grace: only for system-initiated farewells when sexting is hot
                if not is_farewell_pending and farewell_heat == "hot":
                    grace_left = self._grace_remaining.get(chat_id, _GRACE_MAX)
                    if grace_left > 0:
                        self._grace_remaining[chat_id] = grace_left - 1
                        phase = "normal"  # override: give one more turn
                        logger.info(
                            f"⏸ Grace turn for chat {chat_id}: {grace_left - 1} remaining (hot)"
                        )
                    else:
                        self._grace_remaining.pop(chat_id, None)
                        logger.info(f"Backstop hit for chat {chat_id}: no grace left, closing.")

            # --- FAREWELL: fixed template — no LLM, always fires, heat-aware pool ---
            if phase == "farewell":
                pool = _FAREWELL_MESSAGES_HOT if farewell_heat == "hot" else _FAREWELL_MESSAGES
                farewell_text = random.choice(pool)
                try:
                    await self.sender.send_message(chat_id, farewell_text)
                    self.rules.record_bot_message(chat_id)
                    self.context_manager.add_to_history(chat_id, "assistant", farewell_text)
                    await self.chat_registry.enter_closing(chat_id, turns=2)
                    logger.info(
                        f"👋 Farewell sent to chat {chat_id} (heat={farewell_heat}). "
                        f"Entering CLOSING (2 turns left)."
                    )
                except Exception as exc:
                    logger.error(f"Failed to send farewell to chat {chat_id}: {exc}")
                return

            photo_forced = is_photo_request(last_message)

            # Also trigger photo when sexting heat is very high (but gap still applies)
            heat_hot = False
            if not photo_forced:
                recent = self.context_manager.history.get_for_openai(chat_id, limit=6)
                if _detect_heat(recent) == "hot":
                    heat_hot = True

            will_send_photo, photo_path, photo_limit_reached, _photo_caption = self._check_photo(
                turn_count, photos_sent, last_photo_turn, sent_filenames, assigned_filenames,
                force_explicit=photo_forced, heat_hot=heat_hot
            )

            # Choose context type  — farewell handled above, never reaches here.
            # When Rosa sends a photo this turn, the accompanying text is a FIXED
            # teaser (no LLM). This guarantees she never contradicts herself with
            # excuses or VIP/canal mentions while actually sending a photo.
            photo_teaser_fixed = False
            context_messages = None
            if phase == "winding_down":
                context_type = "winding_down"
                _wd_recent = self.context_manager.history.get_for_openai(chat_id, limit=6)
                _wd_heat = _detect_heat(_wd_recent)
                context_messages = self.context_manager.build_context_winding_down_minimal(
                    last_message, _wd_heat
                )
            elif pending_media in ("image", "video"):
                context_type = "media_reaction"
                context_messages = self.context_manager.build_context_media_reaction(
                    chat_id, pending_media, turn_count
                )
            elif will_send_photo:
                context_type = "photo_teaser"
                photo_teaser_fixed = True
            elif photo_limit_reached:
                context_type = "normal"
                context_messages = self.context_manager.build_context_with_photo_limit_hint(
                    chat_id, last_message, turn_count
                )
            else:
                context_type = "normal"
                context_messages = self.context_manager.build_context(
                    chat_id, last_message, turn_count
                )

            if photo_teaser_fixed:
                # No LLM call — deterministic teaser, zero risk of excuse/VIP leakage.
                response_text = random.choice(_PHOTO_TEASERS)
            elif context_type == "normal" and _is_trivial_message(last_message):
                # No LLM for trivial acks — saves cost, avoids over-explaining
                response_text = random.choice(_TRIVIAL_REPLIES)
                logger.info(f"💬 Trivial reply for chat {chat_id}: {last_message!r}")
            else:
                max_tok = _calc_max_tokens(last_message, context_type)

                try:
                    response_text = await self.generator.generate(context_messages, max_tokens=max_tok)
                except Exception as exc:
                    logger.error(f"Failed to generate response: {exc}")
                    return

                # Post-processing: remove asterisks and parentheticals only
                response_text = _sanitize_response(response_text)

                if not response_text:
                    logger.error(f"Response was empty after sanitization for chat {chat_id}")
                    return

            # Send text
            try:
                await self.sender.send_message(chat_id, response_text)
                self.rules.record_bot_message(chat_id)
                self.context_manager.add_to_history(chat_id, "assistant", response_text)

                # Send photo if decided
                if will_send_photo and photo_path:
                    try:
                        await asyncio.sleep(random.uniform(1.0, 2.5))
                        await self.sender.send_photo(chat_id, photo_path)
                        await self.chat_registry.increment_photos_sent(chat_id, filename=photo_path.name)
                        await self.chat_registry.update_last_photo_turn(chat_id, turn_count)
                        logger.info(f"📸 Photo sent to chat {chat_id}: {photo_path.name}")
                    except Exception as exc:
                        logger.error(f"Failed to send photo to chat {chat_id}: {exc}")

                if phase == "farewell":
                    logger.info(f"Farewell sent to chat {chat_id}. Entering CLOSING (2 turns left).")
                    await self.chat_registry.enter_closing(chat_id, turns=2)
                else:
                    await self.chat_registry.increment_turn(chat_id)

                logger.info(
                    f"✅ Sent response to chat {chat_id} "
                    f"(phase={phase}, type={context_type}, {len(response_text)} chars)"
                )
            except Exception as exc:
                logger.error(f"Failed to send message: {exc}")

        except asyncio.CancelledError:
            logger.debug(f"Debounce timer cancelled for chat {chat_id}")
            raise

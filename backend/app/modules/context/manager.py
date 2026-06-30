from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from .loader import PromptLoader
from .validator import PromptValidator
from .history import ConversationHistory
from .models import Message

_MADRID_TZ = ZoneInfo("Europe/Madrid")

_BREVITY_HINT = (
    "LÍMITE DE RESPUESTA: responde con un máximo de 2 mensajes cortos, "
    "como en WhatsApp. Nunca más de 2 bloques separados por línea en blanco. "
    "Sé directa y concisa."
)


def _current_madrid_time_hint() -> str:
    """Return a brief time context string for the current Madrid local time."""
    now = datetime.now(_MADRID_TZ)
    days_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    months_es = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    day_name = days_es[now.weekday()]
    month_name = months_es[now.month - 1]
    return (
        f"[Hora actual en Madrid: {now.strftime('%H:%M')} del {day_name} "
        f"{now.day} de {month_name} de {now.year}. "
        f"Ajusta tu comportamiento al horario correspondiente.]"
    )


class ContextManager:
    """Manages the full conversation context for OpenAI API."""

    def __init__(
        self,
        prompt_loader: PromptLoader,
        prompt_validator: PromptValidator,
        history: ConversationHistory,
        history_window: int = 10,
    ):
        self.prompt_loader = prompt_loader
        self.prompt_validator = prompt_validator
        self.history = history
        self.history_window = history_window
        self._system_prompt: str = ""

    def initialize(self) -> None:
        """Load and validate the system prompt."""
        content = self.prompt_loader.load()
        self.prompt_validator.validate(content)
        self._system_prompt = content

    def build_context(self, chat_id: int, new_message: Optional[str] = None) -> List[dict]:
        """Build the full messages array for OpenAI API."""
        messages = [
            {"role": "system", "content": self._system_prompt},
            {"role": "system", "content": _current_madrid_time_hint()},
            {"role": "system", "content": _BREVITY_HINT},
        ]

        # Add last N messages from history (sliding window to control token cost)
        history_messages = self.history.get_for_openai(chat_id, limit=self.history_window)
        messages.extend(history_messages)

        # Add new user message if provided
        if new_message:
            messages.append({"role": "user", "content": new_message})

        return messages

    def build_farewell_context(self, chat_id: int, new_message: Optional[str] = None) -> List[dict]:
        """
        Build context with a farewell hint injected as the final system message.
        The AI will naturally steer the response toward a goodbye using its
        existing personality (excuses: gym, amigas, sesión de fotos, batería, etc.)
        without sounding like a timer ran out.
        """
        messages = self.build_context(chat_id, new_message)

        farewell_hint = (
            "INSTRUCCIÓN OBLIGATORIA: Este mensaje ES TU DESPEDIDA. "
            "DEBES despedirte en este mensaje sin falta. No puedes seguir la conversación. "
            "Usa una de tus excusas habituales (gym, amigas, sesión de fotos, batería, contenido VIP...). "
            "Dile que ha sido genial, dale un piropo final y pregúntale si habláis mañana o luego. "
            "Sé cariñosa y natural, como Rosa de verdad. "
            "PROHIBIDO continuar el tema de la conversación. SOLO despedida."
        )
        messages.append({"role": "system", "content": farewell_hint})
        return messages

    def add_to_history(self, chat_id: int, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.history.add(chat_id, role, content)

    def clear_history(self, chat_id: int) -> None:
        """Clear history for a new conversation start."""
        self.history.clear(chat_id)

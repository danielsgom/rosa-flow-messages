import re
from datetime import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from .loader import PromptLoader
from .validator import PromptValidator
from .history import ConversationHistory
from .models import Message

_MADRID_TZ = ZoneInfo("Europe/Madrid")

_HOT_KEYWORDS = {
    "tocando", "tocarte", "desnudo", "desnuda", "correrte", "corrido",
    "polla", "coño", "tetas", "culo", "mojada", "duro", "follarte",
    "masturbando", "masturbarte", "eyacular", "orgasmo", "venirme",
    "chuparte", "lamerte", "penetrar",
}
_EMOTIONAL_KEYWORDS = {
    "triste", "llorar", "llorando", "mierda", "mal día", "deprimido",
    "deprimida", "solo", "sola", "soledad", "angustia", "agobio",
    "agobiado", "agobiada", "ansiedad", "me duele", "fatal",
}

def _current_madrid_time_hint() -> str:
    now = datetime.now(_MADRID_TZ)
    days_es = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    months_es = [
        "enero", "febrero", "marzo", "abril", "mayo", "junio",
        "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    ]
    return (
        f"[Hora actual en Madrid: {now.strftime('%H:%M')} del "
        f"{days_es[now.weekday()]} {now.day} de {months_es[now.month - 1]} de {now.year}. "
        f"Ajusta tu comportamiento al horario correspondiente.]"
    )


def _is_night_madrid() -> bool:
    return datetime.now(_MADRID_TZ).hour < 6


def _brevity_hint(user_message: str) -> str:
    if len(user_message) < 20:
        return (
            "Responde con UN SOLO mensaje muy corto (1-2 frases). "
            "No añadas bloques extra. Como WhatsApp real."
        )
    return (
        "Máximo 2 mensajes cortos separados por línea en blanco. "
        "Nunca más de 2 bloques. Sé directa y concisa."
    )


def _detect_heat(recent_messages: List[dict]) -> str:
    user_texts = " ".join(
        m["content"].lower()
        for m in recent_messages[-4:]
        if m.get("role") == "user"
    )
    if any(kw in user_texts for kw in _HOT_KEYWORDS):
        return "hot"
    if any(kw in user_texts for kw in _EMOTIONAL_KEYWORDS):
        return "emotional"
    return "warm"


def _history_window(turn_count: int) -> int:
    if turn_count <= 4:
        return 4
    if turn_count <= 10:
        return 6
    return 8


class ContextManager:
    """Manages the full conversation context for OpenAI API."""

    def __init__(
        self,
        prompt_loader: PromptLoader,
        prompt_validator: PromptValidator,
        history: ConversationHistory,
        history_window: int = 10,
        examples_content: str = "",
        heat_detection: bool = True,
    ):
        self.prompt_loader = prompt_loader
        self.prompt_validator = prompt_validator
        self.history = history
        self.history_window = history_window
        self._examples_content = examples_content
        self._heat_detection = heat_detection
        self._system_prompt: str = ""

    def initialize(self) -> None:
        """Load and validate the system prompt."""
        content = self.prompt_loader.load()
        self.prompt_validator.validate(content)
        self._system_prompt = content

    def build_context(
        self,
        chat_id: int,
        new_message: Optional[str] = None,
        turn_count: int = 0,
    ) -> List[dict]:
        """Build the full messages array for OpenAI API."""
        messages: List[dict] = [
            {"role": "system", "content": self._system_prompt},
        ]

        # Examples: only for the first 3 turns
        if turn_count < 3 and self._examples_content:
            messages.append({"role": "system", "content": self._examples_content})

        # Time hint: first turn, every 5 turns, or late night
        if turn_count == 0 or turn_count % 5 == 0 or _is_night_madrid():
            messages.append({"role": "system", "content": _current_madrid_time_hint()})

        # Dynamic history window
        limit = _history_window(turn_count)
        history_messages = self.history.get_for_openai(chat_id, limit=limit)
        messages.extend(history_messages)

        # Brevity hint (adaptive)
        messages.append({
            "role": "system",
            "content": _brevity_hint(new_message or ""),
        })

        # Heat detection hint
        if self._heat_detection and history_messages:
            heat = _detect_heat(history_messages)
            if heat == "hot":
                messages.append({
                    "role": "system",
                    "content": "Estás en sexting intenso. Sé muy directa y atrevida. Sin rodeos.",
                })
            elif heat == "emotional":
                messages.append({
                    "role": "system",
                    "content": "Esta persona necesita apoyo emocional. Baja el tono sexual completamente. Escucha.",
                })

        # New user message
        if new_message:
            messages.append({"role": "user", "content": new_message})

        return messages

    def build_farewell_context(
        self, chat_id: int, new_message: Optional[str] = None, turn_count: int = 0
    ) -> List[dict]:
        messages = self.build_context(chat_id, new_message, turn_count)
        messages.append({"role": "system", "content": (
            "INSTRUCCIÓN OBLIGATORIA: Este mensaje ES TU DESPEDIDA. "
            "DEBES despedirte en este mensaje sin falta. No puedes seguir la conversación. "
            "Usa una de tus excusas habituales (gym, amigas, sesión de fotos, batería, contenido VIP...). "
            "Dile que ha sido genial, dale un piropo final y pregúntale si habláis mañana o luego. "
            "Sé cariñosa y natural, como Rosa de verdad. "
            "PROHIBIDO continuar el tema de la conversación. SOLO despedida."
        )})
        return messages

    def build_context_winding_down(
        self, chat_id: int, new_message: Optional[str] = None, turn_count: int = 0
    ) -> List[dict]:
        messages = self.build_context(chat_id, new_message, turn_count)
        messages.append({"role": "system", "content": (
            "Llevas un rato hablando. Ve bajando la intensidad sutilmente. "
            "Puedes hacer un comentario de que tienes cosas pendientes pero SIN decir adiós todavía. "
            "Un solo mensaje corto, natural."
        )})
        return messages

    def build_context_with_photo_hint(
        self, chat_id: int, new_message: Optional[str] = None, turn_count: int = 0
    ) -> List[dict]:
        messages = self.build_context(chat_id, new_message, turn_count)
        messages.append({"role": "system", "content": (
            "INSTRUCCIÓN OBLIGATORIA: Acabas de decidir mandar una foto. "
            "Escribe SOLO una frase muy corta y sugerente (máx 10 palabras). Nada más. "
            "No continúes la conversación. "
            "Ejemplo: 'mira lo que te mando 😏' o 'toma, para que no te olvides de mí 🔥'."
        )})
        return messages

    def build_context_with_photo_limit_hint(
        self, chat_id: int, new_message: Optional[str] = None, turn_count: int = 0
    ) -> List[dict]:
        messages = self.build_context(chat_id, new_message, turn_count)
        messages.append({"role": "system", "content": (
            "Ya has mandado todas las fotos que podías en esta conversación. "
            "Si te piden más fotos, diles de forma natural que ya les has mandado "
            "bastante por hoy y que si quieren más estén pendientes del canal, "
            "que les van a gustar. Sin mencionar packs ni secciones."
        )})
        return messages

    def add_to_history(self, chat_id: int, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.history.add(chat_id, role, content)

    def clear_history(self, chat_id: int) -> None:
        """Clear history for a new conversation start."""
        self.history.clear(chat_id)

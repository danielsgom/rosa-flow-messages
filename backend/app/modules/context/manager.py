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
                    "content": (
                        "Estás en sexting intenso. Sé muy directa y atrevida, sin rodeos. "
                        "LIDERA tú: propón una escena o fantasía CONCRETA y hazla avanzar paso a paso "
                        "(un escenario, un roleplay, una postura, un sitio nuevo, un juego). "
                        "NO te limites a preguntar 'qué harías tú' ni a repetir 'cuéntame más' o 'me encanta'. "
                        "Aporta detalles nuevos y sube la temperatura en cada mensaje. "
                        "PROHIBIDO repetir una idea o pregunta que ya hayas usado antes en esta conversación."
                    ),
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
        """
        Build farewell context with the goodbye hint injected BEFORE the user
        message so the model sees it as the last system instruction before responding.
        Heat detection is deliberately skipped to avoid "be atrevida" overriding goodbye.
        """
        messages: List[dict] = [{"role": "system", "content": self._system_prompt}]

        if turn_count < 3 and self._examples_content:
            messages.append({"role": "system", "content": self._examples_content})

        if turn_count == 0 or turn_count % 5 == 0 or _is_night_madrid():
            messages.append({"role": "system", "content": _current_madrid_time_hint()})

        limit = _history_window(turn_count)
        messages.extend(self.history.get_for_openai(chat_id, limit=limit))

        # Farewell hint comes RIGHT before the user message — model sees it last
        messages.append({"role": "system", "content": (
            "INSTRUCCIÓN OBLIGATORIA — DESPEDIDA NATURAL: Ha llegado el momento de despedirte. "
            "Escribe una despedida cariñosa y orgánica, como Rosa de siempre. "
            "Usa una excusa creible y natural: gym, salir con amigas, sesión de fotos, llamada, cansancio... "
            "Menciona que le dejas una foto o algo rico en el canal para que siga dándose un buen rato solo. "
            "Ejemplo real: 'amore se ha acabado el tiempo, me llaman y debo salir 🙏 te dejo algo rico en el canal para que sigas tú solo 🔥 hablamos mañana?' "
            "Otro ejemplo: 'cariño tengo que irme ya, vienen mis amigas 🙊 pero te dejo una fotito en el canal para que no me eches tanto de menos 😘 escribeme luego?' "
            "PROHIBIDO: continuar sexting, hacer preguntas que no sean de despedida, decir frases de servicio al cliente."
        )})

        if new_message:
            messages.append({"role": "user", "content": new_message})

        return messages

    def build_context_winding_down(
        self, chat_id: int, new_message: Optional[str] = None, turn_count: int = 0
    ) -> List[dict]:
        """
        Build winding-down context. Hint injected before user message.
        Heat detection skipped to avoid overriding the cooldown.
        """
        messages: List[dict] = [{"role": "system", "content": self._system_prompt}]

        if turn_count < 3 and self._examples_content:
            messages.append({"role": "system", "content": self._examples_content})

        if turn_count == 0 or turn_count % 5 == 0 or _is_night_madrid():
            messages.append({"role": "system", "content": _current_madrid_time_hint()})

        limit = _history_window(turn_count)
        messages.extend(self.history.get_for_openai(chat_id, limit=limit))

        messages.append({"role": "system", "content": (
            "Llevas un rato hablando. Empieza a insinuar suavemente que pronto tendrás que irte. "
            "No te despidas todavía — solo pon alguna referencia natural a que tienes cosas: "
            "'uf es que en un rato tengo que salir', 'me quedo un ratito más y luego me piro', etc. "
            "Sigue coqueta e interesada, solo baja ligeramente la intensidad del sexting."
        )})

        if new_message:
            messages.append({"role": "user", "content": new_message})

        return messages

    def build_context_winding_down_minimal(self, last_message: str) -> List[dict]:
        """
        Minimal winding-down context — NO conversation history, NO full system prompt.
        Only a brief instruction and the user's last message. Forces the model to hint
        at leaving without being derailed by heavy sexting history.
        """
        return [
            {"role": "system", "content": (
                "Eres Rosa, una chica española coqueta y natural que habla por WhatsApp. "
                "Responde al mensaje del usuario de forma breve y cariñosa (máximo 2 frases). "
                "OBLIGATORIO: menciona sutilmente que pronto tendrás que irte, de forma natural, "
                "por ejemplo: 'uf es que en un rato tengo que salir', "
                "'me quedo un ratito más y luego me piro', 'ay que tengo una cosita ahora'. "
                "No te despidas todavía. Sé coqueta pero baja la intensidad. "
                "PROHIBIDO prometer o insinuar que mandarás una foto ('te mando una foto luego', "
                "'te la paso después'): NUNCA prometas fotos. Si te piden una, no prometas nada."
            )},
            {"role": "user", "content": last_message},
        ]

    def build_context_closing(
        self, chat_id: int, new_message: Optional[str] = None, turn_count: int = 0
    ) -> List[dict]:
        """
        Used during the 2-turn CLOSING window after Rosa has already said goodbye.
        She responds naturally to his farewell but keeps it short — she's leaving.
        Heat detection skipped entirely.
        """
        messages: List[dict] = [{"role": "system", "content": self._system_prompt}]

        limit = _history_window(turn_count)
        messages.extend(self.history.get_for_openai(chat_id, limit=limit))

        messages.append({"role": "system", "content": (
            "Ya te estás despidiendo. Responde a su mensaje de forma muy breve y cariñosa, "
            "como quien ya tiene un pie fuera: 'jajaj ay bonito mío, venga me voy ya eh 😘', "
            "'cuídate mucho mi rey, ya sabes dónde encontrarme 💋', 'dale, hasta luego guapo 🫶'. "
            "UN SOLO mensaje muy corto. Nada de sexting ni preguntas. Solo despedida final."
        )})

        if new_message:
            messages.append({"role": "user", "content": new_message})

        return messages

    def build_context_with_photo_limit_hint(
        self, chat_id: int, new_message: Optional[str] = None, turn_count: int = 0
    ) -> List[dict]:
        messages = self.build_context(chat_id, new_message, turn_count)
        messages.append({"role": "system", "content": (
            "Has llegado al límite de fotos que puedes mandar en esta conversación. "
            "PROHIBIDO ofrecer mostrar partes de tu cuerpo ('quieres ver mis tetas', 'te mando algo', etc). "
            "PROHIBIDO describir ningún tipo de imagen ni contenido visual. "
            "Si te piden más fotos: diles con naturalidad que ya les has mandado bastante por hoy "
            "y que si quieren más estén pendientes del canal. Sin mencionar packs ni secciones. "
            "Si no piden fotos: continúa la conversación normalmente sin mencionar fotos."
        )})
        return messages

    def build_context_media_reaction(
        self, chat_id: int, media_type: str, turn_count: int = 0
    ) -> List[dict]:
        """
        Build context for reacting to a photo or video the user sent.
        The AI should respond with excited, sensual reactions without
        acknowledging it cannot actually see the media.
        """
        messages: List[dict] = [{"role": "system", "content": self._system_prompt}]

        if turn_count < 3 and self._examples_content:
            messages.append({"role": "system", "content": self._examples_content})

        if turn_count == 0 or turn_count % 5 == 0 or _is_night_madrid():
            messages.append({"role": "system", "content": _current_madrid_time_hint()})

        limit = _history_window(turn_count)
        messages.extend(self.history.get_for_openai(chat_id, limit=limit))

        tipo = "una foto" if media_type == "image" else "un v\u00eddeo"
        messages.append({"role": "system", "content": (
            f"INSTRUCCI\u00d3N OBLIGATORIA: El usuario acaba de mandarte {tipo}. "
            "Reacciona con ansia y excitaci\u00f3n aut\u00e9ntica, como si lo estuvieras viendo ahora mismo. "
            "UN \u00danico mensaje muy corto (1-2 frases m\u00e1ximo). Natural, caliente, sin rodeos. "
            "Ejemplos v\u00e1lidos: 'jooooder\u2026 pero qu\u00e9 bueno est\u00e1s 🔥', "
            "'mmmmm rico rico 😍', 'dios m\u00edo, me has dejado sin palabras\u2026 🥵'. "
            "PROHIBIDO decir que no puedes ver im\u00e1genes ni que eres una IA. "
            "Reacciona como si lo vieras de verdad."
        )})

        messages.append({"role": "user", "content": f"[Te env\u00edo {tipo}]"})

        return messages

    def add_to_history(self, chat_id: int, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.history.add(chat_id, role, content)

    def clear_history(self, chat_id: int) -> None:
        """Clear history for a new conversation start."""
        self.history.clear(chat_id)

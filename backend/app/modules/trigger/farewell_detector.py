"""
Farewell detection module for conversation lifecycle management.
Detects when a user is ending the conversation.

Design:
- Multi-word explicit farewells are matched as substrings (unambiguous phrases).
- Short standalone goodbyes (adios, bye) are matched only when the message is
  essentially just that word (prevents firing on accidental occurrences).
- "me voy a [action]" is NOT a farewell unless action is sleep-related, to avoid
  false positives like "me voy a correr" or "me voy a por agua y sigo".
- Removed: "cuídate", "later", "take care", "me voy a comer" — too ambiguous.
"""
import re

# Unambiguous multi-word farewell phrases
_FAREWELL_EXPLICIT = {
    "hasta luego", "hasta mañana", "hasta pronto", "hasta la próxima",
    "nos vemos", "buenas noches", "que descanses", "nos hablamos",
    "me voy a dormir", "me voy a la cama", "tengo que irme", "me tengo que ir",
    "tengo que salir ya", "good night", "goodbye", "bye bye",
    "see you later", "talk later", "catch you later",
}

# Short standalone goodbyes: only match when the whole message is (essentially) the word
_SHORT_FAREWELL_RE = re.compile(
    r'^\s*(?:adios|adiós|chao|chau|ciao|bye)\s*[!?.]*\s*$',
    re.IGNORECASE,
)

# "me piro" is real slang for leaving
_ME_PIRO_RE = re.compile(r'\bme piro\b', re.IGNORECASE)

# "me voy a [verb/noun]" that is NOT a farewell (continuation intent)
# Exceptions handled by _FAREWELL_EXPLICIT above ("me voy a dormir", "me voy a la cama")
_ME_VOY_CONTINUATION_RE = re.compile(
    r'\bme voy a (?!dormir|la cama)(\w)',
    re.IGNORECASE,
)


def is_farewell(text: str) -> bool:
    """
    Determine if a message contains a clear farewell intent.

    Returns True only for genuine conversation-ending signals.
    False positives ("me voy a correr", "cuídate", "take care") return False.
    """
    if not text:
        return False

    t = text.lower().strip()

    # Short standalone: "adios", "bye", etc.
    if _SHORT_FAREWELL_RE.match(t):
        return True

    # "me piro" — Spanish slang for leaving
    if _ME_PIRO_RE.search(t):
        return True

    # Cancel: "me voy a [non-sleep action]" is NOT a farewell
    if _ME_VOY_CONTINUATION_RE.search(t):
        return False

    return any(kw in t for kw in _FAREWELL_EXPLICIT)

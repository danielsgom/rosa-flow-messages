"""
Farewell detection module for conversation lifecycle management.
Detects when a user is ending the conversation.
"""

FAREWELL_KEYWORDS = {
    # Spanish
    "adios", "adiós", "hasta luego", "hasta mañana", "nos vemos",
    "chao", "chau", "me voy", "me piro", "hasta pronto",
    "buenas noches", "que descanses", "nos hablamos", "cuídate", "cuidate",
    # English
    "bye", "goodbye", "see you", "talk later", "take care",
    "later", "catch you later", "im out", "i'm out",
    # Informal
    "me voy a dormir", "me voy a comer", "tengo que irme",
}


def is_farewell(text: str) -> bool:
    """
    Determine if a message contains a farewell intent.

    Args:
        text: The message text to analyze.

    Returns:
        True if the message is a farewell, False otherwise.
    """
    if not text:
        return False

    text_lower = text.lower().strip()

    for keyword in FAREWELL_KEYWORDS:
        # Use word boundary check to avoid partial matches
        if keyword in text_lower:
            return True

    return False

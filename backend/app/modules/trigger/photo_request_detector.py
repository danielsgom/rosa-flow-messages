"""
Detector for messages where the user is explicitly requesting a photo FROM Rosa.

Design:
- Only fire when the intent is unambiguous: "foto" in any form, direct send
  commands (mándame, envíame) + open object (algo/una), or "muéstrate".
- Removed false-positive sources:
    * "quiero verte" → desire/meeting intent, not a media request
    * "quiero ver" → fires on "quiero ver cómo te corres", "quiero ver qué haces"
    * "enséñame" alone → fires on "enséñame cómo lo haces" (action, not photo)
    * "algo rico/tuyo/de ti" → vague desire, not a specific photo request
"""
import re

_PHOTO_PATTERNS = [
    # foto / fotos / fotito / fotaza / fotazo / fotaca — any word starting with "fot"
    re.compile(r'\bfot\w+\b|\bfoto\b', re.IGNORECASE),
    # Direct send command + open object ("mándame algo", "mándame una")
    re.compile(
        r'\b(?:mándame|mandame|envíame|enviame|pásame|pasame)\s+(?:algo|una|un)\b',
        re.IGNORECASE,
    ),
    # "mándame" alone (e.g. "mándame") in short messages is a send request
    re.compile(r'^\s*(?:mándame|mandame|envíame|enviame)\s*[!?.]*\s*$', re.IGNORECASE),
    # "muéstrate" / "muestrate" — unambiguous show command
    re.compile(r'\b(?:muéstrate|muestrate)\b', re.IGNORECASE),
    # "enséñame algo" (with explicit object) — distinguish from "enséñame cómo"
    re.compile(r'\b(?:enséñame|enseñame)\s+algo\b', re.IGNORECASE),
]

# Cancel patterns: direct send commands that are NOT photo requests
_NOT_PHOTO_RE = re.compile(
    r'\b(?:mándame|mandame)\s+(?:un beso|un abrazo|calor|amor|cariño|mensajes?)',
    re.IGNORECASE,
)


def is_photo_request(text: str) -> bool:
    """
    Return True only when the user is clearly asking Rosa to send a photo/visual.
    Uses pattern matching to avoid false positives from general sexual context.
    """
    if not text:
        return False
    t = text.lower().strip()
    if _NOT_PHOTO_RE.search(t):
        return False
    return any(p.search(t) for p in _PHOTO_PATTERNS)

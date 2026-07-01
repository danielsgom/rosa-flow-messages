"""
Detector for messages where the user is explicitly requesting a photo from Rosa.
"""

PHOTO_REQUEST_KEYWORDS = {
    "foto", "fotito", "fotaza", "fotazo",
    "mándame", "mandame", "manda algo", "manda una",
    "enséñame", "enseñame", "enseña", "muéstrate", "muestrate",
    "quiero verte", "quiero una foto", "quiero ver",
    "algo tuyo", "algo rico", "algo de ti",
    "una foto tuya", "una fotito",
}


def is_photo_request(text: str) -> bool:
    """
    Determine if a message is an explicit request for Rosa to send a photo.

    Args:
        text: The message text to analyze.

    Returns:
        True if the user is asking for a photo.
    """
    if not text:
        return False
    text_lower = text.lower().strip()
    return any(kw in text_lower for kw in PHOTO_REQUEST_KEYWORDS)

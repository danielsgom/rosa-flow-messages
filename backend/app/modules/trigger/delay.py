import random

from app.modules.logger import get_logger
from app.config import Settings

logger = get_logger(__name__)


def calculate_delay(min_seconds: float, max_seconds: float, enabled: bool = True) -> float:
    """
    Calculate a random delay before sending a response.

    Args:
        min_seconds: Minimum delay in seconds.
        max_seconds: Maximum delay in seconds.
        enabled: Whether delay is enabled.

    Returns:
        Delay in seconds. Returns 0 if delay is disabled.
    """
    if not enabled:
        return 0.0

    if min_seconds >= max_seconds:
        return min_seconds

    delay = random.uniform(min_seconds, max_seconds)
    logger.debug(f"Calculated delay: {delay:.2f}s")
    return delay

import math
import random
from datetime import datetime
from zoneinfo import ZoneInfo

from app.modules.logger import get_logger

logger = get_logger(__name__)

_MADRID_TZ = ZoneInfo("Europe/Madrid")


def _quiet_multiplier() -> float:
    """
    Return a delay multiplier based on the current time in Madrid.
    Rosa responds slower at night (asleep/slow) and slightly slower at dawn.
    """
    hour = datetime.now(_MADRID_TZ).hour
    if 2 <= hour < 7:      # deep night — Rosa is asleep
        return random.uniform(4.0, 8.0)
    if 7 <= hour < 9:      # just woke up — slow start
        return random.uniform(1.5, 2.5)
    if 22 <= hour <= 23:   # late evening — winding down
        return random.uniform(1.2, 1.8)
    return 1.0


def calculate_delay(min_seconds: float, max_seconds: float, enabled: bool = True) -> float:
    """
    Calculate a human-like random delay before sending a response.

    Uses a log-normal distribution so most delays cluster near the lower end
    with a natural long tail (occasional slower responses).
    A rare "distracted" pause (60-120 s) fires ~4% of the time.
    A night-hours multiplier makes Rosa slower to respond late at night.

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

    # Log-normal: median ≈ mid-range, sigma controls the tail
    mid = (min_seconds + max_seconds) / 2.0
    sigma = 0.45
    base = random.lognormvariate(math.log(mid), sigma)
    # Soft cap: don’t go too far above max without the distracted multiplier
    base = max(min_seconds, min(base, max_seconds * 1.5))

    # Occasional "distracted" pause — Rosa was doing something else (~4% of messages)
    if random.random() < 0.04:
        base += random.uniform(45.0, 90.0)
        base = min(base, 120.0)

    # Night/quiet-hours multiplier
    base *= _quiet_multiplier()

    delay = round(base, 1)
    logger.debug(f"Calculated delay: {delay:.1f}s")
    return delay

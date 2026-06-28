from pydantic import BaseModel
from typing import Optional


class TriggerResult(BaseModel):
    """Result of trigger decision."""
    should_respond: bool
    reason: str = ""
    delay_seconds: float = 0.0

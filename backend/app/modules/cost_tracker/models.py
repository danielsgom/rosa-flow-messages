from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field


class CostEntry(BaseModel):
    """A single LLM API call cost record."""
    chat_id: int
    chat_name: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ChatCostSummary(BaseModel):
    """Aggregated cost for a single chat."""
    chat_id: int
    chat_name: str
    calls: int
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float


class CostSummary(BaseModel):
    """Overall cost summary."""
    total_calls: int
    total_prompt_tokens: int
    total_completion_tokens: int
    total_tokens: int
    total_cost_usd: float

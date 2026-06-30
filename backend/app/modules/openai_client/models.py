from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class CompletionRequest(BaseModel):
    """Request model for OpenRouter completion."""
    model: str
    messages: List[Dict[str, str]]
    temperature: float = 0.8
    max_tokens: int = 2000
    reasoning_effort: Optional[str] = None  # "low", "medium", "high", or None


class CompletionResponse(BaseModel):
    """Response model for OpenRouter completion."""
    content: str
    model: str
    usage: Dict[str, Any] = {}

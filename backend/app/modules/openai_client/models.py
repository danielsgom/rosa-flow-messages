from pydantic import BaseModel
from typing import List, Dict, Any


class CompletionRequest(BaseModel):
    """Request model for OpenRouter completion."""
    model: str
    messages: List[Dict[str, str]]
    temperature: float = 0.8
    max_tokens: int = 2000


class CompletionResponse(BaseModel):
    """Response model for OpenRouter completion."""
    content: str
    model: str
    usage: Dict[str, Any] = {}

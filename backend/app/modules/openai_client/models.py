from pydantic import BaseModel
from typing import List, Dict, Any


class CompletionRequest(BaseModel):
    """Request model for OpenAI completion."""
    model: str
    messages: List[Dict[str, str]]
    temperature: float = 0.8
    max_completion_tokens: int = 500


class CompletionResponse(BaseModel):
    """Response model for OpenAI completion."""
    content: str
    model: str
    usage: Dict[str, Any] = {}

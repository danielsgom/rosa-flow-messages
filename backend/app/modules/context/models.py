from pydantic import BaseModel
from typing import Literal


class Message(BaseModel):
    """A single message in conversation history."""
    role: Literal["system", "user", "assistant"]
    content: str

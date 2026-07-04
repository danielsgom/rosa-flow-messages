from typing import Optional

from pydantic import BaseModel


class PhotoMeta(BaseModel):
    filename: str
    size_bytes: int
    enabled: bool
    url: str
    caption: Optional[str] = None

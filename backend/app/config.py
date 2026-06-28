from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Telegram MTProto
    telegram_api_id: int
    telegram_api_hash: str
    telegram_phone: str
    telegram_session_name: str = "rosa_session"

    # OpenRouter
    openrouter_api_key: str
    openrouter_model: str = "deepseek/deepseek-v4-pro"

    # Delay
    response_delay_seconds_min: float = 2.0
    response_delay_seconds_max: float = 12.0
    response_delay_enabled: bool = True

    # System Prompt
    system_prompt_path: str = "app/templates/system_prompt.md"
    system_prompt_max_tokens: int = 15000

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

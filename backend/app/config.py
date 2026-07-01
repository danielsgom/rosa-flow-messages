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
    openrouter_model: str = "deepseek/deepseek-chat"
    openrouter_max_tokens: int = 200

    # Delay
    response_delay_seconds_min: float = 2.0
    response_delay_seconds_max: float = 12.0
    response_delay_enabled: bool = True

    # Conversation Session Limits (cost control)
    conversation_max_turns_min: int = 15
    conversation_max_turns_max: int = 20
    context_history_window: int = 10

    # System Prompt
    system_prompt_path: str = "app/templates/system_prompt.md"
    system_prompt_examples_path: str = "app/templates/system_prompt_examples.md"
    system_prompt_max_tokens: int = 15000

    # Photos
    photos_dir: str = "photos"
    photo_send_probability: float = 0.20
    photo_max_per_session: int = 2
    photo_min_turns_gap: int = 8

    # Conversation naturalness
    conversation_heat_detection: bool = True

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

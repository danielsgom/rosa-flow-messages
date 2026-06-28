import pytest


@pytest.fixture
def sample_settings():
    """Sample settings for testing."""
    from app.config import Settings
    return Settings(
        telegram_api_id=123456,
        telegram_api_hash="test_hash",
        telegram_phone="+34600000000",
        telegram_session_name="test_session",
        openai_api_key="sk-test-key",
        openai_model="gpt-5.5",
        response_delay_seconds_min=1.0,
        response_delay_seconds_max=3.0,
        response_delay_enabled=True,
        system_prompt_path="templates/system_prompt.md",
        system_prompt_max_tokens=2000,
        log_level="DEBUG",
    )

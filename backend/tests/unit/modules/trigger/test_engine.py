import pytest
from unittest.mock import AsyncMock, MagicMock
from app.modules.trigger.engine import TriggerEngine
from app.modules.trigger.models import TriggerResult
from app.modules.chat_registry import ConversationStatus


class TestTriggerEngine:
    @pytest.fixture
    def engine(self, sample_settings):
        registry = MagicMock()
        context_manager = MagicMock()
        generator = MagicMock()
        sender = MagicMock()
        return TriggerEngine(registry, context_manager, generator, sender, sample_settings)

    @pytest.mark.asyncio
    async def test_farewell_detected(self, engine):
        engine.chat_registry.register_or_update = AsyncMock(return_value=MagicMock(auto_enabled=True))
        engine.chat_registry.set_conversation_status = AsyncMock()

        result = await engine.process_message(
            chat_id=123,
            sender_id=456,
            text="adios",
            my_id=999,
        )

        assert result.should_respond is False
        assert result.reason == "farewell_detected"
        engine.chat_registry.set_conversation_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_conversation_reactivation(self, engine):
        chat = MagicMock(auto_enabled=True)
        engine.chat_registry.register_or_update = AsyncMock(return_value=chat)
        engine.chat_registry.get_conversation_status = AsyncMock(return_value=ConversationStatus.CLOSED)
        engine.chat_registry.set_conversation_status = AsyncMock()
        engine.generator.generate = AsyncMock(return_value="Hola de nuevo!")
        engine.sender.send_message = AsyncMock()

        result = await engine.process_message(
            chat_id=123,
            sender_id=456,
            text="hola de nuevo",
            my_id=999,
        )

        # Should reactivate to ACTIVE
        assert engine.chat_registry.set_conversation_status.called

    @pytest.mark.asyncio
    async def test_auto_disabled(self, engine):
        chat = MagicMock(auto_enabled=False)
        engine.chat_registry.register_or_update = AsyncMock(return_value=chat)
        engine.chat_registry.get_conversation_status = AsyncMock(return_value=ConversationStatus.ACTIVE)

        result = await engine.process_message(
            chat_id=123,
            sender_id=456,
            text="hola",
            my_id=999,
        )

        assert result.should_respond is False
        assert result.reason == "auto_disabled"

    @pytest.mark.asyncio
    async def test_outbound_message_ignored(self, engine):
        result = await engine.process_message(
            chat_id=123,
            sender_id=999,  # Same as my_id
            text="hola",
            my_id=999,
        )

        assert result.should_respond is False
        assert result.reason == "outbound_message"

    @pytest.mark.asyncio
    async def test_successful_response(self, engine, sample_settings):
        sample_settings.response_delay_enabled = False  # Skip delay for test speed
        chat = MagicMock(auto_enabled=True)
        engine.chat_registry.register_or_update = AsyncMock(return_value=chat)
        engine.chat_registry.get_conversation_status = AsyncMock(return_value=ConversationStatus.ACTIVE)
        engine.generator.generate = AsyncMock(return_value="Que tal!")
        engine.sender.send_message = AsyncMock()
        engine.rules.is_in_cooldown = MagicMock(return_value=False)

        result = await engine.process_message(
            chat_id=123,
            sender_id=456,
            text="hola",
            my_id=999,
        )

        assert result.should_respond is True
        assert result.reason == "success"
        engine.generator.generate.assert_called_once()
        engine.sender.send_message.assert_called_once()

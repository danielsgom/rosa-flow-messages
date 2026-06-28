import pytest
import asyncio
from app.modules.chat_registry import ChatRegistry, ChatInfo, ConversationStatus


class TestChatRegistry:
    @pytest.fixture
    def registry(self):
        return ChatRegistry()

    @pytest.mark.asyncio
    async def test_register_new_chat(self, registry):
        chat = await registry.register_or_update(
            chat_id=123, name="Alice", last_message="Hola!"
        )
        assert chat.chat_id == 123
        assert chat.name == "Alice"
        assert chat.last_message_preview == "Hola!"

    @pytest.mark.asyncio
    async def test_update_existing_chat(self, registry):
        await registry.register_or_update(chat_id=123, name="Alice", last_message="Hola")
        chat = await registry.register_or_update(
            chat_id=123, last_message="Adios"
        )
        assert chat.last_message_preview == "Adios"
        assert chat.name == "Alice"  # Name preserved

    @pytest.mark.asyncio
    async def test_list_chats_sorted(self, registry):
        await registry.register_or_update(chat_id=1, name="A", last_message="msg1")
        await registry.register_or_update(chat_id=2, name="B", last_message="msg2")
        chats = await registry.list_chats()
        assert len(chats) == 2
        # Most recent first

    @pytest.mark.asyncio
    async def test_toggle_auto(self, registry):
        await registry.register_or_update(chat_id=123, name="Test")
        result = await registry.toggle_auto(123, True)
        assert result.auto_enabled is True
        assert result.chat_id == 123

    @pytest.mark.asyncio
    async def test_toggle_auto_nonexistent(self, registry):
        result = await registry.toggle_auto(999, True)
        assert result is None

    @pytest.mark.asyncio
    async def test_conversation_status(self, registry):
        await registry.register_or_update(chat_id=123, name="Test")
        await registry.set_conversation_status(123, ConversationStatus.CLOSED)
        status = await registry.get_conversation_status(123)
        assert status == ConversationStatus.CLOSED

        # Reactivate
        await registry.set_conversation_status(123, ConversationStatus.ACTIVE)
        status = await registry.get_conversation_status(123)
        assert status == ConversationStatus.ACTIVE

    @pytest.mark.asyncio
    async def test_concurrency(self, registry):
        async def add_chat(i):
            await registry.register_or_update(chat_id=i, name=f"User{i}")

        await asyncio.gather(*[add_chat(i) for i in range(100)])
        chats = await registry.list_chats()
        assert len(chats) == 100

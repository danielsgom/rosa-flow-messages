import pytest
from app.modules.chat_registry.models import ChatInfo, ConversationStatus


class TestChatInfo:
    def test_default_values(self):
        chat = ChatInfo(chat_id=123, name="Test")
        assert chat.chat_id == 123
        assert chat.name == "Test"
        assert chat.auto_enabled is False
        assert chat.conversation_status == ConversationStatus.ACTIVE
        assert chat.last_message_preview == ""

    def test_conversation_status_enum(self):
        assert ConversationStatus.ACTIVE.value == "active"
        assert ConversationStatus.CLOSED.value == "closed"

import pytest
from app.modules.context.history import ConversationHistory


class TestConversationHistory:
    @pytest.fixture
    def history(self):
        return ConversationHistory(max_messages=5)

    def test_add_message(self, history):
        history.add(123, "user", "Hola")
        messages = history.get(123)
        assert len(messages) == 1
        assert messages[0].role == "user"
        assert messages[0].content == "Hola"

    def test_add_multiple_messages(self, history):
        history.add(123, "user", "Hola")
        history.add(123, "assistant", "Hola!")
        history.add(123, "user", "Adios")

        messages = history.get(123)
        assert len(messages) == 3

    def test_fifo_limit(self, history):
        # Add more than max
        for i in range(10):
            history.add(123, "user", f"msg{i}")

        messages = history.get(123)
        assert len(messages) == 5  # max_messages
        # Oldest should be removed
        assert messages[0].content == "msg5"

    def test_isolation_between_chats(self, history):
        history.add(123, "user", "msg1")
        history.add(456, "user", "msg2")

        assert len(history.get(123)) == 1
        assert len(history.get(456)) == 1
        assert history.get(123)[0].content == "msg1"
        assert history.get(456)[0].content == "msg2"

    def test_clear_history(self, history):
        history.add(123, "user", "Hola")
        history.clear(123)
        assert len(history.get(123)) == 0

    def test_empty_chat(self, history):
        assert len(history.get(999)) == 0
        assert history.has_messages(999) is False

    def test_has_messages(self, history):
        assert history.has_messages(123) is False
        history.add(123, "user", "Hola")
        assert history.has_messages(123) is True

    def test_get_for_openai(self, history):
        history.add(123, "user", "Hola")
        history.add(123, "assistant", "Que tal!")
        openai_format = history.get_for_openai(123)
        assert openai_format == [
            {"role": "user", "content": "Hola"},
            {"role": "assistant", "content": "Que tal!"},
        ]

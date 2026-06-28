import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock


class TestRoutes:
    @pytest.fixture
    def client(self):
        from fastapi import FastAPI
        from app.api.routes import router, ChatRegistryDep
        from app.modules.chat_registry import ChatRegistry, ChatInfo

        app = FastAPI()
        app.include_router(router)

        registry = ChatRegistry()
        ChatRegistryDep.registry = registry

        return TestClient(app)

    def test_get_chats_empty(self, client):
        response = client.get("/api/chats")
        assert response.status_code == 200
        assert response.json() == []

    def test_toggle_chat_not_found(self, client):
        response = client.patch("/api/chats/999/toggle", json={"enabled": True})
        assert response.status_code == 404

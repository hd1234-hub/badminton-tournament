"""Agent 集成测试：mock Anthropic 客户端，验证完整链路"""

import json
from unittest.mock import AsyncMock, patch, MagicMock

import pytest

from app.config import settings


def _register(client):
    return client.post("/api/v1/auth/register", json={
        "username": "agenttest", "password": "test123456", "name": "测试用户",
    }).json()["token"]


class TestAgentNoAPIKey:
    def test_chat_without_api_key_returns_error(self, client):
        token = _register(client)
        resp = client.post("/api/v1/agent/chat",
                           json={"message": "帮我看看俱乐部"},
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        body = resp.text
        assert "未配置 API Key" in body or "ANTHROPIC_API_KEY" in body

    def test_chat_requires_auth(self, client):
        resp = client.post("/api/v1/agent/chat", json={"message": "你好"})
        assert resp.status_code in (401, 403)


class TestAgentWithMock:
    @pytest.fixture(autouse=True)
    def set_api_key(self):
        original = settings.anthropic_api_key
        settings.anthropic_api_key = "test-mock-key"
        yield
        settings.anthropic_api_key = original

    def test_chat_text_only(self, client):
        with patch("app.services.agent_service.AsyncAnthropic") as mock_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            text_block = MagicMock(type="text", text="你好！我可以帮你管理羽毛球赛事。")
            mock_response.content = [text_block]
            mock_client.messages.create.return_value = mock_response
            mock_cls.return_value = mock_client

            token = _register(client)
            resp = client.post("/api/v1/agent/chat",
                               json={"message": "你好"},
                               headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200
            body = resp.text
            # SSE 格式: "data: {...}"
            assert "data:" in body
            assert '"type":"start"' in body.replace(" ", "")
            assert '"type":"text"' in body.replace(" ", "")
            assert '"type":"done"' in body.replace(" ", "")

    def test_chat_with_tool_call(self, client):
        with patch("app.services.agent_service.AsyncAnthropic") as mock_cls:
            mock_client = AsyncMock()

            # 第一次调用返回 text + tool_use
            text_block_1 = MagicMock(type="text", text="让我帮你查询。")
            tool_block = MagicMock()
            tool_block.type = "tool_use"
            tool_block.name = "list_user_clubs"
            tool_block.id = "tool_001"
            tool_block.input = {}
            tool_block.to_dict.return_value = {
                "type": "tool_use", "name": "list_user_clubs", "id": "tool_001", "input": {},
            }
            resp1 = MagicMock()
            resp1.content = [text_block_1, tool_block]

            # 第二次调用返回纯文本
            text_block_2 = MagicMock(type="text", text="你目前有一个俱乐部。")
            resp2 = MagicMock()
            resp2.content = [text_block_2]

            mock_client.messages.create.side_effect = [resp1, resp2]
            mock_cls.return_value = mock_client

            token = _register(client)
            resp = client.post("/api/v1/agent/chat",
                               json={"message": "帮我看看俱乐部"},
                               headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200
            body = resp.text
            # 验证所有事件类型都出现了
            clean = body.replace(" ", "")
            assert '"type":"start"' in clean
            assert '"type":"text"' in clean
            assert '"type":"tool_call"' in clean
            assert '"type":"done"' in clean

    def test_chat_empty_message(self, client):
        with patch("app.services.agent_service.AsyncAnthropic") as mock_cls:
            token = _register(client)
            resp = client.post("/api/v1/agent/chat",
                               json={"message": ""},
                               headers={"Authorization": f"Bearer {token}"})
            assert resp.status_code == 200

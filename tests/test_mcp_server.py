"""Tests for wp_memlog.mcp_server"""
import json
import pytest
from unittest.mock import patch, MagicMock

# MCP is an optional dependency — skip all tests if not installed
mcp = pytest.importorskip("mcp.server")

from wp_memlog.mcp_server import (
    list_tools,
    call_tool,
    _get_meili_client,
    _get_wp_client,
)


class TestListTools:
    """Test MCP tool listing"""

    @pytest.mark.asyncio
    async def test_returns_three_tools(self):
        """Test that list_tools returns 3 tools"""
        tools = await list_tools()
        assert len(tools) == 3
        tool_names = [t.name for t in tools]
        assert "memlog_search" in tool_names
        assert "memlog_post" in tool_names
        assert "memlog_list_agents" in tool_names

    @pytest.mark.asyncio
    async def test_search_tool_schema(self):
        """Test memlog_search tool has correct schema"""
        tools = await list_tools()
        search_tool = next(t for t in tools if t.name == "memlog_search")
        assert search_tool.inputSchema["required"] == ["query"]
        assert "query" in search_tool.inputSchema["properties"]
        assert "agent" in search_tool.inputSchema["properties"]
        assert "limit" in search_tool.inputSchema["properties"]

    @pytest.mark.asyncio
    async def test_post_tool_schema(self):
        """Test memlog_post tool has correct schema"""
        tools = await list_tools()
        post_tool = next(t for t in tools if t.name == "memlog_post")
        assert set(post_tool.inputSchema["required"]) == {"agent", "content"}


class TestGetClients:
    """Test client factory functions"""

    def test_get_meili_client_defaults(self, monkeypatch):
        """Test MeiliSearchClient creation with defaults"""
        monkeypatch.setenv("WP_MEMLOG_MEILI_URL", "http://127.0.0.1:7700")
        monkeypatch.setenv("WP_MEMLOG_MEILI_KEY", "test-key")
        monkeypatch.delenv("MEILI_SEARCH_KEY", raising=False)

        client = _get_meili_client()
        assert client is not None

    def test_get_wp_client_defaults(self, monkeypatch):
        """Test WpClient creation with defaults"""
        monkeypatch.setenv("WP_MEMLOG_WP_URL", "http://127.0.0.1:8080")
        monkeypatch.setenv("WP_MEMLOG_WP_USERNAME", "test-user")
        monkeypatch.setenv("WP_MEMLOG_WP_APP_PASSWORD", "test-pw")

        client = _get_wp_client()
        assert client is not None


class TestCallTool:
    """Test MCP tool execution"""

    @pytest.mark.asyncio
    async def test_unknown_tool(self):
        """Test calling unknown tool returns error"""
        result = await call_tool("unknown_tool", {})
        assert len(result) == 1
        data = json.loads(result[0].text)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_list_agents(self, monkeypatch, tmp_path):
        """Test memlog_list_agents tool"""
        agents_yaml = tmp_path / "config" / "agents.yaml"
        agents_yaml.parent.mkdir(parents=True, exist_ok=True)
        agents_yaml.write_text(
            "agents:\n"
            "  test-agent:\n"
            "    name: Test Agent\n"
            "    category: test\n"
            "    enabled: true\n"
            "    session_dir: /tmp/sessions\n"
            "    cron: '0 0 * * *'\n"
        )

        # Patch the Path resolution in _tool_list_agents
        with patch("wp_memlog.mcp_server.load_agents_config") as mock_load:
            from wp_memlog.collect.config import AgentConfig, Config
            mock_load.return_value = Config(
                version="1.0",
                agents={
                    "test-agent": AgentConfig(
                        name="Test Agent",
                        category="test",
                        enabled=True,
                        session_dir="/tmp/sessions",
                        session_pattern="*.md",
                        cron="0 0 * * *",
                    )
                },
                defaults={},
            )
            result = await call_tool("memlog_list_agents", {})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert len(data) == 1
        assert data[0]["name"] == "Test Agent"
        assert data[0]["category"] == "test"

    @pytest.mark.asyncio
    async def test_search_tool(self, monkeypatch):
        """Test memlog_search tool"""
        monkeypatch.setenv("WP_MEMLOG_MEILI_URL", "http://127.0.0.1:7700")
        monkeypatch.setenv("WP_MEMLOG_MEILI_KEY", "test-key")

        mock_result = MagicMock()
        mock_result.post_id = 1
        mock_result.title = "Test"
        mock_result.excerpt = "Excerpt"
        mock_result.date = "2026-01-01"
        mock_result.categories = ["test"]
        mock_result.tags = []
        mock_result.relevance_score = 0.9
        mock_result.url = "http://localhost/?p=1"

        with patch("wp_memlog.mcp_server._get_meili_client") as mock_client:
            mock_client.return_value.search.return_value = [mock_result]
            result = await call_tool("memlog_search", {"query": "test"})

        assert len(result) == 1
        data = json.loads(result[0].text)
        assert len(data) == 1
        assert data[0]["title"] == "Test"

"""Tests for MCP server tools (unit-level, no live services required)."""
from unittest.mock import patch

from wp_memlog.mcp_server import _get_meili_client, _get_wp_client


class TestGetMeiliClient:
    """Test MeiliSearch client creation from env vars."""

    @patch.dict("os.environ", {
        "WP_MEMLOG_MEILI_URL": "http://test:7700",
        "WP_MEMLOG_MEILI_KEY": "test-master-key",
        "MEILI_SEARCH_KEY": "test-search-key",
    })
    def test_with_search_key(self):
        client = _get_meili_client()
        assert client is not None

    @patch.dict("os.environ", {
        "WP_MEMLOG_MEILI_URL": "http://test:7700",
        "WP_MEMLOG_MEILI_KEY": "test-master-key",
    })
    def test_without_search_key(self):
        client = _get_meili_client()
        assert client is not None

    @patch.dict("os.environ", {}, clear=False)
    def test_defaults(self):
        client = _get_meili_client()
        assert client is not None


class TestGetWpClient:
    """Test WP client creation from env vars."""

    @patch.dict("os.environ", {
        "WP_MEMLOG_WP_URL": "http://test:8080",
        "WP_MEMLOG_WP_USERNAME": "testuser",
        "WP_MEMLOG_WP_APP_PASSWORD": "testpass",
    })
    def test_with_env(self):
        client = _get_wp_client()
        assert client is not None

    @patch.dict("os.environ", {}, clear=False)
    def test_defaults(self):
        client = _get_wp_client()
        assert client is not None


class TestToolListAgents:
    """Test memlog_list_agents tool logic."""

    def test_list_agents_returns_json(self):
        from wp_memlog.collect.config import load_agents_config
        cfg = load_agents_config("config/agents.yaml")
        agents = []
        for key, agent_cfg in cfg.agents.items():
            agents.append({
                "key": key,
                "name": agent_cfg.name,
                "category": agent_cfg.category if hasattr(agent_cfg, "category") else key,
                "enabled": agent_cfg.enabled,
            })
        assert len(agents) >= 4
        keys = [a["key"] for a in agents]
        assert "hermes" in keys
        assert "opencode" in keys
        assert "antigravity" in keys
        assert "claude_cli" in keys

    def test_agents_have_category(self):
        from wp_memlog.collect.config import load_agents_config
        cfg = load_agents_config("config/agents.yaml")
        for key, agent_cfg in cfg.agents.items():
            assert agent_cfg.category, f"Agent {key} missing category"


class TestAgentConfigCategory:
    """Test that agents.yaml has category field for all agents."""

    def test_all_agents_have_category(self):
        from wp_memlog.collect.config import load_agents_config
        cfg = load_agents_config("config/agents.yaml")
        for key, agent_cfg in cfg.agents.items():
            assert agent_cfg.category, f"Agent '{key}' is missing 'category' field"
            assert isinstance(agent_cfg.category, str)
            assert len(agent_cfg.category) > 0

    def test_hermes_category_is_deus(self):
        from wp_memlog.collect.config import load_agents_config
        cfg = load_agents_config("config/agents.yaml")
        assert cfg.agents["hermes"].category == "deus"

    def test_enabled_agents_loaded(self):
        from wp_memlog.collect.config import load_agents_config
        cfg = load_agents_config("config/agents.yaml")
        enabled = [k for k, a in cfg.agents.items() if a.enabled]
        assert "hermes" in enabled

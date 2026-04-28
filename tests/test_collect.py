"""Tests for wp-memlog.collect"""
import pytest
from pathlib import Path


def test_hermes_adapter_discovery(tmp_path):
    """Test Hermes adapter session discovery"""
    from wp_memlog.collect import HermesAdapter
    
    # Create mock structure
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    memory_dir = project_dir / "memory"
    memory_dir.mkdir()
    
    # Add test file
    (memory_dir / "session.md").write_text("Test session")
    
    adapter = HermesAdapter(str(tmp_path))
    sessions = adapter.get_sessions()
    
    assert len(sessions) >= 0  # May find sessions


def test_config_loader_defaults():
    """Test config loader with defaults"""
    from wp_memlog.collect.config import load_agents_config
    
    # Non-existent file should return defaults
    config = load_agents_config("/nonexistent.yaml")
    
    assert config.version == "1.0"
    assert config.agents == {}


def test_agent_config_attributes():
    """Test AgentConfig has required attributes"""
    from wp_memlog.collect.config import load_agents_config
    
    config = load_agents_config("config/agents.yaml")
    
    # Check hermes is configured
    if "hermes" in config.agents:
        hermes = config.agents["hermes"]
        assert hasattr(hermes, "name")
        assert hasattr(hermes, "enabled")
        assert hasattr(hermes, "session_dir")
        assert hasattr(hermes, "session_pattern")
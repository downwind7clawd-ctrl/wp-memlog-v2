"""Configuration loader for agents.yaml"""
import os
import yaml
from pathlib import Path
from dataclasses import dataclass

@dataclass
class AgentConfig:
    name: str
    enabled: bool
    session_dir: str
    session_pattern: str
    cron: str = "0 */6 * * *"
    category: str = ""


@dataclass
class Config:
    version: str
    agents: dict
    defaults: dict


def load_agents_config(path: str = "config/agents.yaml") -> Config:
    """Load agents.yaml with variable substitution"""
    path = Path(path)
    if not path.exists():
        return Config(version="1.0", agents={}, defaults={"cron": "0 */6 * * *"})

    with open(path) as f:
        data = yaml.safe_load(f)

    agents = {}
    for name, cfg in data.get("agents", {}).items():
        session_dir = cfg["session_dir"].replace("{{HOME}}", os.path.expanduser("~"))
        agents[name] = AgentConfig(
            name=cfg.get("name", name),
            enabled=cfg.get("enabled", False),
            session_dir=session_dir,
            session_pattern=cfg["session_pattern"],
            cron=cfg.get("cron", data.get("defaults", {}).get("cron", "0 */6 * * *")),
            category=cfg.get("category", name),
        )

    return Config(
        version=data.get("version", "1.0"),
        agents=agents,
        defaults=data.get("defaults", {})
    )
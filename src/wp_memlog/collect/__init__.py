"""wp_memlog.collect - Multi-agent session collector"""
from .adapters import (
    HermesAdapter,
    OpenCodeAdapter,
    AntiGravityAdapter,
    ClaudeCLIAdapter,
    SessionFile,
    AgentAdapter,
)

__all__ = [
    "HermesAdapter",
    "OpenCodeAdapter",
    "AntiGravityAdapter", 
    "ClaudeCLIAdapter",
    "SessionFile",
    "AgentAdapter",
]
"""Agent adapters for session collection"""
from __future__ import annotations
import json
import os
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, Optional

@dataclass
class SessionFile:
    path: str
    id: str
    modified: datetime


class AgentAdapter(Protocol):
    """Protocol for agent session adapters"""
    def get_sessions(self) -> list[SessionFile]:
        ...


class BaseAdapter:
    """Base adapter with common functionality"""
    def __init__(self, session_dir: str):
        self.session_dir = Path(os.path.expanduser(session_dir))

    def _scan_files(self, pattern: str) -> list[Path]:
        if not self.session_dir.exists():
            return []
        return list(self.session_dir.glob(pattern))


class HermesAdapter(BaseAdapter):
    """Hermes (Claude Code) session adapter - reads memory/*.md"""
    def get_sessions(self) -> list[SessionFile]:
        sessions = []
        # memory/*.md (new structure)
        for project_dir in self._scan_files("*"):
            if not project_dir.is_dir():
                continue
            memory_dir = project_dir / "memory"
            if not memory_dir.exists():
                continue
            for fp in memory_dir.glob("*.md"):
                sessions.append(SessionFile(
                    path=str(fp),
                    id=fp.stem,
                    modified=datetime.fromtimestamp(fp.stat().st_mtime)
                ))
        return sessions


class OpenCodeAdapter(BaseAdapter):
    """OpenCode session adapter"""
    def get_sessions(self) -> list[SessionFile]:
        sessions = []
        for fp in self._scan_files("*.json"):
            sessions.append(SessionFile(
                path=str(fp),
                id=fp.stem,
                modified=datetime.fromtimestamp(fp.stat().st_mtime)
            ))
        return sessions


class AntiGravityAdapter(BaseAdapter):
    """AntiGravity session adapter"""
    def get_sessions(self) -> list[SessionFile]:
        return self._get_generic_sessions("*.json")

    def _get_generic_sessions(self, pattern: str) -> list[SessionFile]:
        sessions = []
        for fp in self._scan_files(pattern):
            sessions.append(SessionFile(
                path=str(fp),
                id=fp.stem,
                modified=datetime.fromtimestamp(fp.stat().st_mtime)
            ))
        return sessions


class ClaudeCLIAdapter(AntiGravityAdapter):
    """Claude CLI session adapter"""
    def __init__(self, session_dir: str = "~/.config/Claude/sessions"):
        super().__init__(session_dir)
"""Session payload with idempotency + chunking"""

import uuid
import re
from dataclasses import dataclass, field
from typing import Optional

try:
    import tiktoken
except ImportError:
    tiktoken = None


@dataclass
class SessionPayload:
    """에이전트가 세션 시작 시 생성하고 종료까지 유지하는 페이로드."""
    agent: str
    date: str
    content: str
    title: str = ""
    idem_key: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: str = ""

    def __post_init__(self):
        if not self.title:
            self.title = f"[{self.agent}] {self.date} 세션"
        if not self.category:
            self.category = self.agent.lower()


def count_tokens(text: str) -> int:
    """정확한 토큰 카운트 (tiktoken)."""
    if tiktoken is None:
        return len(text) // 4
    try:
        enc = tiktoken.encoding_for_model("gpt-4")
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def chunk_session(transcript: str, max_tokens: int = 6000) -> list[str]:
    """문장 단위 + 줄바꿈 기준 청킹. 한국어 대화 전문 대응."""
    if count_tokens(transcript) <= max_tokens:
        return [transcript]

    code_blocks = []
    def _protect(m):
        code_blocks.append(m.group(0))
        return f"\x00CODEBLOCK_{len(code_blocks) - 1}\x00"

    transcript = re.sub(r"```[\s\S]*?```", _protect, transcript)
    transcript = transcript.replace("```", "\x00TRIPLE_BACKTICK\x00")

    parts = re.split(r"(?<=[.!?。])\s*|\n{2,}", transcript)

    chunks, current = [], ""
    for p in parts:
        if count_tokens(current + p) > max_tokens:
            if current.strip():
                chunks.append(current.strip())
            current = p
        else:
            current += (" " if current and not current.endswith("\n") else "") + p
    if current.strip():
        chunks.append(current.strip())

    result = []
    for chunk in chunks:
        restored = chunk
        for i, block in enumerate(code_blocks):
            restored = restored.replace(f"\x00CODEBLOCK_{i}\x00", block)
        restored = restored.replace("\x00TRIPLE_BACKTICK\x00", "```")
        result.append(restored)
    return result
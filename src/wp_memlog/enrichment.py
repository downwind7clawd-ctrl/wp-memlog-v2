"""OpenRouter-based enrichment for wp-memlog"""

import os
import httpx
from dataclasses import dataclass
from typing import Optional


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-oss-120b:free"


@dataclass
class EnrichmentResult:
    """Result from OpenRouter enrichment."""
    excerpt: str
    tags: list[str]
    title: Optional[str] = None


async def generate_excerpt(content: str, model: str = DEFAULT_MODEL) -> str:
    """Generate excerpt/summary using OpenRouter."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set")

    prompt = f"""Summarize the following message in 2-3 sentences (max 100 words).
Focus on key decisions, outcomes, and any outstanding tasks.

Message:
{content[:3000]}
"""

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://127.0.0.1:8080",
                "X-Title": "wp-memlog"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def extract_tags(content: str, model: str = DEFAULT_MODEL) -> list[str]:
    """Extract relevant tags from content using OpenRouter."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set")

    prompt = f"""Extract 3-5 relevant keywords/tags from the following content.
Return them as a comma-separated list, no explanation.

Content:
{content[:2000]}
"""

    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://127.0.0.1:8080",
                "X-Title": "wp-memlog"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 50
            }
        )
        response.raise_for_status()
        data = response.json()
        tags_text = data["choices"][0]["message"]["content"]
        return [t.strip() for t in tags_text.split(",")]


async def enrich_session(content: str, title: str = "", model: str = DEFAULT_MODEL) -> EnrichmentResult:
    """Generate both excerpt and tags from content."""
    excerpt = await generate_excerpt(content, model)
    tags = await extract_tags(content, model)
    return EnrichmentResult(
        excerpt=excerpt,
        tags=tags,
        title=title
    )


def generate_excerpt_sync(content: str, model: str = DEFAULT_MODEL) -> str:
    """Synchronous version of generate_excerpt."""
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not set")

    prompt = f"""Summarize the following message in 2-3 sentences (max 100 words).
Focus on key decisions, outcomes, and any outstanding tasks.

Message:
{content[:3000]}
"""

    with httpx.Client(timeout=60) as client:
        response = client.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://127.0.0.1:8080",
                "X-Title": "wp-memlog"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 200
            }
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
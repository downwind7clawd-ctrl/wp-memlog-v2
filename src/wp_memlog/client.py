"""WordPress REST API client + Meilisearch search"""

import os
import json
from dataclasses import dataclass
from typing import Optional

import httpx
from meilisearch import Client as MeiliClient

from .session import SessionPayload


@dataclass
class PostResult:
    post_id: int
    indexed: bool
    enriched: bool


@dataclass
class SearchResult:
    post_id: int
    title: str
    excerpt: Optional[str]
    content_preview: str
    date: str
    categories: list[str]
    tags: list[str]
    relevance_score: float
    enriched: bool
    url: str


class WpClient:
    def __init__(self, wp_url: str, username: str, app_password: str):
        self.wp_url = wp_url.rstrip("/")
        self.auth = (username, app_password)

    def create_post(
        self,
        title: str,
        content: str,
        status: str = "private",
        category: Optional[int] = None,
        meta: Optional[dict] = None,
    ) -> int:
        """Create a new post."""
        data = {
            "title": title,
            "content": content,
            "status": status,
        }
        if category:
            data["categories"] = [category]
        if meta:
            data["meta"] = meta

        with httpx.Client() as client:
            resp = client.post(
                f"{self.wp_url}/wp-json/wp/v2/posts",
                auth=self.auth,
                json=data,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()["id"]

    def update_post(self, post_id: int, **kwargs) -> dict:
        """Update a post."""
        with httpx.Client() as client:
            resp = client.post(
                f"{self.wp_url}/wp-json/wp/v2/posts/{post_id}",
                auth=self.auth,
                json=kwargs,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    def get_post(self, post_id: int) -> dict:
        """Get a post."""
        with httpx.Client() as client:
            resp = client.get(
                f"{self.wp_url}/wp-json/wp/v2/posts/{post_id}",
                auth=self.auth,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    def list_posts(
        self,
        status: Optional[str] = None,
        per_page: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        """List posts."""
        params = {"per_page": per_page, "offset": offset}
        if status:
            params["status"] = status

        with httpx.Client() as client:
            resp = client.get(
                f"{self.wp_url}/wp-json/wp/v2/posts",
                auth=self.auth,
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()


class MeiliSearchClient:
    def __init__(self, url: str, api_key: str, index_name: str = "wp_posts"):
        self.client = MeiliClient(url, api_key)
        self.index = self.client.index(index_name)

    def index_document(
        self,
        post_id: int,
        title: str,
        content: str,
        excerpt: Optional[str] = None,
        categories: Optional[list] = None,
        date: Optional[str] = None,
        status: str = "private",
        enriched: bool = False,
    ):
        """Index a document."""
        doc = {
            "id": str(post_id),
            "title": title,
            "content": content,
            "excerpt": excerpt or "",
            "categories": categories or [],
            "date": date or "",
            "status": status,
            "_enriched": enriched,
        }
        self.index.add_documents([doc])

    def update_excerpt(self, post_id: int, excerpt: str):
        """Update excerpt after ClassifAI enrichment."""
        self.index.update_documents([{"id": str(post_id), "excerpt": excerpt, "_enriched": True}])

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        limit: int = 5,
    ) -> list[SearchResult]:
        """Search sessions."""
        filters = []
        if category:
            filters.append(f"categories = {category}")
        # TODO: Meilisearch v1.38+ upgrade 후 date 필터 활성화
        # if date_from:
        #     filters.append(f"date >= {date_from}")
        # if date_to:
        #     filters.append(f"date <= {date_to}")

        params = {
            "limit": limit,
            "filter": filters if filters else None,
        }

        results = self.index.search(query, params)
        out = []
        for hit in results["hits"]:
            excerpt = hit.get("excerpt") or hit.get("content", "")[:500]
            out.append(SearchResult(
                post_id=int(hit.get("id", hit.get("_id", 0))),
                title=hit.get("title", ""),
                excerpt=excerpt,
                content_preview=hit.get("content", "")[:500],
                date=hit.get("date", ""),
                categories=hit.get("categories", []),
                tags=hit.get("tags", []),
                relevance_score=hit.get("_rankingScore", 0.0),
                enriched=hit.get("_enriched", False),
                url=hit.get("url", ""),
            ))
        return out


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable."""
    return os.getenv(key, default)
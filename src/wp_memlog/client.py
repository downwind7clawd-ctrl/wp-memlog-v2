"""WordPress REST API client + Meilisearch search"""

import json
import logging
import os
import shlex
import subprocess
from dataclasses import dataclass
from typing import Optional

import httpx
from meilisearch import Client as MeiliClient
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)



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
    def __init__(self, wp_url: str, username: str, app_password: str, wp_cli: str = "wp"):
        self.wp_url = wp_url.rstrip("/")
        self.auth = (username, app_password)
        self._wp_cli = wp_cli

    def _wp_cli_run(self, *args) -> str:
        """Run a WP-CLI command and return stdout. Raises on failure."""
        cmd = [self._wp_cli, "--allow-root", "--path=/var/www/html", *args]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"WP-CLI failed: {result.stderr.strip()}")
        return result.stdout.strip()

    def create_post(
        self,
        title: str,
        content: str,
        status: str = "private",
        category: Optional[int] = None,
        meta: Optional[dict] = None,
    ) -> int:
        """Create a new post via WP-CLI (avoids REST API auth issues)."""
        args = [
            "post", "create",
            f"--post_title={shlex.quote(title)}",
            f"--post_content={shlex.quote(content)}",
            f"--post_status={shlex.quote(status)}",
        ]
        if category:
            args.append(f"--post_category={category}")
        if meta:
            for k, v in meta.items():
                args.append(f"--meta_input={shlex.quote(json.dumps({k: v}))}")
        args.append("--porcelain")

        output = self._wp_cli_run(*args)
        return int(output)

    def update_post(self, post_id: int, **kwargs) -> dict:
        """Update a post via WP-CLI."""
        args = ["post", "update", str(post_id)]
        for k, v in kwargs.items():
            if k == "meta":
                args.append(f"--meta_input={shlex.quote(json.dumps(v))}")
            else:
                args.append(f"--{k}={shlex.quote(str(v))}")
        self._wp_cli_run(*args)
        return {"id": post_id, "updated": True}

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def get_post(self, post_id: int) -> dict:
        """Get a post."""
        with httpx.Client(follow_redirects=True) as http:
            resp = http.get(
                f"{self.wp_url}/wp-json/wp/v2/posts/{post_id}",
                auth=self.auth,
                timeout=30,
            )
            if resp.status_code >= 400:
                logger.error("WP REST error %d for get_post(%d): %s", resp.status_code, post_id, resp.text)
                resp.raise_for_status()
            return resp.json()

    def resolve_category(self, slug: str) -> int | None:
        """Resolve a category slug to its WP category ID. Returns None if not found."""
        with httpx.Client(follow_redirects=True) as http:
            resp = http.get(
                f"{self.wp_url}/wp-json/wp/v2/categories",
                auth=self.auth,
                params={"slug": slug, "per_page": 1},
                timeout=30,
            )
            if resp.status_code >= 400:
                logger.error("WP REST error %d for resolve_category(%s): %s", resp.status_code, slug, resp.text)
                resp.raise_for_status()
            cats = resp.json()
            if cats:
                return cats[0]["id"]
            return None

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

        with httpx.Client(follow_redirects=True) as http:
            resp = http.get(
                f"{self.wp_url}/wp-json/wp/v2/posts",
                auth=self.auth,
                params=params,
                timeout=30,
            )
            if resp.status_code >= 400:
                logger.error("WP REST error %d for list_posts: %s", resp.status_code, resp.text)
                resp.raise_for_status()
            return resp.json()


class MeiliSearchClient:
    def __init__(self, url: str, api_key: str, index_name: str = "wp_posts", search_key: str | None = None):
        self.client = MeiliClient(url, api_key)
        self.index = self.client.index(index_name)
        self._search_key = search_key

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def update_excerpt(self, post_id: int, excerpt: str):
        """Update excerpt after ClassifAI enrichment."""
        self.index.update_documents([{"id": str(post_id), "excerpt": excerpt, "_enriched": True}])

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
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
        }
        if filters:
            params["filter"] = filters

        # Use search-only key if available (principle of least privilege)
        if self._search_key:
            search_client = MeiliClient(self.client.config.url, self._search_key)
            results = search_client.index(self.index.uid).search(query, params)
        else:
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
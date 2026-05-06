#!/usr/bin/env python3
"""wp-memlog CLI - Agent session storage + search"""

import argparse
import json
import os
import subprocess
import sys

from wp_memlog import (
    SessionPayload,
    MeiliSearchClient,
    Indexer,
    BgeM3Embedder,
)


WP_CLI = os.getenv("WP_MEMLOG_WP_CLI", "wp --allow-root --path=/var/www/html")


def wp(*args):
    """Run WP-CLI command."""
    cmd = ["docker", "exec", "wp-memlog-wp", "wp", "--allow-root"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: WP-CLI error: {result.stderr}", file=sys.stderr)
        return ""
    return result.stdout.strip()


def post_session(
    meili_url: str,
    meili_key: str,
    agent: str,
    date: str,
    content: str,
    title: str = "",
    use_embedder: bool = False,
):
    """Save session to WordPress and index to Meilisearch."""
    # Create payload
    payload = SessionPayload(
        agent=agent,
        date=date,
        content=content,
        title=title or f"[{agent}] {date} Session",
    )

    # Check for existing post with same idem_key
    post_id = None
    try:
        existing = wp("post", "list", "--meta_key=_memlog_idem", f"--meta_value={payload.idem_key}", "--fields=ID", "--format=json")
        if existing:
            posts = json.loads(existing)
            if posts:
                post_id = int(posts[0]["ID"])
    except (json.JSONDecodeError, IndexError, KeyError, ValueError):
        post_id = None

    # Create new post if needed
    if not post_id:
        output = wp(
            "post", "create",
            f"--post_title={payload.title}",
            f"--post_content={payload.content}",
            "--post_status=private",
            "--post_author=admin",
            "--format=id"
        )
        # Parse output like "Success: Created post 12."
        if "Created post" in output:
            post_id = int(output.split()[-1].rstrip("."))
        else:
            print("ERROR: Failed to create post", file=sys.stderr)
            return None
        print(f"Created post {post_id}")

        # Add meta
        wp("post", "meta", "update", str(post_id), "_memlog_idem", payload.idem_key)

    if not post_id:
        print("ERROR: No post_id available", file=sys.stderr)
        return None

    # Index to Meilisearch
    embedder = None
    if use_embedder:
        print("Loading bge-m3 embedder...")
        embedder = BgeM3Embedder()

    indexer = Indexer(meili_url, meili_key, embedder=embedder)
    indexer.index_post(
        post_id=post_id,
        title=payload.title,
        content=payload.content,
        categories=[payload.category],
        enriched=False,
    )
    print("Indexed to Meilisearch")

    return post_id


def search_sessions(
    meili_url: str,
    meili_key: str,
    query: str,
    category: str = None,
    date_from: str = None,
    date_to: str = None,
    limit: int = 5,
    hybrid: float = None,
    meili_search_key: str = None,
):
    """Session search."""
    cli = MeiliSearchClient(meili_url, meili_key, search_key=meili_search_key)

    if hybrid:
        pass  # TODO: Meilisearch v1.38+ upgrade 후 구현
    else:
        results = cli.search(
            query, category=category,
            date_from=date_from, date_to=date_to,
            limit=limit
        )

    print(f"\nFound {len(results)} results for '{query}':\n")
    for r in results:
        print(f"  [{r.post_id}] {r.title}")
        print(f"      enriched: {r.enriched}, score: {r.relevance_score:.2f}")
        if r.excerpt:
            print(f"      excerpt: {r.excerpt[:200]}...")
        print()


def main():
    parser = argparse.ArgumentParser(description="wp-memlog CLI")
    subparsers = parser.add_subparsers(required=True)

    # post subcommand
    post_parser = subparsers.add_parser("post", help="Post a session")
    post_parser.add_argument("--meili-url", default=os.getenv("WP_MEMLOG_MEILI_URL", "http://127.0.0.1:7700"))
    post_parser.add_argument("--meili-key", default=os.getenv("WP_MEMLOG_MEILI_KEY"))
    post_parser.add_argument("--agent", required=True)
    post_parser.add_argument("--date", required=True)
    post_parser.add_argument("--content", required=True)
    post_parser.add_argument("--title", default="")
    post_parser.add_argument("--use-embedder", action="store_true", help="Use bge-m3 embedder")
    post_parser.set_defaults(
        func=lambda a: post_session(
            a.meili_url, a.meili_key,
            a.agent, a.date, a.content, a.title, a.use_embedder
        )
    )

    # search subcommand
    search_parser = subparsers.add_parser("search", help="Search sessions")
    search_parser.add_argument("--meili-url", default=os.getenv("WP_MEMLOG_MEILI_URL", "http://127.0.0.1:7700"))
    search_parser.add_argument("--meili-key", default=os.getenv("WP_MEMLOG_MEILI_KEY"))
    search_parser.add_argument("--meili-search-key", default=os.getenv("MEILI_SEARCH_KEY"))
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--category", default=None)
    search_parser.add_argument("--date-from", default=None, help="Filter from date (ISO)")
    search_parser.add_argument("--date-to", default=None, help="Filter to date (ISO)")
    search_parser.add_argument("--limit", type=int, default=5)
    search_parser.add_argument("--hybrid", type=float, default=None, help="Hybrid ratio (0.7 = 70% semantic)")
    search_parser.set_defaults(
        func=lambda a: search_sessions(a.meili_url, a.meili_key, a.query, a.category, a.date_from, a.date_to, a.limit, a.hybrid, a.meili_search_key)
    )

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
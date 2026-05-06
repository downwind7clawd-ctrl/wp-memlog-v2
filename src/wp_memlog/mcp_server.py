"""wp-memlog MCP server — stdio-based, exposes memlog tools to MCP clients."""

import json
import os
from datetime import date
from pathlib import Path

from mcp.server import Server
from mcp.types import Tool, TextContent

from .client import MeiliSearchClient, WpClient
from .collect.config import load_agents_config
from .session import SessionPayload

server = Server("wp-memlog")


def _get_meili_client() -> MeiliSearchClient:
    """Create MeiliSearchClient from environment variables."""
    url = os.getenv("WP_MEMLOG_MEILI_URL", "http://127.0.0.1:7700")
    api_key = os.getenv("WP_MEMLOG_MEILI_KEY", "")
    search_key = os.getenv("MEILI_SEARCH_KEY") or None
    return MeiliSearchClient(url, api_key, search_key=search_key)


def _get_wp_client() -> WpClient:
    """Create WpClient from environment variables."""
    wp_url = os.getenv("WP_MEMLOG_WP_URL", "http://127.0.0.1:8080")
    username = os.getenv("WP_MEMLOG_WP_USERNAME", "memlog-writer")
    app_password = os.getenv("WP_MEMLOG_WP_APP_PASSWORD", "")
    return WpClient(wp_url, username, app_password)


@server.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="memlog_search",
            description="Search past agent sessions by semantic/keyword query",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query string"},
                    "agent": {"type": "string", "description": "Filter by agent name (optional)"},
                    "limit": {"type": "integer", "description": "Max results (default: 5)", "default": 5},
                    "date_from": {"type": "string", "description": "Start date YYYY-MM-DD (optional)"},
                    "date_to": {"type": "string", "description": "End date YYYY-MM-DD (optional)"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="memlog_post",
            description="Save a session to WordPress and index in Meilisearch",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent": {"type": "string", "description": "Agent name (must match agents.yaml category)"},
                    "content": {"type": "string", "description": "Session content to save"},
                    "title": {"type": "string", "description": "Post title (optional, auto-generated if empty)"},
                    "date": {"type": "string", "description": "Date YYYY-MM-DD (optional, default: today)"},
                },
                "required": ["agent", "content"],
            },
        ),
        Tool(
            name="memlog_list_agents",
            description="List all configured agents from agents.yaml",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "memlog_search":
        return await _tool_search(arguments)
    elif name == "memlog_post":
        return await _tool_post(arguments)
    elif name == "memlog_list_agents":
        return await _tool_list_agents(arguments)
    else:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


async def _tool_search(args: dict) -> list[TextContent]:
    query = args["query"]
    agent = args.get("agent")
    limit = args.get("limit", 5)
    date_from = args.get("date_from")
    date_to = args.get("date_to")

    client = _get_meili_client()
    category = agent if agent else None
    results = client.search(
        query=query,
        category=category,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    output = [
        {
            "post_id": r.post_id,
            "title": r.title,
            "excerpt": r.excerpt,
            "date": r.date,
            "categories": r.categories,
            "tags": r.tags,
            "score": r.relevance_score,
            "url": r.url,
        }
        for r in results
    ]
    return [TextContent(type="text", text=json.dumps(output, ensure_ascii=False, indent=2))]


async def _tool_post(args: dict) -> list[TextContent]:
    agent = args["agent"]
    content = args["content"]
    title = args.get("title")
    date_str = args.get("date", date.today().isoformat())

    # Build payload
    payload = SessionPayload(
        agent=agent,
        date=date_str,
        content=content,
        title=title,
    )

    # Resolve category slug → WP category ID
    wp = _get_wp_client()
    category_id = wp.resolve_category(payload.category)

    # Create WordPress post
    post_id = wp.create_post(
        title=payload.title,
        content=payload.content,
        status="private",
        category=category_id,
    )

    # Index to Meilisearch
    meili = _get_meili_client()
    meili.index_document(
        post_id=post_id,
        title=payload.title,
        content=payload.content,
        categories=[payload.category],
        date=date_str,
        status="private",
    )

    output = {
        "post_id": post_id,
        "title": payload.title,
        "category": payload.category,
        "indexed": True,
        "url": f"{os.getenv('WP_MEMLOG_WP_URL', 'http://127.0.0.1:8080')}/?p={post_id}",
    }
    return [TextContent(type="text", text=json.dumps(output, ensure_ascii=False, indent=2))]


async def _tool_list_agents(args: dict) -> list[TextContent]:
    config_path = Path(__file__).parent.parent.parent / "config" / "agents.yaml"
    cfg = load_agents_config(str(config_path))
    agents = []
    for key, agent_cfg in cfg.agents.items():
        agents.append({
            "key": key,
            "name": agent_cfg.name,
            "category": agent_cfg.category if hasattr(agent_cfg, "category") else key,
            "enabled": agent_cfg.enabled,
            "session_dir": agent_cfg.session_dir,
            "cron": agent_cfg.cron,
        })
    return [TextContent(type="text", text=json.dumps(agents, ensure_ascii=False, indent=2))]


def main():
    """Entry point for stdio MCP server."""
    import asyncio
    from mcp.server.stdio import stdio_server

    async def _run():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()

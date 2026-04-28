#!/usr/bin/env python3
"""wp-memlog collector CLI - Multi-agent session collector"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from wp_memlog.collect import (
    HermesAdapter,
    OpenCodeAdapter,
    AntiGravityAdapter,
    SessionFile,
)
from wp_memlog.collect.config import load_agents_config
from wp_memlog import MeiliSearchClient, SessionPayload

WP_CLI = "docker exec wp-memlog-wp wp --allow-root"


def wp_cli(*args):
    """Run WP-CLI command."""
    cmd = WP_CLI.split() + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip(), result.stderr.strip(), result.returncode


ADAPTERS = {
    "hermes": HermesAdapter,
    "opencode": OpenCodeAdapter,
    "antigravity": AntiGravityAdapter,
    "claude_cli": AntiGravityAdapter,
}


def collect_agent(
    agent_name: str,
    config_path: str = "config/agents.yaml",
    dry_run: bool = False,
):
    """Collect sessions from a specific agent"""
    config = load_agents_config(config_path)
    agent_cfg = config.agents.get(agent_name)

    if not agent_name:
        print(f"Unknown agent: {agent_name}")
        return 1

    if not agent_cfg.enabled:
        print(f"Agent {agent_name} is disabled")
        return 0

    adapter_class = ADAPTERS.get(agent_name)
    if not adapter_class:
        print(f"No adapter for {agent_name}")
        return 1

    adapter = adapter_class(agent_cfg.session_dir)
    sessions = adapter.get_sessions()

    print(f"[{agent_name}] Found {len(sessions)} sessions in {agent_cfg.session_dir}")

    meili_client = None
    if not dry_run:
        meili_url = os.getenv("WP_MEMLOG_MEILI_URL", "http://127.0.0.1:7700")
        meili_key = os.getenv("WP_MEMLOG_MEILI_KEY")
        if not meili_key:
            print("ERROR: WP_MEMLOG_MEILI_KEY not set")
            return 1
        meili_client = MeiliSearchClient(meili_url, meili_key)

    collected = 0
    for session in sessions:
        if dry_run:
            print(f"  - {session.id}: {session.path}")
        else:
            try:
                payload = parse_session_to_payload(session, agent_name)
                if payload:
                    # Create post via WP-CLI
                    output, stderr, code = wp_cli(
                        "post", "create",
                        f"--post_title={payload.title}",
                        f"--post_content={payload.content}",
                        "--post_status=private",
                        "--post_author=admin",
                        "--format=id"
                    )
                    if "Created post" in output:
                        post_id = int(output.split()[-1].rstrip("."))
                    else:
                        print(f"  - {session.id}: ERROR - {output}")
                        continue

                    # Add meta
                    wp_cli("post", "meta", "update", str(post_id), "_memlog_idem", payload.idem_key)

                    # Index to Meilisearch
                    meili_client.index_document(
                        post_id=post_id,
                        title=payload.title,
                        content=payload.content,
                        categories=[payload.category],
                        enriched=False,
                    )
                    print(f"  - {session.id}: posted as {post_id}")
                    collected += 1
            except Exception as e:
                print(f"  - {session.id}: ERROR - {e}")

    if not dry_run:
        print(f"Collected {collected} new sessions")
    return 0

    adapter_class = ADAPTERS.get(agent_name)
    if not adapter_class:
        print(f"No adapter for {agent_name}")
        return 1

    adapter = adapter_class(agent_cfg.session_dir)
    sessions = adapter.get_sessions()

    print(f"[{agent_name}] Found {len(sessions)} sessions in {agent_cfg.session_dir}")

    # Initialize clients if not dry_run
    wp_client = None
    meili_client = None
    if not dry_run:
        wp_url = os.getenv("WP_MEMLOG_WP_URL", "http://127.0.0.1:8080")
        wp_user = os.getenv("WP_MEMLOG_WP_USER", "memlog_writer")
        wp_apppw = os.getenv("WP_MEMLOG_WP_APPPW")
        meili_url = os.getenv("WP_MEMLOG_MEILI_URL", "http://127.0.0.1:7700")
        meili_key = os.getenv("WP_MEMLOG_MEILI_KEY")

        if not wp_apppw:
            print("ERROR: WP_MEMLOG_WP_APPPW not set")
            return 1
        if not meili_key:
            print("ERROR: WP_MEMLOG_MEILI_KEY not set")
            return 1

        wp_client = WpClient(wp_url, wp_user, wp_apppw)
        meili_client = MeiliSearchClient(meili_url, meili_key)

    collected = 0
    for session in sessions:
        if dry_run:
            print(f"  - {session.id}: {session.path}")
        else:
            try:
                payload = parse_session_to_payload(session, agent_name)
                if payload:
                    post_id = wp_client.create_post(
                        title=payload.title,
                        content=payload.content,
                        status="private",
                        meta={"_memlog_idem": payload.idem_key}
                    )
                    meili_client.index_document(
                        post_id=post_id,
                        title=payload.title,
                        content=payload.content,
                        categories=[payload.category],
                        enriched=False,
                    )
                    print(f"  - {session.id}: posted as {post_id}")
                    collected += 1
            except Exception as e:
                print(f"  - {session.id}: ERROR - {e}")

    if not dry_run:
        print(f"Collected {collected} new sessions")
    return 0


def parse_session_to_payload(session: SessionFile, agent_name: str) -> SessionPayload | None:
    """Parse md session file into SessionPayload"""
    try:
        with open(session.path) as f:
            content = f.read()
    except Exception:
        return None

    if not content.strip():
        return None

    title = f"[{agent_name}] {session.id} 세션"

    return SessionPayload(
        agent=agent_name,
        date=session.id[:10] if len(session.id) >= 10 else session.id,
        content=content,
        title=title,
    )


def main():
    parser = argparse.ArgumentParser(description="wp-memlog collector")
    parser.add_argument(
        "--config",
        default="config/agents.yaml",
        help="Path to agents.yaml"
    )
    subparsers = parser.add_subparsers(required=True)

    collect_parser = subparsers.add_parser("collect", help="Collect sessions")
    collect_parser.add_argument("agent", help="Agent name (hermes, opencode, etc)")
    collect_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show sessions without collecting"
    )
    collect_parser.set_defaults(subparser="collect")

    list_parser = subparsers.add_parser("list", help="List configured agents")
    list_parser.set_defaults(subparser="list")

    args = parser.parse_args()

    if args.subparser == "collect":
        return collect_agent(args.agent, args.config, args.dry_run)
    elif args.subparser == "list":
        config = load_agents_config(args.config)
        print("Configured agents:")
        for name, cfg in config.agents.items():
            status = "✓" if cfg.enabled else "✗"
            print(f"  [{status}] {name}: {cfg.session_dir}")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
# wp-memlog — AI 에이전트를 위한 무한 기억력 시스템

> **Version: v6.0.6** | 2026-05-06
> **"세션이 끝나도, 기억은 영원히."**
> Every session. Every agent. Remembered forever.

![Version](https://img.shields.io/badge/version-6.0.6-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen)
![MCP](https://img.shields.io/badge/MCP-native-purple)

**wp-memlog** is an open-source memory system for AI agents. It automatically saves session transcripts to WordPress and makes them searchable via Meilisearch — with optional semantic search, MCP native support, and multi-agent shared memory.

---

## Why wp-memlog?

| Pain Point | Solution |
|---|---|
| AI agents forget everything between sessions | **Infinite memory** — every session saved & indexed |
| Re-explaining context every time | **Smart search** — find any past session in milliseconds |
| Cloud-locked memory services ($$$) | **100% local** — your data stays on your server |
| Single-agent silos | **Multi-agent** — all agents share one memory pool |
| Complex infrastructure | **One command** — `setup.sh` handles everything |

---

## The Problem

AI agents forget everything between sessions. You repeat context, re-explain decisions, and lose hours of work. Existing solutions are either cloud-locked ($$$), single-agent only, or require complex infrastructure.

**wp-memlog solves this:**

- **Infinite memory** — Every session is saved, indexed, and searchable
- **Multi-agent** — Hermes, OpenCode, AntiGravity, Claude CLI all share one memory
- **100% local** — No cloud dependency. Your data stays on your server
- **Zero search cost** — Local bge-m3 embeddings, no per-query fees
- **MCP native** — Any MCP-compatible client can search and save sessions
- **No vendor lock-in** — WordPress + Meilisearch, both open-source

---

## Use Cases

### 🔬 Research Agent → Knowledge Base
```
Hermes (Claude Code) analyzes code → saves findings to WP
→ Searchable by OpenCode later → No context loss across sessions
```

### 📝 Daily Memoir → KDP Publishing
```
AntiGravity writes daily logs → auto-saved to WP
→ Weekly: export all posts → generate KDP book draft
→ Monthly: publish memoir with zero manual work
```

### 🤖 Multi-Agent Collaboration
```
Hermes: "Found bug in auth module" → saved
OpenCode: searches "auth bug" → finds Hermes's finding
→ Builds on previous work without re-explaining
```

### 📊 Session Analytics
```
3 years × 20 sessions/day = ~21,900 sessions
→ All searchable by date, agent, category, content
→ Pattern recognition across years of work
```

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                      AI Agents                               │
│  Hermes (Claude Code) │ OpenCode │ AntiGravity │ Claude CLI │
└──────────┬──────────────┬──────────┬──────────────┬─────────┘
           │              │          │              │
           ▼              ▼          ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│  ① Save Session                                              │
│  wp_memlog_cli.py post --agent hermes --content "..."        │
│  OR via MCP: memlog_post(agent, content)                     │
│                                                              │
│  ┌─────────────────────┐    ┌──────────────────────────┐    │
│  │  WordPress (Docker) │    │  Meilisearch (Docker)    │    │
│  │  Private posts      │───▶│  Keyword + Semantic      │    │
│  │  mu-plugins         │    │  bge-m3 local embedder   │    │
│  │  ClassifAI summary  │    │  Hybrid search ready     │    │
│  └─────────────────────┘    └──────────────────────────┘    │
│                                                              │
│  ② Search                                                    │
│  wp_memlog_cli.py search "architecture decisions"            │
│  OR via MCP: memlog_search(query, agent?, limit?)            │
│                                                              │
│  ③ Auto-Collect (cron)                                       │
│  collector.sh scans agent session dirs every 6 hours         │
└──────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### One-Line Install

```bash
git clone https://github.com/yourname/wp-memlog.git
cd wp-memlog
./scripts/setup.sh
```

That's it. `setup.sh` handles everything:

1. ✅ Pre-flight checks (Docker, Python 3.10+, curl)
2. ✅ Auto-generates secure keys + `.env`
3. ✅ Starts Docker containers (WordPress + MariaDB + Meilisearch)
4. ✅ Installs WordPress, creates categories/roles
5. ✅ Configures Meilisearch index
6. ✅ Installs Python packages
7. ✅ Runs verification tests
8. ✅ Prints login credentials

### After Install

```bash
# Save a session
.venv/bin/python3 src/wp_memlog_cli.py post \
  --agent hermes --date 2026-01-01 \
  --content "Session content here" --title "[hermes] Planning session"

# Search past sessions
.venv/bin/python3 src/wp_memlog_cli.py search "planning" --limit 5

# Collect from agent directories
.venv/bin/python3 src/collector_cli.py --config config/agents.yaml collect hermes

# Health check
./scripts/doctor.sh

# Health check + auto-fix
./scripts/doctor.sh --fix
```

---

## Features

| Feature | Description |
|---------|-------------|
| 🔍 **Semantic Search** | bge-m3 local embeddings — search by meaning, not just keywords |
| 🤖 **Multi-Agent** | Hermes, OpenCode, AntiGravity, Claude CLI — all in one index |
| 🔌 **MCP Native** | `memlog_search`, `memlog_post`, `memlog_list_agents` tools |
| 🔒 **Private by Default** | All posts are private — only service accounts can read |
| 🧠 **AI Summarization** | Optional ClassifAI + OpenRouter auto-summary & tagging |
| 📦 **One-Command Setup** | `setup.sh` does everything — no manual config needed |
| 🔄 **Auto-Collect** | Cron-based collector scans agent session directories |
| 🛡️ **Security First** | No hardcoded secrets, least-privilege roles, path traversal protection |
| 🌐 **Multi-Language** | English, Korean, Chinese, Japanese README |

---

## Supported Agents

| Agent | Session Source | Status |
|-------|---------------|--------|
| **Hermes** (Claude Code) | `~/.claude/projects/*/memory/*.md` | ✅ Default |
| **OpenCode** | `~/.opencode/sessions/*.json` | ⚙️ Configurable |
| **AntiGravity** | `~/.antigravity/sessions/*.json` | ⚙️ Configurable |
| **Claude CLI** | `~/.config/Claude/sessions/*.json` | ⚙️ Configurable |

Add your own agent in `config/agents.yaml` — no code changes needed.

---

## MCP Server

wp-memlog includes a native MCP server for any MCP-compatible client (Claude Desktop, OpenCode, etc.).

### Setup

```bash
# Install with MCP support
pip install -e ".[mcp]"

# Run the server (stdio)
python -m wp_memlog.mcp_server
```

### MCP Client Config (Claude Desktop / OpenCode)

```json
{
  "mcpServers": {
    "wp-memlog": {
      "command": "python",
      "args": ["-m", "wp_memlog.mcp_server"],
      "cwd": "/path/to/wp-memlog",
      "env": {
        "WP_MEMLOG_MEILI_URL": "http://127.0.0.1:7700",
        "WP_MEMLOG_MEILI_KEY": "your-master-key",
        "MEILI_SEARCH_KEY": "your-search-key",
        "WP_MEMLOG_WP_URL": "http://127.0.0.1:8080",
        "WP_MEMLOG_WP_USERNAME": "memlog-writer",
        "WP_MEMLOG_WP_APP_PASSWORD": "your-app-password"
      }
    }
  }
}
```

### Available Tools

#### `memlog_search`
Search past agent sessions by semantic/keyword query.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | ✅ | Search query |
| `agent` | string | | Filter by agent name |
| `limit` | integer | | Max results (default: 5) |
| `date_from` | string | | Start date YYYY-MM-DD |
| `date_to` | string | | End date YYYY-MM-DD |

#### `memlog_post`
Save a session to WordPress and index in Meilisearch.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent` | string | ✅ | Agent name (must match agents.yaml category) |
| `content` | string | ✅ | Session content |
| `title` | string | | Auto-generated if empty |
| `date` | string | | Default: today |

#### `memlog_list_agents`
List all configured agents from agents.yaml.

No parameters required.

---

## Requirements

| Item | Minimum | Recommended |
|------|---------|-------------|
| Docker | 20.10+ | Latest |
| Docker Compose | 2.0+ | Latest |
| Python | 3.10 | 3.11+ |
| RAM | 4 GB | 8 GB |
| Disk | 5 GB | 10 GB |

## Access URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| WordPress | http://127.0.0.1:8080/wp-admin | admin / printed by setup.sh |
| Meilisearch | http://127.0.0.1:7700 | Master key in `.env` |

---

## Configuration

### Environment Variables (.env)

Auto-generated by `setup.sh`. Key variables:

```bash
# Meilisearch
MEILI_MASTER_KEY=<auto-generated>
MEILI_SEARCH_KEY=<auto-generated>
WP_MEMLOG_MEILI_URL=http://127.0.0.1:7700

# WordPress
WP_ADMIN_PASSWORD=<auto-generated>
WP_MEMLOG_WP_URL=http://127.0.0.1:8080
WP_MEMLOG_WP_USERNAME=memlog-writer
WP_MEMLOG_WP_APP_PASSWORD=<auto-generated>

# OpenRouter (optional — AI summarization)
OPENROUTER_API_KEY=sk-or-v1-...
```

### Agent Config (config/agents.yaml)

```yaml
version: "1.0"

defaults:
  cron: "0 */6 * * *"
  enabled: false

agents:
  hermes:
    name: "Hermes (Claude Code)"
    display_name: "Deus"
    category: "deus"           # WP category slug
    enabled: true
    session_dir: "{{HOME}}/.claude/projects"
    session_pattern: "*/memory/*.md"
    cron: "0 */6 * * *"
    description: "Primary agent — Claude Code sessions"
```

Add a new agent by adding a block — no code changes, no hardcoded names.

---

## CLI Reference

### Main CLI (`wp_memlog_cli.py`)

| Command | Description |
|---------|-------------|
| `post` | Save session to WordPress + Meilisearch |
| `search` | Keyword/semantic search |

```bash
# Save with embedding
.venv/bin/python3 src/wp_memlog_cli.py post \
  --agent hermes --date 2026-01-01 \
  --content "..." --title "Title" --use-embedder

# Search with category filter
.venv/bin/python3 src/wp_memlog_cli.py search "query" --category hermes
```

### Collector CLI (`collector_cli.py`)

| Command | Description |
|---------|-------------|
| `collect` | Collect sessions from agent directory |
| `list` | List configured agents |

```bash
# Dry-run collection
.venv/bin/python3 src/collector_cli.py --config config/agents.yaml collect hermes --dry-run
```

### Maintenance Scripts

| Script | Description |
|--------|-------------|
| `./scripts/setup.sh` | Full installation (first run) |
| `./scripts/setup.sh --quick` | Skip env/WordPress (containers only) |
| `./scripts/setup.sh --reset` | Full reset + restart |
| `./scripts/doctor.sh` | Health check |
| `./scripts/doctor.sh --fix` | Health check + auto-fix |
| `./scripts/backup.sh` | Meilisearch + WP + DB backup |
| `./scripts/monitor.sh` | Resource monitoring (cron) |
| `./scripts/safe-compose.sh` | Safe docker compose wrapper |

---

## Troubleshooting

### Containers won't start
```bash
docker compose logs wp-memlog-wp
docker compose logs wp-memlog-meilisearch
docker compose logs wp-memlog-db
```

### Meilisearch 403 error
```bash
./scripts/setup.sh --quick  # Regenerates search key
```

### WordPress REST API 401
WordPress 6.7 may have Application Password issues. CLI uses WP-CLI as a reliable alternative.

### Python import errors
```bash
.venv/bin/pip install -e ".[embedder]"
```

### bge-m3 model download slow
First run downloads ~2.2GB. Cached in Docker volume — no re-download on restart.

### Full reset
```bash
./scripts/setup.sh --reset
```

---

## Cost Estimate

| Item | Cost |
|------|------|
| Meilisearch search (local bge-m3) | $0 |
| ClassifAI summary (OpenRouter) | ~$0.0006/session |
| **5 sessions/day** | **~$0.10/month** |
| **30 sessions/day** | **~$0.60/month** |

---

## Comparison

| Feature | wp-memlog | Mem0 | Honcho | Claude Memory |
|---------|-----------|------|--------|---------------|
| Open source | ✅ MIT | ✅ Apache | ✅ MIT | ❌ |
| Self-hosted | ✅ | ✅ | ✅ | ❌ |
| Multi-agent | ✅ | ✅ | ✅ | ❌ |
| MCP native | ✅ | ❌ | ❌ | ❌ |
| Semantic search | ✅ bge-m3 | ✅ | ✅ | ❌ |
| Zero search cost | ✅ local | ❌ cloud | ❌ cloud | ❌ |
| WordPress backend | ✅ | ❌ | ❌ | ❌ |
| One-command setup | ✅ | ❌ | ❌ | N/A |

---

## Security

- **No hardcoded secrets** — All API keys/passwords from environment variables
- **Least privilege** — `memlog_writer` has no `edit_others_posts` or `delete_posts`
- **Command injection prevention** — `shlex.quote()` for all WP-CLI arguments
- **DB dump security** — `mysqldump --defaults-extra-file` (no process listing exposure)
- **Path traversal protection** — `os.path.realpath()` validation on session files
- **ClassifAI auth guard** — `current_user_can('edit_posts')` check
- **Git history protection** — `git filter-branch` for any accidental key commits
- **Meilisearch key separation** — Master key for indexing, search-only key for queries

---

## Code Structure

```
wp-memlog/
├── src/
│   ├── wp_memlog/              # Python package
│   │   ├── __init__.py         # Public API
│   │   ├── session.py          # SessionPayload + chunking
│   │   ├── client.py           # WP REST API + Meilisearch search
│   │   ├── embedder.py         # bge-m3 local embedder (optional)
│   │   ├── indexer.py          # Meilisearch direct indexing
│   │   ├── enrichment.py       # OpenRouter summary/tagging
│   │   ├── mcp_server.py       # MCP stdio server
│   │   └── collect/            # Multi-agent collector
│   │       ├── adapters.py     # Hermes, OpenCode, AntiGravity
│   │       └── config.py       # agents.yaml loader
│   ├── wp_memlog_cli.py        # Main CLI (post, search)
│   └── collector_cli.py        # Collector CLI (collect, list)
├── scripts/
│   ├── setup.sh                # One-command setup
│   ├── doctor.sh               # Health check + auto-fix
│   ├── backup.sh               # Backup
│   ├── monitor.sh              # Monitoring
│   ├── collector.sh            # Multi-agent collector daemon
│   ├── healthcheck.sh          # Container health
│   ├── safe-compose.sh         # Safe compose wrapper
│   └── cron.d/                 # Cron entries
├── wp-content/mu-plugins/      # WordPress must-use plugins
├── tests/                      # Test suite (26 tests)
├── docs/                       # Design docs
├── Dockerfile                  # WP + WP-CLI build
├── docker-compose.yml          # Full infrastructure
├── pyproject.toml              # Python package config
├── config/agents.yaml          # Agent configuration
└── .env                        # Environment (gitignored)
```

---

## Roadmap

- [x] Phase 1: Docker + WordPress + Meilisearch setup
- [x] Phase 2: Python package (client, indexer, embedder, session)
- [x] Phase 3: Search integration (keyword + hybrid)
- [x] Phase 4: Multi-agent collector
- [x] Phase 5: One-command setup, docs, health checks
- [x] **Phase 6: MCP server, agent de-hardcoding, i18n README**
- [ ] Phase 7: Web dashboard, Ollama integration, public release

---

## Contributing

PRs welcome! Please:

1. Fork the repo
2. Create a feature branch
3. Run tests: `source .venv/bin/activate && pytest tests/ -v`
4. Run linter: `ruff check src/ tests/`
5. Submit PR with clear description

---

## License

MIT

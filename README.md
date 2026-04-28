# wp-memlog — Agent Infinite Memory System

> Automatically store agent session conversations in WordPress and search by semantic meaning.

## Getting Started

### Requirements
- Docker + Docker Compose
- Python 3.10+
- OpenRouter API Key (optional)

### 1. Run Docker

```bash
cd /home/david/nas_1tb/dev/wp-memlog
docker compose up -d
```

### 2. Access URLs
- WordPress: http://127.0.0.1:8080
- Meilisearch: http://127.0.0.1:7700

### 3. Set Environment Variables

Create `.env` file:
```bash
cp .env.example .env
# Edit: Set OPENROUTER_API_KEY, etc.
```

### 4. Install Python Package

```bash
.venv/bin/pip install -e .
```

---

## Usage

### Post Session

```bash
# Save session to WordPress
.venv/bin/python src/wp_memlog_cli.py post \
  --agent macguffin \
  --date "2026-04-28" \
  --content "Conversation content" \
  --title "Session title"
```

### Search

```bash
# Meilisearch search
.venv/bin/python src/wp_memlog_cli.py search "search query" --limit 5
.venv/bin/python src/wp_memlog_cli.py search "search query" --category hermes
```

### Run Collector

```bash
# Manual run
.venv/bin/python src/collector_cli.py --config config/agents.yaml collect hermes

# dry-run (test)
.venv/bin/python src/collector_cli.py --config config/agents.yaml collect hermes --dry-run
```

### Cron Automation (every 6 hours)

```bash
crontab -e
# Add:
0 */6 * * * /home/david/nas_1tb/dev/wp-memlog/scripts/collector.sh --run hermes >> /var/log/wp-memlog-collector.log 2>&1
```

---

## Using OpenRouter Summarization

```python
from wp_memlog import generate_excerpt_sync

excerpt = generate_excerpt_sync("Content to summarize")
```

---

## Troubleshooting

### Application Passwords Error
Currently works with admin/password. Application Passwords setup is complex in WordPress 6.7.

### ClassifAI Not Working
Use OpenRouter directly from Python (`src/wp_memlog/enrichment.py`) instead.

---

## Architecture

```
Agent → WP REST API → WordPress (storage)
         → Meilisearch (indexing)
         → OpenRouter (summarization, direct from Python)
```

---

## Improvement Tasks

- I1: Replace ClassifAI → Python completely
- I2: WP save_post hook automatic summarization

---

## File Structure

```
wp-memlog/
├── src/
│   ├── wp_memlog/          # Python package
│   │   ├── session.py      # SessionPayload + chunk_session
│   │   ├── client.py        # WpClient + MeiliSearchClient
│   │   ├── embedder.py     # BgeM3Embedder
│   │   ├── indexer.py       # Indexer
│   │   ├── enrichment.py   # OpenRouter summarization
│   │   └── collect/        # Multi-agent collector adapters
│   │       ├── adapters.py # Hermes, OpenCode, AntiGravity adapters
│   │       └── config.py   # agents.yaml config loader
│   ├── wp_memlog_cli.py    # Main CLI (post, search)
│   └── collector_cli.py    # Collector CLI (collect, list)
├── scripts/
│   ├── collector.sh       # Collector daemon
│   ├── backup.sh          # Backup (meili + wp + db)
│   └── monitor.sh         # Monitoring
├── wp-content/mu-plugins/ # WordPress must-use plugins
│   ├── memlog-roles.php   # Custom roles (writer, reader)
│   ├── memlog-setup.php   # Auto user + app password setup
│   ├── memlog-openrouter.php # OpenRouter API routing
│   └── memlog-classifai-auto.php # ClassifAI auto meta
├── config/
│   └── agents.yaml        # Agent configuration
├── docker-compose.yml     # WP + MariaDB + Meilisearch
├── pyproject.toml         # Python package config
├── AGENTS.md              # AI agent security rules
├── PLAN.md                # Architecture & roadmap
└── .env                   # Environment variables
```
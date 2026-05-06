# wp-memlog — 赋予 AI 智能体无限记忆

> 每一次会话。每一个智能体。永远被记住。

![Version](https://img.shields.io/badge/version-6.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen)
![MCP](https://img.shields.io/badge/MCP-native-purple)

**wp-memlog** 是一个面向 AI 智能体的开源记忆系统。它自动将会话记录保存到 WordPress，并通过 Meilisearch 实现搜索功能——支持语义搜索、MCP 原生集成和多智能体共享记忆。

---

## 为什么需要？

AI 智能体在会话之间会忘记一切。你需要重复上下文，重新解释决策，浪费数小时的工作。现有方案要么依赖云端（$$$），要么只支持单一智能体，要么需要复杂的基础设施。

**wp-memlog 解决这些问题：**

- **无限记忆** — 每次会话都被保存、索引和搜索
- **多智能体** — Hermes、OpenCode、AntiGravity、Claude CLI 共享一个记忆库
- **100% 本地** — 无云端依赖。数据留在你的服务器上
- **零搜索成本** — 本地 bge-m3 嵌入，无按查询收费
- **MCP 原生** — 任何 MCP 兼容客户端都能搜索和保存会话
- **无供应商锁定** — WordPress + Meilisearch，都是开源的

---

## 工作原理

```
┌─────────────────────────────────────────────────────────────┐
│                      AI 智能体                               │
│  Hermes (Claude Code) │ OpenCode │ AntiGravity │ Claude CLI │
└──────────┬──────────────┬──────────┬──────────────┬─────────┘
           │              │          │              │
           ▼              ▼          ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│  ① 保存会话                                                   │
│  wp_memlog_cli.py post --agent hermes --content "..."        │
│  或通过 MCP: memlog_post(agent, content)                     │
│                                                              │
│  ┌─────────────────────┐    ┌──────────────────────────┐    │
│  │  WordPress (Docker) │    │  Meilisearch (Docker)    │    │
│  │  私有文章            │───▶│  关键词 + 语义搜索         │    │
│  │  mu-plugins         │    │  bge-m3 本地嵌入器        │    │
│  │  ClassifAI 摘要     │    │  混合搜索就绪             │    │
│  └─────────────────────┘    └──────────────────────────┘    │
│                                                              │
│  ② 搜索                                                      │
│  wp_memlog_cli.py search "架构决策"                           │
│  或通过 MCP: memlog_search(query, agent?, limit?)            │
│                                                              │
│  ③ 自动收集 (cron)                                            │
│  collector.sh 每 6 小时扫描智能体会话目录                       │
└──────────────────────────────────────────────────────────────┘
```

---

## 快速开始

### 一键安装

```bash
git clone https://github.com/yourname/wp-memlog.git
cd wp-memlog
./scripts/setup.sh
```

完成。`setup.sh` 自动处理一切：

1. ✅ 预检查 (Docker, Python 3.10+, curl)
2. ✅ 自动生成安全密钥 + `.env`
3. ✅ 启动 Docker 容器 (WordPress + MariaDB + Meilisearch)
4. ✅ 安装 WordPress，创建分类/角色
5. ✅ 配置 Meilisearch 索引
6. ✅ 安装 Python 包
7. ✅ 运行验证测试
8. ✅ 打印登录凭据

### 安装后

```bash
# 保存会话
.venv/bin/python3 src/wp_memlog_cli.py post \
  --agent hermes --date 2026-01-01 \
  --content "会话内容" --title "[hermes] 规划会话"

# 搜索历史会话
.venv/bin/python3 src/wp_memlog_cli.py search "规划" --limit 5

# 按智能体会话收集
.venv/bin/python3 src/collector_cli.py --config config/agents.yaml collect hermes

# 健康检查
./scripts/doctor.sh

# 健康检查 + 自动修复
./scripts/doctor.sh --fix
```

---

## 功能特性

| 功能 | 描述 |
|------|------|
| 🔍 **语义搜索** | bge-m3 本地嵌入——按含义搜索，不仅限于关键词 |
| 🤖 **多智能体** | Hermes、OpenCode、AntiGravity、Claude CLI——共享一个索引 |
| 🔌 **MCP 原生** | `memlog_search`、`memlog_post`、`memlog_list_agents` 工具 |
| 🔒 **默认私有** | 所有文章都是私有的——只有服务账户可以读取 |
| 🧠 **AI 摘要** | 可选的 ClassifAI + OpenRouter 自动摘要和标签 |
| 📦 **一键安装** | `setup.sh` 完成一切——无需手动配置 |
| 🔄 **自动收集** | 基于 cron 的收集器扫描智能体会话目录 |
| 🛡️ **安全优先** | 无硬编码密钥、最小权限原则、路径遍历保护 |
| 🌐 **多语言** | 英文、韩文、中文、日文 README |

---

## 支持的智能体

| 智能体会话源 | 状态 |
|-------------|------|
| **Hermes** (Claude Code) `~/.claude/projects/*/memory/*.md` | ✅ 默认 |
| **OpenCode** `~/.opencode/sessions/*.json` | ⚙️ 可配置 |
| **AntiGravity** `~/.antigravity/sessions/*.json` | ⚙️ 可配置 |
| **Claude CLI** `~/.config/Claude/sessions/*.json` | ⚙️ 可配置 |

在 `config/agents.yaml` 中添加新智能体——无需修改代码，无需硬编码。

---

## MCP 服务器

wp-memlog 包含一个原生 MCP 服务器，适用于任何 MCP 兼容客户端（Claude Desktop、OpenCode 等）。

### 设置

```bash
# 安装 MCP 支持
pip install -e ".[mcp]"

# 运行服务器 (stdio)
python -m wp_memlog.mcp_server
```

### MCP 客户端配置 (Claude Desktop / OpenCode)

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

### 可用工具

#### `memlog_search`
通过语义/关键词查询搜索历史智能体会话。

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `query` | string | ✅ | 搜索查询 |
| `agent` | string | | 按智能体名称过滤 |
| `limit` | integer | | 最大结果数 (默认: 5) |
| `date_from` | string | | 开始日期 YYYY-MM-DD |
| `date_to` | string | | 结束日期 YYYY-MM-DD |

#### `memlog_post`
保存会话到 WordPress 并在 Meilisearch 中建立索引。

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| `agent` | string | ✅ | 智能体名称 (必须匹配 agents.yaml 中的 category) |
| `content` | string | ✅ | 会话内容 |
| `title` | string | | 为空时自动生成 |
| `date` | string | | 默认: 今天 |

#### `memlog_list_agents`
列出 agents.yaml 中配置的所有智能体。

无需参数。

---

## 系统要求

| 项目 | 最低 | 推荐 |
|------|------|------|
| Docker | 20.10+ | 最新 |
| Docker Compose | 2.0+ | 最新 |
| Python | 3.10 | 3.11+ |
| 内存 | 4 GB | 8 GB |
| 磁盘 | 5 GB | 10 GB |

## 访问地址

| 服务 | 地址 | 凭据 |
|------|------|------|
| WordPress | http://127.0.0.1:8080/wp-admin | admin / setup.sh 输出参考 |
| Meilisearch | http://127.0.0.1:7700 | Master key in `.env` |

---

## 配置

### 环境变量 (.env)

由 `setup.sh` 自动生成。主要变量：

```bash
# Meilisearch
MEILI_MASTER_KEY=<自动生成>
MEILI_SEARCH_KEY=<自动生成>
WP_MEMLOG_MEILI_URL=http://127.0.0.1:7700

# WordPress
WP_ADMIN_PASSWORD=<自动生成>
WP_MEMLOG_WP_URL=http://127.0.0.1:8080
WP_MEMLOG_WP_USERNAME=memlog-writer
WP_MEMLOG_WP_APP_PASSWORD=<自动生成>

# OpenRouter (可选 — AI 摘要)
OPENROUTER_API_KEY=sk-or-v1-...
```

### 智能体配置 (config/agents.yaml)

```yaml
version: "1.0"

defaults:
  cron: "0 */6 * * *"
  enabled: false

agents:
  hermes:
    name: "Hermes (Claude Code)"
    display_name: "Deus"
    category: "deus"           # WP 分类 slug
    enabled: true
    session_dir: "{{HOME}}/.claude/projects"
    session_pattern: "*/memory/*.md"
    cron: "0 */6 * * *"
    description: "主智能体 — Claude Code 会话"
```

添加新智能体只需添加一个配置块——无需修改代码，无需硬编码。

---

## CLI 参考

### 主 CLI (`wp_memlog_cli.py`)

| 命令 | 描述 |
|------|------|
| `post` | 保存会话到 WordPress + Meilisearch |
| `search` | 关键词/语义搜索 |

```bash
# 带嵌入保存
.venv/bin/python3 src/wp_memlog_cli.py post \
  --agent hermes --date 2026-01-01 \
  --content "..." --title "标题" --use-embedder

# 按分类过滤搜索
.venv/bin/python3 src/wp_memlog_cli.py search "查询" --category hermes
```

### 收集 CLI (`collector_cli.py`)

| 命令 | 描述 |
|------|------|
| `collect` | 从智能体目录收集会话 |
| `list` | 列出已配置的智能体 |

```bash
# 试运行收集
.venv/bin/python3 src/collector_cli.py --config config/agents.yaml collect hermes --dry-run
```

### 维护脚本

| 脚本 | 描述 |
|------|------|
| `./scripts/setup.sh` | 完整安装 (首次运行) |
| `./scripts/setup.sh --quick` | 跳过环境/WordPress (仅容器) |
| `./scripts/setup.sh --reset` | 完全重置 + 重启 |
| `./scripts/doctor.sh` | 健康检查 |
| `./scripts/doctor.sh --fix` | 健康检查 + 自动修复 |
| `./scripts/backup.sh` | Meilisearch + WP + DB 备份 |
| `./scripts/monitor.sh` | 资源监控 (cron) |
| `./scripts/safe-compose.sh` | 安全的 docker compose 包装器 |

---

## 故障排除

### 容器无法启动
```bash
docker compose logs wp-memlog-wp
docker compose logs wp-memlog-meilisearch
docker compose logs wp-memlog-db
```

### Meilisearch 403 错误
```bash
./scripts/setup.sh --quick  # 重新生成搜索密钥
```

### WordPress REST API 401
WordPress 6.7 可能存在 Application Passwords 问题。CLI 使用 WP-CLI 作为可靠的替代方案。

### Python 导入错误
```bash
.venv/bin/pip install -e ".[embedder]"
```

### bge-m3 模型下载慢
首次运行下载约 2.2GB。缓存在 Docker 卷中——重启时不重新下载。

### 完全重置
```bash
./scripts/setup.sh --reset
```

---

## 成本估算

| 项目 | 成本 |
|------|------|
| Meilisearch 搜索 (本地 bge-m3) | $0 |
| ClassifAI 摘要 (OpenRouter) | ~$0.0006/会话 |
| **每天 5 会话** | **~$0.10/月** |
| **每天 30 会话** | **~$0.60/月** |

---

## 对比

| 功能 | wp-memlog | Mem0 | Honcho | Claude Memory |
|------|-----------|------|--------|---------------|
| 开源 | ✅ MIT | ✅ Apache | ✅ MIT | ❌ |
| 自托管 | ✅ | ✅ | ✅ | ❌ |
| 多智能体 | ✅ | ✅ | ✅ | ❌ |
| MCP 原生 | ✅ | ❌ | ❌ | ❌ |
| 语义搜索 | ✅ bge-m3 | ✅ | ✅ | ❌ |
| 零搜索成本 | ✅ 本地 | ❌ 云端 | ❌ 云端 | ❌ |
| WordPress 后端 | ✅ | ❌ | ❌ | ❌ |
| 一键安装 | ✅ | ❌ | ❌ | N/A |

---

## 安全

- **无硬编码密钥** — 所有 API 密钥/密码来自环境变量
- **最小权限** — `memlog_writer` 没有 `edit_others_posts` 或 `delete_posts`
- **命令注入防护** — WP-CLI 调用时使用 `shlex.quote()` 转义参数
- **数据库转储安全** — `mysqldump --defaults-extra-file` (无进程列表暴露)
- **路径遍历防护** — 会话文件路径 `os.path.realpath()` 验证
- **ClassifAI 认证守卫** — `current_user_can('edit_posts')` 检查
- **Git 历史保护** — 意外提交 API 密钥时使用 `git filter-branch` 立即清除
- **Meilisearch 密钥分离** — 主密钥用于索引，仅搜索密钥用于查询

---

## 代码结构

```
wp-memlog/
├── src/
│   ├── wp_memlog/              # Python 包
│   │   ├── __init__.py         # 公共 API
│   │   ├── session.py          # SessionPayload + 分块
│   │   ├── client.py           # WP REST API + Meilisearch 搜索
│   │   ├── embedder.py         # bge-m3 本地嵌入器 (可选)
│   │   ├── indexer.py          # Meilisearch 直接索引
│   │   ├── enrichment.py       # OpenRouter 摘要/标签
│   │   ├── mcp_server.py       # MCP stdio 服务器
│   │   └── collect/            # 多智能体收集器
│   │       ├── adapters.py     # Hermes, OpenCode, AntiGravity
│   │       └── config.py       # agents.yaml 加载器
│   ├── wp_memlog_cli.py        # 主 CLI (post, search)
│   └── collector_cli.py        # 收集 CLI (collect, list)
├── scripts/
│   ├── setup.sh                # 一键安装
│   ├── doctor.sh               # 健康检查 + 自动修复
│   ├── backup.sh               # 备份
│   ├── monitor.sh              # 监控
│   ├── collector.sh            # 多智能体收集器守护进程
│   ├── healthcheck.sh          # 容器健康
│   ├── safe-compose.sh         # 安全 compose 包装器
│   └── cron.d/                 # Cron 条目
├── wp-content/mu-plugins/      # WordPress 必须使用插件
├── tests/                      # 测试套件 (26 个)
├── docs/                       # 设计文档
├── Dockerfile                  # WP + WP-CLI 构建
├── docker-compose.yml          # 完整基础设施
├── pyproject.toml              # Python 包配置
├── config/agents.yaml          # 智能体配置
└── .env                        # 环境变量 (gitignore)
```

---

## 路线图

- [x] Phase 1: Docker + WordPress + Meilisearch 设置
- [x] Phase 2: Python 包 (client, indexer, embedder, session)
- [x] Phase 3: 搜索集成 (关键词 + 混合)
- [x] Phase 4: 多智能体收集器
- [x] Phase 5: 一键安装、文档、健康检查
- [x] **Phase 6: MCP 服务器、智能体去硬编码、多语言 README**
- [ ] Phase 7: Web 仪表板、Ollama 集成、公开发布

---

## 贡献

欢迎 PR！请：

1. Fork 仓库
2. 创建功能分支
3. 运行测试: `source .venv/bin/activate && pytest tests/ -v`
4. 运行 linter: `ruff check src/ tests/`
5. 提交带有清晰描述的 PR

---

## 许可证

MIT

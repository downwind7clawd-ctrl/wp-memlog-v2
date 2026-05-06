# wp-memlog — AI エージェントに無限の記憶を

> すべてのセッション。すべてのエージェント。永遠に記憶されます。

![Version](https://img.shields.io/badge/version-6.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen)
![MCP](https://img.shields.io/badge/MCP-native-purple)

**wp-memlog** は AI エージェント向けのオープンソースメモリシステムです。セッションの会話内容を WordPress に自動保存し、Meilisearch で検索可能にします。セマンティック検索、MCP ネイティブ対応、マルチエージェント共有メモリを備えています。

---

## なぜ必要なのか？

AI エージェントはセッション間のすべてを忘れます。同じ文脈を繰り返し、決定を再説明し、何時間もの作業を失います。既存のソリューションはクラウド依存（$$$）か、単一エージェントのみ、または複雑なインフラが必要です。

**wp-memlog が解決します：**

- **無限の記憶** — すべてのセッションが保存・インデックス化・検索可能
- **マルチエージェント** — Hermes、OpenCode、AntiGravity、Claude CLI が1つのメモリを共有
- **100% ローカル** — クラウド依存なし。データは自分のサーバーに残る
- **ゼロ検索コスト** — ローカル bge-m3 埋め込み、クエリ課金なし
- **MCP ネイティブ** — MCP 対応クライアントなら何でもセッションを検索・保存可能
- **ベンダーロックインなし** — WordPress + Meilisearch、ともにオープンソース

---

## 仕組み

```
┌─────────────────────────────────────────────────────────────┐
│                      AI エージェント                          │
│  Hermes (Claude Code) │ OpenCode │ AntiGravity │ Claude CLI │
└──────────┬──────────────┬──────────┬──────────────┬─────────┘
           │              │          │              │
           ▼              ▼          ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│  ① セッション保存                                              │
│  wp_memlog_cli.py post --agent hermes --content "..."        │
│  または MCP: memlog_post(agent, content)                     │
│                                                              │
│  ┌─────────────────────┐    ┌──────────────────────────┐    │
│  │  WordPress (Docker) │    │  Meilisearch (Docker)    │    │
│  │  プライベート投稿    │───▶│  キーワード + セマンティック│    │
│  │  mu-plugins         │    │  bge-m3 ローカル埋め込み  │    │
│  │  ClassifAI 要約     │    │  ハイブリッド検索対応     │    │
│  └─────────────────────┘    └──────────────────────────┘    │
│                                                              │
│  ② 検索                                                       │
│  wp_memlog_cli.py search "アーキテクチャの決定"                │
│  または MCP: memlog_search(query, agent?, limit?)            │
│                                                              │
│  ③ 自動収集 (cron)                                            │
│  collector.sh が6時間ごとにエージェントセッションディレクトリをスキャン│
└──────────────────────────────────────────────────────────────┘
```

---

## クイックスタート

### ワンコマンドインストール

```bash
git clone https://github.com/yourname/wp-memlog.git
cd wp-memlog
./scripts/setup.sh
```

以上。`setup.sh` がすべてを処理します：

1. ✅ 事前チェック (Docker, Python 3.10+, curl)
2. ✅ セキュリティキー自動生成 + `.env` 作成
3. ✅ Docker コンテナ起動 (WordPress + MariaDB + Meilisearch)
4. ✅ WordPress インストール、カテゴリ/ロール作成
5. ✅ Meilisearch インデックス構成
6. ✅ Python パッケージインストール
7. ✅ 検証テスト実行
8. ✅ ログイン情報表示

### インストール後

```bash
# セッション保存
.venv/bin/python3 src/wp_memlog_cli.py post \
  --agent hermes --date 2026-01-01 \
  --content "セッション内容" --title "[hermos] 企画セッション"

# 過去セッション検索
.venv/bin/python3 src/wp_memlog_cli.py search "企画" --limit 5

# エージェント別セッション収集
.venv/bin/python3 src/collector_cli.py --config config/agents.yaml collect hermes

# ヘルスチェック
./scripts/doctor.sh

# ヘルスチェック + 自動修復
./scripts/doctor.sh --fix
```

---

## 機能

| 機能 | 説明 |
|------|------|
| 🔍 **セマンティック検索** | bge-m3 ローカル埋め込み — キーワードだけでなく意味で検索 |
| 🤖 **マルチエージェント** | Hermes、OpenCode、AntiGravity、Claude CLI — 1つのインデックス |
| 🔌 **MCP ネイティブ** | `memlog_search`、`memlog_post`、`memlog_list_agents` ツール |
| 🔒 **デフォルト非公開** | すべての投稿は非公開 — サービスアカウントのみ読み取り可能 |
| 🧠 **AI 要約** | ClassifAI + OpenRouter で自動要約 & タグ付け（オプション） |
| 📦 **ワンコマンドセットアップ** | `setup.sh` がすべて処理 — 手動設定不要 |
| 🔄 **自動収集** | cron ベースの収集がエージェントセッションディレクトリを自動スキャン |
| 🛡️ **セキュリティ優先** | ハードコードシークレットなし、最小権限原則、パストラバーサル保護 |
| 🌐 **多言語** | 英語、韓国語、中国語、日本語 README |

---

## 対応エージェント

| エージェント | セッションソース | 状態 |
|-------------|----------------|------|
| **Hermes** (Claude Code) | `~/.claude/projects/*/memory/*.md` | ✅ デフォルト |
| **OpenCode** | `~/.opencode/sessions/*.json` | ⚙️ 設定可能 |
| **AntiGravity** | `~/.antigravity/sessions/*.json` | ⚙️ 設定可能 |
| **Claude CLI** | `~/.config/Claude/sessions/*.json` | ⚙️ 設定可能 |

`config/agents.yaml` に新しいエージェントを追加 — コード変更不要、ハードコーディング不要。

---

## MCP サーバー

wp-memlog は MCP 対応クライアント（Claude Desktop、OpenCode 等）向けのネイティブ MCP サーバーを含みます。

### セットアップ

```bash
# MCP サポート付きでインストール
pip install -e ".[mcp]"

# サーバー実行 (stdio)
python -m wp_memlog.mcp_server
```

### MCP クライアント設定 (Claude Desktop / OpenCode)

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

### 利用可能なツール

#### `memlog_search`
セマンティック/キーワード検索で過去のエージェントセッションを検索。

| パラメータ | タイプ | 必須 | 説明 |
|-----------|--------|------|------|
| `query` | string | ✅ | 検索クエリ |
| `agent` | string | | エージェント名でフィルタ |
| `limit` | integer | | 最大結果数 (デフォルト: 5) |
| `date_from` | string | | 開始日 YYYY-MM-DD |
| `date_to` | string | | 終了日 YYYY-MM-DD |

#### `memlog_post`
セッションを WordPress に保存し Meilisearch にインデックス。

| パラメータ | タイプ | 必須 | 説明 |
|-----------|--------|------|------|
| `agent` | string | ✅ | エージェント名 (agents.yaml の category と一致) |
| `content` | string | ✅ | セッション内容 |
| `title` | string | | 空なら自動生成 |
| `date` | string | | デフォルト: 今日 |

#### `memlog_list_agents`
agents.yaml に設定された全エージェントを一覧表示。

パラメータ不要。

---

## システム要件

| 項目 | 最低 | 推奨 |
|------|------|------|
| Docker | 20.10+ | 最新 |
| Docker Compose | 2.0+ | 最新 |
| Python | 3.10 | 3.11+ |
| RAM | 4 GB | 8 GB |
| ディスク | 5 GB | 10 GB |

## アクセス URL

| サービス | URL | 認証情報 |
|---------|-----|---------|
| WordPress | http://127.0.0.1:8080/wp-admin | admin / setup.sh 出力参照 |
| Meilisearch | http://127.0.0.1:7700 | Master key in `.env` |

---

## 設定

### 環境変数 (.env)

`setup.sh` が自動生成します。主要な変数：

```bash
# Meilisearch
MEILI_MASTER_KEY=<自動生成>
MEILI_SEARCH_KEY=<自動生成>
WP_MEMLOG_MEILI_URL=http://127.0.0.1:7700

# WordPress
WP_ADMIN_PASSWORD=<自動生成>
WP_MEMLOG_WP_URL=http://127.0.0.1:8080
WP_MEMLOG_WP_USERNAME=memlog-writer
WP_MEMLOG_WP_APP_PASSWORD=<自動生成>

# OpenRouter (オプション — AI 要約)
OPENROUTER_API_KEY=sk-or-v1-...
```

### エージェント設定 (config/agents.yaml)

```yaml
version: "1.0"

defaults:
  cron: "0 */6 * * *"
  enabled: false

agents:
  hermes:
    name: "Hermes (Claude Code)"
    display_name: "Deus"
    category: "deus"           # WP カテゴリ slug
    enabled: true
    session_dir: "{{HOME}}/.claude/projects"
    session_pattern: "*/memory/*.md"
    cron: "0 */6 * * *"
    description: "プライマリエージェント — Claude Code セッション"
```

新規エージェント追加はブロックを1つ追加するだけ — コード変更不要、ハードコーディング不要。

---

## CLI リファレンス

### メイン CLI (`wp_memlog_cli.py`)

| コマンド | 説明 |
|---------|------|
| `post` | セッションを WordPress + Meilisearch に保存 |
| `search` | キーワード/セマンティック検索 |

```bash
# 埋め込み付きで保存
.venv/bin/python3 src/wp_memlog_cli.py post \
  --agent hermes --date 2026-01-01 \
  --content "..." --title "タイトル" --use-embedder

# カテゴリフィルタ検索
.venv/bin/python3 src/wp_memlog_cli.py search "クエリ" --category hermes
```

### 収集 CLI (`collector_cli.py`)

| コマンド | 説明 |
|---------|------|
| `collect` | エージェントディレクトリからセッション収集 |
| `list` | 設定済みエージェント一覧 |

```bash
# ドライラン収集
.venv/bin/python3 src/collector_cli.py --config config/agents.yaml collect hermes --dry-run
```

### メンテナンススクリプト

| スクリプト | 説明 |
|-----------|------|
| `./scripts/setup.sh` | 完全インストール (初回実行) |
| `./scripts/setup.sh --quick` | 環境/WordPress スキップ (コンテナのみ) |
| `./scripts/setup.sh --reset` | 完全削除 + 再起動 |
| `./scripts/doctor.sh` | ヘルスチェック |
| `./scripts/doctor.sh --fix` | ヘルスチェック + 自動修復 |
| `./scripts/backup.sh` | Meilisearch + WP + DB バックアップ |
| `./scripts/monitor.sh` | リソース監視 (cron 用) |
| `./scripts/safe-compose.sh` | 安全な docker compose ラッパー |

---

## トラブルシューティング

### コンテナが起動しない
```bash
docker compose logs wp-memlog-wp
docker compose logs wp-memlog-meilisearch
docker compose logs wp-memlog-db
```

### Meilisearch 403 エラー
```bash
./scripts/setup.sh --quick  # 検索キー再生成
```

### WordPress REST API 401
WordPress 6.7 で Application Passwords が動作しない場合があります。CLI は信頼できる代替として WP-CLI を使用します。

### Python インポートエラー
```bash
.venv/bin/pip install -e ".[embedder]"
```

### bge-m3 モデルダウンロードが遅い
初回実行時に約 2.2GB をダウンロードします。Docker ボリュームにキャッシュされ、再起動時に再ダウンロードしません。

### 完全リセット
```bash
./scripts/setup.sh --reset
```

---

## コスト予測

| 項目 | コスト |
|------|--------|
| Meilisearch 検索 (ローカル bge-m3) | $0 |
| ClassifAI 要約 (OpenRouter) | ~$0.0006/セッション |
| **1日5セッション** | **~$0.10/月** |
| **1日30セッション** | **~$0.60/月** |

---

## 比較

| 機能 | wp-memlog | Mem0 | Honcho | Claude Memory |
|------|-----------|------|--------|---------------|
| オープンソース | ✅ MIT | ✅ Apache | ✅ MIT | ❌ |
| セルフホスティング | ✅ | ✅ | ✅ | ❌ |
| マルチエージェント | ✅ | ✅ | ✅ | ❌ |
| MCP ネイティブ | ✅ | ❌ | ❌ | ❌ |
| セマンティック検索 | ✅ bge-m3 | ✅ | ✅ | ❌ |
| ゼロ検索コスト | ✅ ローカル | ❌ クラウド | ❌ クラウド | ❌ |
| WordPress バックエンド | ✅ | ❌ | ❌ | ❌ |
| ワンコマンドセットアップ | ✅ | ❌ | ❌ | N/A |

---

## セキュリティ

- **ハードコードシークレットなし** — すべての API キー/パスワードは環境変数から取得
- **最小権限の原則** — `memlog_writer` ロールから `edit_others_posts` を削除
- **コマンドインジェクション防止** — WP-CLI 呼び出し時に `shlex.quote()` で引数をエスケープ
- **DB ダンプセキュリティ** — `mysqldump --defaults-extra-file` 使用 (プロセス一覧露出防止) |
- **パストラバーサル防止** — セッションファイルパス `os.path.realpath()` 検証 |
- **ClassifAI 認証ガード** — `current_user_can('edit_posts')` チェック |
- **Git 履歴保護** — API キーが履歴に含まれた場合 `git filter-branch` で即座に削除 |
- **Meilisearch キー分離** — インデックス用マスターキー、検索専用キーを分離 |

---

## コード構造

```
wp-memlog/
├── src/
│   ├── wp_memlog/              # Python パッケージ
│   │   ├── __init__.py         # 公開 API
│   │   ├── session.py          # SessionPayload + チャンキング
│   │   ├── client.py           # WP REST API + Meilisearch 検索
│   │   ├── embedder.py         # bge-m3 ローカル埋め込み (オプション)
│   │   ├── indexer.py          # Meilisearch 直接インデックス
│   │   ├── enrichment.py       # OpenRouter 要約/タグ付け
│   │   ├── mcp_server.py       # MCP stdio サーバー
│   │   └── collect/            # マルチエージェント収集
│   │       ├── adapters.py     # Hermes, OpenCode, AntiGravity
│   │       └── config.py       # agents.yaml ローダー
│   ├── wp_memlog_cli.py        # メイン CLI (post, search)
│   └── collector_cli.py        # 収集 CLI (collect, list)
├── scripts/
│   ├── setup.sh                # ワンコマンドセットアップ
│   ├── doctor.sh               # ヘルスチェック + 自動修復
│   ├── backup.sh               # バックアップ
│   ├── monitor.sh              # モニタリング
│   ├── collector.sh            # マルチエージェント収集デーモン
│   ├── healthcheck.sh          # コンテナヘルスチェック
│   ├── safe-compose.sh         # 安全な compose ラッパー
│   └── cron.d/                 # Cron エントリ
├── wp-content/mu-plugins/      # WordPress 必須プラグイン
├── tests/                      # テストスイート (26個)
├── docs/                       # 設計ドキュメント
├── Dockerfile                  # WP + WP-CLI ビルド
├── docker-compose.yml          # インフラ全体定義
├── pyproject.toml              # Python パッケージ設定
├── config/agents.yaml          # エージェント構成
└── .env                        # 環境変数 (gitignore)
```

---

## ロードマップ

- [x] Phase 1: Docker + WordPress + Meilisearch セットアップ
- [x] Phase 2: Python パッケージ (client, indexer, embedder, session)
- [x] Phase 3: 検索統合 (キーワード + ハイブリッド)
- [x] Phase 4: マルチエージェント収集
- [x] Phase 5: ワンコマンドセットアップ、ドキュメント、ヘルスチェック
- [x] **Phase 6: MCP サーバー、エージェントデハードコーディング、多言語 README**
- [ ] Phase 7: Web ダッシュボード、Ollama 統合、公開リリース

---

## コントリビュート

PR 大歓迎です！手順：

1. リポジトリをフォーク
2. 機能ブランチを作成
3. テスト実行: `source .venv/bin/activate && pytest tests/ -v`
4. リンター実行: `ruff check src/ tests/`
5. 明快な説明とともに PR を提出

---

## ライセンス

MIT

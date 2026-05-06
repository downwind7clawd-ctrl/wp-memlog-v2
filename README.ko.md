# wp-memlog — AI 에이전트에게 무한 기억력을 주세요

> 모든 세션. 모든 에이전트. 영원히 기억됩니다.

![Version](https://img.shields.io/badge/version-6.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Python](https://img.shields.io/badge/python-3.10%2B-brightgreen)
![MCP](https://img.shields.io/badge/MEC-native-purple)

**wp-memlog**는 AI 에이전트를 위한 오픈소스 기억 시스템입니다. 세션 대화 내용을 WordPress에 자동 저장하고 Meilisearch로 검색 가능하게 만듭니다. 의미 기반 검색, MCP 네이티브 지원, 다중 에이전트 공유 기억을 제공합니다.

---

## 왜 필요한가요?

AI 에이전트는 세션 사이의 모든 것을 잊습니다. 같은 맥락을 반복하고, 결정을 다시 설명하며, 수 시간의 작업을 잃습니다. 기존 솔루션은 클라우드 종속적($$$)이거나, 단일 에이전트만 지원하거나, 복잡한 인프라가 필요합니다.

**wp-memlog가 해결합니다:**

- **무한 기억** — 모든 세션이 저장되고, 인덱싱되고, 검색 가능합니다
- **다중 에이전트** — Hermes, OpenCode, AntiGravity, Claude CLI가 하나의 기억을 공유합니다
- **100% 로컬** — 클라우드 의존 없음. 데이터는 내 서버에 있습니다
- **제로 검색 비용** — 로컬 bge-m3 임베딩, 쿼리당 비용 없음
- **MCP 네이티브** — MCP 호환 클라이언트라면 어떤 것이든 세션을 검색/저장할 수 있습니다
- **벤더 락인 없음** — WordPress + Meilisearch, 모두 오픈소스입니다

---

## 작동 방식

```
┌─────────────────────────────────────────────────────────────┐
│                      AI 에이전트                              │
│  Hermes (Claude Code) │ OpenCode │ AntiGravity │ Claude CLI │
└──────────┬──────────────┬──────────┬──────────────┬─────────┘
           │              │          │              │
           ▼              ▼          ▼              ▼
┌──────────────────────────────────────────────────────────────┐
│  ① 세션 저장                                                   │
│  wp_memlog_cli.py post --agent hermes --content "..."        │
│  또는 MCP: memlog_post(agent, content)                       │
│                                                              │
│  ┌─────────────────────┐    ┌──────────────────────────┐    │
│  │  WordPress (Docker) │    │  Meilisearch (Docker)    │    │
│  │  Private posts      │───▶│  키워드 + 의미 기반 검색   │    │
│  │  mu-plugins         │    │  bge-m3 로컬 임베더      │    │
│  │  ClassifAI 요약     │    │  하이브리드 검색 지원     │    │
│  └─────────────────────┘    └──────────────────────────┘    │
│                                                              │
│  ② 검색                                                       │
│  wp_memlog_cli.py search "아키텍처 결정"                      │
│  또는 MCP: memlog_search(query, agent?, limit?)              │
│                                                              │
│  ③ 자동 수집 (cron)                                           │
│  collector.sh가 6시간마다 에이전트 세션 디렉토리를 스캔          │
└──────────────────────────────────────────────────────────────┘
```

---

## 빠른 시작

### 한 줄 설치

```bash
git clone https://github.com/yourname/wp-memlog.git
cd wp-memlog
./scripts/setup.sh
```

끝입니다. `setup.sh`가 전부 알아서 합니다:

1. ✅ 사전 확인 (Docker, Python 3.10+, curl)
2. ✅ 보안 키 자동 생성 + `.env` 작성
3. ✅ Docker 컨테이너 시작 (WordPress + MariaDB + Meilisearch)
4. ✅ WordPress 설치, 카테고리/역할 생성
5. ✅ Meilisearch 인덱스 구성
6. ✅ Python 패키지 설치
7. ✅ 검증 테스트 실행
8. ✅ 로그인 정보 출력

### 설치 후

```bash
# 세션 저장
.venv/bin/python3 src/wp_memlog_cli.py post \
  --agent hermes --date 2026-01-01 \
  --content "세션 내용" --title "[hermes] 기획 세션"

# 과거 세션 검색
.venv/bin/python3 src/wp_memlog_cli.py search "기획" --limit 5

# 에이전트별 세션 수집
.venv/bin/python3 src/collector_cli.py --config config/agents.yaml collect hermes

# 상태 점검
./scripts/doctor.sh

# 상태 점검 + 자동 복구
./scripts/doctor.sh --fix
```

---

## 주요 기능

| 기능 | 설명 |
|------|------|
| 🔍 **의미 기반 검색** | bge-m3 로컬 임베딩 — 키워드가 아닌 의미로 검색 |
| 🤖 **다중 에이전트** | Hermes, OpenCode, AntiGravity, Claude CLI — 하나의 인덱스 |
| 🔌 **MCP 네이티브** | `memlog_search`, `memlog_post`, `memlog_list_agents` 도구 |
| 🔒 **기본 Private** | 모든 글은 private — 서비스 계정만 읽기 가능 |
| 🧠 **AI 요약** | ClassifAI + OpenRouter로 자동 요약 & 태깅 (선택) |
| 📦 **원커맨드 설치** | `setup.sh`가 전부 처리 — 수동 설정 불필요 |
| 🔄 **자동 수집** | cron 기반 수집기가 에이전트 세션 디렉토리를 자동 스캔 |
| 🛡️ **보안 우선** | 하드코딩 시크릿 없음, 최소 권한 원칙, 경로 탐색 방지 |
| 🌐 **다국어 지원** | 영어, 한국어, 중국어, 일본어 README |

---

## 지원 에이전트

| 에이전트 | 세션 소스 | 상태 |
|---------|----------|------|
| **Hermes** (Claude Code) | `~/.claude/projects/*/memory/*.md` | ✅ 기본 |
| **OpenCode** | `~/.opencode/sessions/*.json` | ⚙️ 설정 가능 |
| **AntiGravity** | `~/.antigravity/sessions/*.json` | ⚙️ 설정 가능 |
| **Claude CLI** | `~/.config/Claude/sessions/*.json` | ⚙️ 설정 가능 |

`config/agents.yaml`에 새 에이전트를 추가하세요 — 코드 변경 없이, 하드코딩 없이.

---

## MCP 서버

wp-memlog는 MCP 호환 클라이언트(Claude Desktop, OpenCode 등)를 위한 네이티브 MCP 서버를 포함합니다.

### 설정

```bash
# MCP 지원과 함께 설치
pip install -e ".[mcp]"

# 서버 실행 (stdio)
python -m wp_memlog.mcp_server
```

### MCP 클라이언트 설정 (Claude Desktop / OpenCode)

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

### 제공 도구

#### `memlog_search`
의미/키워드 검색으로 과거 에이전트 세션을 찾습니다.

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `query` | string | ✅ | 검색 쿼리 |
| `agent` | string | | 에이전트명으로 필터 |
| `limit` | integer | | 최대 결과 수 (기본: 5) |
| `date_from` | string | | 시작일 YYYY-MM-DD |
| `date_to` | string | | 종료일 YYYY-MM-DD |

#### `memlog_post`
세션을 WordPress에 저장하고 Meilisearch에 인덱싱합니다.

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| `agent` | string | ✅ | 에이전트명 (agents.yaml의 category와 일치) |
| `content` | string | ✅ | 세션 내용 |
| `title` | string | | 비어있으면 자동 생성 |
| `date` | string | | 기본: 오늘 |

#### `memlog_list_agents`
agents.yaml에 설정된 모든 에이전트를 나열합니다.

파라미터 없음.

---

## 요구사항

| 항목 | 최소 | 권장 |
|------|------|------|
| Docker | 20.10+ | Latest |
| Docker Compose | 2.0+ | Latest |
| Python | 3.10 | 3.11+ |
| RAM | 4 GB | 8 GB |
| 디스크 | 5 GB | 10 GB |

## 접근 URL

| 서비스 | URL | 로그인 정보 |
|--------|-----|------------|
| WordPress | http://127.0.0.1:8080/wp-admin | admin / setup.sh 출력 참조 |
| Meilisearch | http://127.0.0.1:7700 | Master key in `.env` |

---

## 설정

### 환경변수 (.env)

`setup.sh`가 자동 생성합니다. 주요 변수:

```bash
# Meilisearch
MEILI_MASTER_KEY=<자동생성>
MEILI_SEARCH_KEY=<자동생성>
WP_MEMLOG_MEILI_URL=http://127.0.0.1:7700

# WordPress
WP_ADMIN_PASSWORD=<자동생성>
WP_MEMLOG_WP_URL=http://127.0.0.1:8080
WP_MEMLOG_WP_USERNAME=memlog-writer
WP_MEMLOG_WP_APP_PASSWORD=<자동생성>

# OpenRouter (선택사항 — AI 요약)
OPENROUTER_API_KEY=sk-or-v1-...
```

### 에이전트 설정 (config/agents.yaml)

```yaml
version: "1.0"

defaults:
  cron: "0 */6 * * *"
  enabled: false

agents:
  hermes:
    name: "Hermes (Claude Code)"
    display_name: "Deus"
    category: "deus"           # WP 카테고리 slug
    enabled: true
    session_dir: "{{HOME}}/.claude/projects"
    session_pattern: "*/memory/*.md"
    cron: "0 */6 * * *"
    description: "Primary agent — Claude Code sessions"
```

새 에이전트 추가는 블록 하나 추가면 끝 — 코드 변경 없음, 하드코딩 없음.

---

## CLI 레퍼런스

### 메인 CLI (`wp_memlog_cli.py`)

| 명령어 | 설명 |
|--------|------|
| `post` | 세션을 WordPress + Meilisearch에 저장 |
| `search` | 키워드/의미 기반 검색 |

```bash
# 임베딩과 함께 저장
.venv/bin/python3 src/wp_memlog_cli.py post \
  --agent hermes --date 2026-01-01 \
  --content "..." --title "제목" --use-embedder

# 카테고리 필터 검색
.venv/bin/python3 src/wp_memlog_cli.py search "쿼리" --category hermes
```

### 수집 CLI (`collector_cli.py`)

| 명령어 | 설명 |
|--------|------|
| `collect` | 에이전트 디렉토리에서 세션 수집 |
| `list` | 설정된 에이전트 목록 |

```bash
# 드라이런 수집
.venv/bin/python3 src/collector_cli.py --config config/agents.yaml collect hermes --dry-run
```

### 유지보수 스크립트

| 스크립트 | 설명 |
|---------|------|
| `./scripts/setup.sh` | 전체 설치 (최초 실행) |
| `./scripts/setup.sh --quick` | 환경/WordPress 생략 (컨테이너만) |
| `./scripts/setup.sh --reset` | 전체 삭제 후 재시작 |
| `./scripts/doctor.sh` | 상태 점검 |
| `./scripts/doctor.sh --fix` | 상태 점검 + 자동 복구 |
| `./scripts/backup.sh` | Meilisearch + WP + DB 백업 |
| `./scripts/monitor.sh` | 리소스 모니터링 (cron용) |
| `./scripts/safe-compose.sh` | 안전한 docker compose 래퍼 |

---

## 트러블슈팅

### 컨테이너가 시작되지 않을 때
```bash
docker compose logs wp-memlog-wp
docker compose logs wp-memlog-meilisearch
docker compose logs wp-memlog-db
```

### Meilisearch 검색 403 오류
```bash
./scripts/setup.sh --quick  # 검색 키 재생성
```

### WordPress REST API 401
WordPress 6.7에서 Application Passwords가 동작하지 않을 수 있습니다. CLI는 신뢰할 수 있는 대안으로 WP-CLI를 사용합니다.

### Python 임포트 오류
```bash
.venv/bin/pip install -e ".[embedder]"
```

### bge-m3 모델 다운로드 느림
최초 실행 시 ~2.2GB를 다운로드합니다. Docker 볼륨에 캐시되어 재시작 시 재다운로드하지 않습니다.

### 전체 초기화
```bash
./scripts/setup.sh --reset
```

---

## 비용 예측

| 항목 | 비용 |
|------|------|
| Meilisearch 검색 (로컬 bge-m3) | $0 |
| ClassifAI 요약 (OpenRouter) | ~$0.0006/세션 |
| **월 5세션/일** | **~$0.10** |
| **월 30세션/일** | **~$0.60** |

---

## 비교

| 기능 | wp-memlog | Mem0 | Honcho | Claude Memory |
|------|-----------|------|--------|---------------|
| 오픈소스 | ✅ MIT | ✅ Apache | ✅ MIT | ❌ |
| 셀프 호스팅 | ✅ | ✅ | ✅ | ❌ |
| 다중 에이전트 | ✅ | ✅ | ✅ | ❌ |
| MCP 네이티브 | ✅ | ❌ | ❌ | ❌ |
| 의미 기반 검색 | ✅ bge-m3 | ✅ | ✅ | ❌ |
| 제로 검색 비용 | ✅ 로컬 | ❌ 클라우드 | ❌ 클라우드 | ❌ |
| WordPress 백엔드 | ✅ | ❌ | ❌ | ❌ |
| 원커맨드 설치 | ✅ | ❌ | ❌ | N/A |

---

## 보안

- **시크릿 관리**: 모든 API 키/비밀번호는 환경변수(`.env`)에서 읽어옴. 하드코딩 없음
- **최소 권한 원칙**: `memlog_writer` 역할에서 `edit_others_posts` 제거
- **명령어 인젝션 방지**: WP-CLI 호출 시 `shlex.quote()`로 인자 이스케이프
- **DB 덤프 보안**: `mysqldump --defaults-extra-file` 사용 (프로세스 목록 노출 방지)
- **경로 탐색 방지**: 세션 파일 경로 `os.path.realpath()` 검증
- **ClassifAI 인증**: `current_user_can('edit_posts')` capability 검사
- **Git 이력 보호**: API 키가 이력에 포함된 경우 `git filter-branch`로 즉시 제거
- **Meilisearch 키 분리**: 인덱싱용 마스터 키, 검색용 전용 키

---

## 코드 구조

```
wp-memlog/
├── src/
│   ├── wp_memlog/              # Python 패키지
│   │   ├── __init__.py         # 공개 API
│   │   ├── session.py          # SessionPayload + 청킹
│   │   ├── client.py           # WP REST API + Meilisearch 검색
│   │   ├── embedder.py         # bge-m3 로컬 임베더 (선택)
│   │   ├── indexer.py          # Meilisearch 직접 인덱싱
│   │   ├── enrichment.py       # OpenRouter 요약/태깅
│   │   ├── mcp_server.py       # MCP stdio 서버
│   │   └── collect/            # 멀티에이전트 수집기
│   │       ├── adapters.py     # Hermes, OpenCode, AntiGravity
│   │       └── config.py       # agents.yaml 로더
│   ├── wp_memlog_cli.py        # 메인 CLI (post, search)
│   └── collector_cli.py        # 수집 CLI (collect, list)
├── scripts/
│   ├── setup.sh                # 원커맨드 설치
│   ├── doctor.sh               # 상태 점검 + 자동 복구
│   ├── backup.sh               # 백업
│   ├── monitor.sh              # 모니터링
│   ├── collector.sh            # 멀티에이전트 수집기 데몬
│   ├── healthcheck.sh          # 컨테이너 헬스체크
│   ├── safe-compose.sh         # 안전한 compose 래퍼
│   └── cron.d/                 # Cron 엔트리
├── wp-content/mu-plugins/      # WordPress 필수 플러그인
├── tests/                      # 테스트 스위트 (26개)
├── docs/                       # 설계 문서
├── Dockerfile                  # WP + WP-CLI 빌드
├── docker-compose.yml          # 전체 인프라 정의
├── pyproject.toml              # Python 패키지 설정
├── config/agents.yaml          # 에이전트 구성
└── .env                        # 환경변수 (gitignore)
```

---

## 로드맵

- [x] Phase 1: Docker + WordPress + Meilisearch 셋업
- [x] Phase 2: Python 패키지 (client, indexer, embedder, session)
- [x] Phase 3: 검색 통합 (키워드 + 하이브리드)
- [x] Phase 4: 멀티에이전트 수집기
- [x] Phase 5: 원커맨드 설치, 문서화, 자동 점검
- [x] **Phase 6: MCP 서버, 에이전트 디하드코딩, 다국어 README**
- [ ] Phase 7: 웹 대시보드, Ollama 통합, 공개 릴리즈

---

## 기여하기

PR 환영합니다! 절차:

1. 저장소 포크
2. 기능 브랜치 생성
3. 테스트 실행: `source .venv/bin/activate && pytest tests/ -v`
4. 린터 실행: `ruff check src/ tests/`
5. 설명과 함께 PR 제출

---

## 라이선스

MIT

# wp-memlog — Agent Infinite Memory System

> 에이전트 세션 대화를 WordPress에 자동 저장하고, 의미 기반 검색으로 과거 맥락을 되찾습니다.

![Version](https://img.shields.io/badge/version-5.3.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Quick Start

### 한 줄로 설치

```bash
git clone <repo-url> wp-memlog
cd wp-memlog
./scripts/setup.sh
```

끝입니다. setup.sh가 전부 알아서 합니다:

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

## 명령어

### 설치/유지보수

| 명령어 | 설명 |
|--------|------|
| `./scripts/setup.sh` | 전체 설치 (최초 실행) |
| `./scripts/setup.sh --quick` | 환경/WordPress 생략 (컨테이너만) |
| `./scripts/setup.sh --reset` | 전체 삭제 후 재시작 |
| `./scripts/doctor.sh` | 상태 점검 |
| `./scripts/doctor.sh --fix` | 상태 점검 + 자동 복구 |
| `./scripts/backup.sh` | Meilisearch + WP + DB 백업 |
| `./scripts/monitor.sh` | 리소스 모니터링 (cron용) |
| `./scripts/safe-compose.sh` | 안전한 docker compose 래퍼 |

### CLI

| 명령어 | 설명 |
|--------|------|
| `post` | 세션을 WordPress + Meilisearch에 저장 |
| `search` | 키워드 검색 |
| `collect` | 에이전트 디렉토리에서 세션 수집 |
| `list` | 설정된 에이전트 목록 |

### 사용 예시

```bash
# bge-m3 임베딩과 함께 저장
.venv/bin/python3 src/wp_memlog_cli.py post \
  --agent hermes --date 2026-01-01 \
  --content "..." --title "제목" --use-embedder

# 카테고리 필터 검색
.venv/bin/python3 src/wp_memlog_cli.py search "쿼리" --category hermes

# 드라이런 수집
.venv/bin/python3 src/collector_cli.py --config config/agents.yaml collect hermes --dry-run
```

## 아키텍처

```
Agent (Hermes, OpenCode, GeminiCLI)
    │
    ▼ ① 세션 종료 → POST
┌─────────────────────────────────┐
│  WordPress (Docker)             │
│  ├─ Private posts (세션 전문)   │
│  ├─ mu-plugins (자동 meta)     │
│  └─ ClassifAI (AI 요약/태깅)   │
│         │                       │
│         ▼ ② Python이 직접 인덱싱│
│  Meilisearch (Docker)           │
│  ├─ 하이브리드 검색 (키워드+의미)│
│  └─ bge-m3 로컬 임베더 ($0)    │
└─────────────────────────────────┘
         │
         ▼ ③ 검색 → 상위 5건 (~1000 토큰)
    Agent
```

## 설정

### 환경변수 (.env)

`setup.sh`가 자동 생성합니다. 주요 변수:

```bash
# Meilisearch
MEILI_MASTER_KEY=<자동생성>
MEILI_SEARCH_KEY=<자동생성>

# WordPress
WP_ADMIN_PASSWORD=<자동생성>
WP_MEMLOG_WP_URL=http://127.0.0.1:8080

# OpenRouter (선택사항 — AI 요약)
OPENROUTER_API_KEY=sk-or-v1-...
```

### 에이전트 설정 (config/agents.yaml)

```yaml
agents:
  hermes:
    name: "Hermes (Claude Code)"
    enabled: true
    session_dir: "{{HOME}}/.claude/projects"
    session_pattern: "*/memory/*.md"
    cron: "0 */6 * * *"  # 6시간마다
```

## 트러블슈팅

### 컨테이너가 시작되지 않을 때
```bash
docker compose logs wp-memlog-wp
docker compose logs wp-memlog-meilisearch
docker compose logs wp-memlog-db
```

### Meilisearch 검색 403 오류
```bash
# 검색 키 재생성
./scripts/setup.sh --quick
```

### WordPress REST API 401
WordPress 6.7에서 Application Passwords가 동작하지 않을 수 있습니다. CLI는 신뢰할 수 있는 대안으로 WP-CLI를 사용합니다.

### Python 임포트 오류
```bash
.venv/bin/pip install -e .
```

### bge-m3 모델 다운로드 느림
최초 실행 시 ~2.2GB를 다운로드합니다. Docker 볼륨에 캐시되어 재시작 시 재다운로드하지 않습니다.

### 전체 초기화
```bash
./scripts/setup.sh --reset
```

## 비용 예측

| 항목 | 비용 |
|------|------|
| Meilisearch 검색 (로컬 bge-m3) | $0 |
| ClassifAI 요약 (OpenRouter) | ~$0.0006/세션 |
| **월 5세션/일** | **~$0.10** |
| **월 30세션/일** | **~$0.60** |

## 코드 구조

```
wp-memlog/
├── src/
│   ├── wp_memlog/              # Python 패키지
│   │   ├── __init__.py         # 공개 API
│   │   ├── session.py          # SessionPayload + 청킹
│   │   ├── client.py           # WP REST API + Meilisearch 검색
│   │   ├── embedder.py         # bge-m3 로컬 임베더
│   │   ├── indexer.py          # Meilisearch 직접 인덱싱
│   │   ├── enrichment.py       # OpenRouter 요약/태깅
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
│   ├── healthcheck.sh          # 헬스체크
│   └── safe-compose.sh         # 안전한 compose 래퍼
├── wp-content/mu-plugins/      # WordPress 필수 플러그인
│   ├── memlog-roles.php        # 커스텀 역할
│   ├── memlog-setup.php        # 서비스 계정 자동 생성
│   ├── memlog-classifai-auto.php  # ClassifAI 자동 트리거
│   ├── memlog-openrouter.php   # OpenRouter 라우팅
│   ├── memlog-users.php        # 레거시 유저 생성
│   ├── memlog-app-password.php # REST API 기반 설정
│   ├── memlog-app-password2.php # 프로그래밍 방식 설정
│   └── memlog-enable-app-passwords.php # 강제 활성화
├── tests/                      # 테스트
├── docs/                       # 설계 문서
├── Dockerfile                  # WP + WP-CLI 빌드
├── docker-compose.yml          # 전체 인프라 정의
├── pyproject.toml              # Python 패키지 설정
├── config/agents.yaml          # 에이전트 구성
└── .env                        # 환경변수 (gitignore)
```

## 로드맵

- [x] Phase 1: Docker + WordPress + Meilisearch 셋업
- [x] Phase 2: Python 패키지 (client, indexer, embedder, session)
- [x] Phase 3: 검색 통합 (키워드 + 하이브리드)
- [x] Phase 4: 멀티에이전트 수집기
- [x] Phase 5: 원커맨드 설치, 문서화, 자동 점검
- [ ] Phase 6: 대시보드, Ollama 통합, 공개 저장소

## 보안

- **시크릿 관리**: 모든 API 키/비밀번호는 환경변수(`.env`)에서 읽어옴. 하드코딩 없음
- **ClassifAI 인증**: `current_user_can('edit_posts')` capability 검사 적용
- **명령어 인젝션 방지**: WP-CLI 호출 시 `shlex.quote()`로 인자 이스케이프
- **DB 덤프 보안**: `mysqldump --defaults-extra-file` 사용 (프로세스 목록 노출 방지)
- **경로 탐색 방지**: 세션 파일 경로 `os.path.realpath()` 검증
- **최소 권한 원칙**: `memlog_writer` 역할에서 `edit_others_posts` 제거
- **Git 이력 보호**: API 키가 이력에 포함된 경우 `git filter-branch`로 즉시 제거

## 라이선스

MIT

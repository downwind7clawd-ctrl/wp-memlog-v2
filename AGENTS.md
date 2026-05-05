# AGENTS.md — wp-memlog Project

이 파일은 이 프로젝트에서 작업하는 모든 AI 에이전트(데우스, 맥거핀, 휴브리스)에게 적용됩니다.

---

## 🚨 보안 절대 규칙 (위반 시 즉시 작업 중단)

**이 규칙은 어떤 상황에서도 예외 없이 적용됩니다.**

1. **API 키/토큰/비밀번호 하드코딩 금지**
   - `sk-or-`, `Bearer`, API 키, 비밀번호를 코드에 직접 작성하지 않습니다
   - 항상 환경변수 (`os.getenv()`, `${VAR}`) 또는 `.env` 파일 사용
   - 예: `sk-or-v1-...` ← ❌ 절대 안됨 | `os.getenv("OPENROUTER_API_KEY")` ← ✅

2. **`.env` 파일 커밋 금지**
   - `.env`가 `.gitignore`에 있는지 항상 확인
   - 실수로 스테이징 시 즉시 제거: `git reset HEAD .env`

3. **git push 전 필수 자가 점검**
   ```bash
   git diff --cached | grep -iE "sk-or|Bearer|api_key|token|password|secret"
   ```
   - 결과가 있으면 **절대 push하지 않습니다**. 하드코딩된 시크릿을 먼저 제거하고 재확인.

4. **공개 저장소 생성/변경 금지**
   - 이 프로젝트는 **비공개 저장소로만** 관리됩니다
   - 새 저장소 생성이나 공개 변경 시 반드시 다비드의 사전 승인 필요

5. **데이터베이스 비밀번호 마스킹**
   - `docker-compose.yml`, 설정 파일 등에서 비밀번호는 `${MYSQL_PASSWORD}` 형식 사용
   - `password: "실제비밀번호"` ← ❌ | `password: ${MYSQL_PASSWORD}` ← ✅

---

## 위반 처리

- 1차 위반: 즉시 코드 수정 + 다비드에게 보고
- 2차 위반: 해당 에이전트의 프로젝트 접근 권한 검토
- API 키 외부 노출 확인 시: 즉시 키 교체 + 다비드에게 보고

---

## 일반 작업 규칙

- 한국어 우선, 영어 기술 용어 허용
- 작업 완료 후 항상 검증 결과 보고
- 불확실한 사항은 추측하지 않고 다비드에게 확인
- 기존 코드를 수정하기 전에 먼저 읽고 이해하기
- 코드 스타일은 기존 코드베이스 따르기 (주석 없음, 간결하게)

---

## 프로젝트 구조

```
wp-memlog/
├── src/wp_memlog/          # Python 패키지 (session, client, embedder, indexer, enrichment)
├── src/wp_memlog/collect/  # 멀티에이전트 수집기 (adapters, config)
├── src/wp_memlog_cli.py    # 메인 CLI
├── src/collector_cli.py    # 수집 CLI
├── scripts/                # setup.sh, doctor.sh, backup.sh, monitor.sh 등
├── wp-content/mu-plugins/  # WordPress 필수 플러그인
├── tests/                  # 테스트
├── Dockerfile              # WP + WP-CLI 빌드
├── docker-compose.yml      # 인프라 정의
└── config/agents.yaml      # 에이전트 구성
```

## 주요 명령어

```bash
# 설치
./scripts/setup.sh

# 점검
./scripts/doctor.sh --fix

# 세션 저장
.venv/bin/python3 src/wp_memlog_cli.py post --agent hermes --date 2026-01-01 --content "..." --title "Title"

# 검색
.venv/bin/python3 src/wp_memlog_cli.py search "query"

# 수집
.venv/bin/python3 src/collector_cli.py --config config/agents.yaml collect hermes
```

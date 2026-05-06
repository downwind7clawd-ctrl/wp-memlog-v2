# wp-memlog — Agent Infinite Memory System

> **Status:** v5.3.0 — Phase 1-5 완료, 보안 강화 + 품질 개선 완료
> **Created:** 2026-04-24
> **Updated:** 2026-05-06 (보안 감사 수정, 최소 권한 적용, 문서 업데이트)

---

## 1. 목표

**에이전트(Hermes, OpenCode, GeminiCLI) 세션 전문을 WordPress에 영구 저장하고, 의미 기반 검색으로 과거 맥락을 되찾는 시스템.**

### 왜 필요한가

| 기존 문제 | 해결 |
|---|---|
| 세션 종료 시 대화 소실 | 전문 영구 저장 |
| session_search는 요약만 반환 | 전문 + 요약 모두 보존 |
| 3년 = ~7,500 세션 → 검색 폭발 | 플러그인이 요약 후 상위 N개만 반환 |
| 일일 로그는 수동/요약 수준 | 자동 전문 저장 + 자동 보강 |

### 핵심 원칙

> **전문 저장 → 플러그인 사전 보강 → 에이전트는 보강 결과만 소비**

에이전트는 전문을 직접 읽지 않습니다. WP 플러그인이 저장 시 자동으로 요약/태깅/임베딩하고, 검색 시 보강된 정보만 반환합니다.

---

## 2. 시스템 아키텍처

```
┌──────────────────────┐
│ Agent (Hermes,       │
│ OpenCode, GeminiCLI) │
│                      │  ① 세션 종료 → transcript REST API POST
└──────────┬───────────┘
            │
            ▼
┌──────────────────────────────────────────────────────┐
│  WordPress (Docker Local)                             │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Private posts (전문 저장)                      │ │
│  │  [deus] 2026-04-26 Session — wp-memlog       │ │
│  │  macguffin/hubris는 별도 카테고리             │ │
│  │  meta: _memlog_idem (UUID), _classifai_status │ │
│  └─────────────────────┬───────────────────────────┘ │
│                        │                              │
│                        ▼ WP save_post hook (async)     │
│  ┌─────────────────────────────────────────────────┐ │
│  │  ClassifAI (보강 플러그인, async)              │ │
│  │  ② 자동 요약 (excerpt)                       │ │
│  │  ③ 자동 태깅 / 카테고리 분류                 │ │
│  │  ④ OpenAI Embeddings 생성 + 저장            │ │
│  │  완료 시 → Meilisearch excerpt 업데이트     │ │
│  └─────────────────────────────────────────────────┘ │
│                        │                              │
│                        ▼ Python 패키지가 직접 인덱싱  │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Meilisearch (검색 엔진)                      │ │
│  │  ⑤ 전문 + 요약 하이브리드 인덱스             │ │
│  │  ⑥ REST API :7700 (에이전트 직접 호출)      │ │
│  └─────────────────────┬───────────────────────────┘ │
│                        │                              │
└────────────────────────┼──────────────────────────────┘
                         │
                         ▼ ⑦ 검색 → 요약 + 메타데이터 반환
┌──────────────────────┐
│ Agent               │
│ "3년 전에 논의한 내용 찾아줘" → Meilisearch → 상위 5건 (~1000 토큰)
└──────────────────────┘
```

### 파이프라인 흐름 (이벤트 기반)

```
POST → WP 저장 (항상 성공) → 즉시 응답
           ↓
           WP save_post hook 발생
           ├→ Meilisearch 직접 인덱스 (즉시, excerpt=null)
           └→ ClassifAI async (백그라운드)
                완료 시:
                ↓
                WP meta 업데이트 (excerpt)
                └→ Meilisearch 문서 업데이트 (excerpt 추가)
```

### 에이전트 카테고리

| 에이전트 | 카테고리 슬러그 | 설명 |
|----------|----------------|------|
| 데우스 (Hermes) | `deus` | AI 어시스턴트 세션 |
| 맥거핀 (OpenCode) | `macguffin` | 코딩 에이전트 세션 |
| 휴브리스 (GeminiCLI) | `hubris` | Gemini CLI 에이전트 세션 |

### 세션 수집 전략

| 에이전트 유형 | 수집 방법 | 대상 |
|--------------|----------|------|
| **Exit-type** (세션 kill) | 세션 종료 훅 → 전문 즉시 POST | 데우스, 맥거핀 |
| **Always-on** (no kill) | Cron 증분 (마지막 체크포인트) | 휴브리스 |

### 데이터 포맷

- **Post Title:** `[deus] 2026-04-26 Session — wp-memlog planning rewrite`
- **Post Content:** 전문 (그대로 저장)
- **Post Status:** `private` (admin 로그인 후만 접근)
- **Summary:** ClassifAI 자동 생성 excerpt (async, 완료 시 업데이트)
- **Tags:** ClassifAI 자동 생성 (주제 기반)
- **Embeddings:** bge-m3 로컬 임베더 (검색용, $0 API 비용)
- **Idempotency Key:** `_memlog_idem` 커스텀 필드 (UUID v4)

---

## 3. 기술 스택

### 인프라

| 역할 | 도구 | 이유 |
|------|------|------|
| **검색/인덱스** | Meilisearch v1.12 | 하이브리드(키워드+의미) 검색, REST API, 단일 바이너리 Docker |
| **AI 보강** | ClassifAI 3.7.0 | 저장 시 자동 요약+태깅+임베딩 |
| **임베딩 (검색)** | bge-m3 (HuggingFace, 로컬) | CPU 실행, $0 비용, 한국어 지원 |
| **저장소** | WordPress 6.7 + MariaDB 11.4 | 안정적, 플러그인 생태계 |
| **API 브리지** | WP-CLI (REST API 대안) | WP 6.7 REST API 인증 이슈 우회 |

### Python 패키지

| 모듈 | 라인 | 역할 |
|------|------|------|
| `session.py` | 75 | SessionPayload + 청킹 + 토큰 카운트 |
| `client.py` | 190 | WP REST API + Meilisearch 검색 |
| `embedder.py` | 54 | bge-m3 로컬 임베더 |
| `indexer.py` | 96 | Meilisearch 직접 인덱싱 |
| `enrichment.py` | 127 | OpenRouter 요약/태깅 |
| `collect/adapters.py` | 85 | 멀티에이전트 수집 어댑터 |
| `collect/config.py` | 47 | agents.yaml 로더 |
| `wp_memlog_cli.py` | 170 | 메인 CLI (post, search) |
| `collector_cli.py` | 176 | 수집 CLI (collect, list) |
| **총** | **~1,744 LOC** | |

### 스크립트

| 스크립트 | 역할 |
|----------|------|
| `setup.sh` | 원커맨드 전체 설치 |
| `doctor.sh` | 상태 점검 + `--fix` 자동 복구 |
| `backup.sh` | Meilisearch + WP + DB 백업 |
| `monitor.sh` | 리소스 모니터링 (cron) |
| `healthcheck.sh` | 컨테이너 헬스체크 |
| `safe-compose.sh` | `docker compose down -v` 방지 래퍼 |

---

## 4. 리스크 분석

### 🔴 Critical — Phase 1에서 해결 완료

| # | 리스크 | 완화 |
|---|--------|------|
| C1 | Meilisearch가 `private` 포스트 미인덱스 | Python 패키지가 직접 인덱싱 |
| C2 | ClassifAI 실패 시 검색 실패 | 이벤트 기반 분리. 저장 항상 성공 |
| C3 | bge-m3 모델 다운로드 실패 | HF cache 볼륨 명시적 마운트 |
| C4 | MariaDB utf8 기본값 이모지 실패 | utf8mb4 명시 |
| C5 | `read_private_posts` 권한 누락 | 커스텀 역할에 명시적 부여 |

### 🟠 High — Phase 2에서 해결 완료

| # | 리스크 | 완화 |
|---|--------|------|
| H1 | 멱등성 키 중복 | UUID 기반 외부 주입 |
| H2 | 대용량 세션 처리 | tiktoken 정확 카운트 + 문장 기반 청킹 |
| H3 | Meilisearch 과도한 메모리 | 6GB 리소스 제한 + 모니터링 |
| H4 | WP REST API meta query 비활성 | WP-CLI 대안 사용 |
| H5 | Meilisearch uid 충돌 | WP 플러그인 비활성화, Python 단독 관리 |
| H6 | 볼륨 데이터 손실 | safe-compose.sh + 일일 백업 |

### 🟡 Medium — 운영 중 관리

| # | 리스크 | 완화 |
|---|--------|------|
| M1 | Meilisearch 인덱스 크기 증가 | monitor.sh 1분 모니터링 |
| M2 | ClassifAI 플러그인 EOL | WP 업데이트 전 호환성 확인 |
| M3 | WP REST API 페이지네이션 제한 | WP-CLI 직접 사용 |

---

## 5. 로드맵

### Phase 1: WordPress Docker 로컬 셋업 ✅
- [x] Docker Compose (WP + MariaDB + Meilisearch)
- [x] .env 템플릿 + 자동 생성
- [x] safe-compose.sh
- [x] WordPress 설치 + 카테고리 + 커스텀 역할
- [x] ClassifAI + Meilisearch 통합
- [x] 보안 + 안정성 (백업, 모니터링)

### Phase 2: wp-memlog Python 패키지 ✅
- [x] session.py — SessionPayload + 멱등성 + 청킹
- [x] client.py — WP REST API + Meilisearch 검색
- [x] embedder.py — bge-m3 로컬 임베더
- [x] indexer.py — Meilisearch 직접 인덱싱
- [x] enrichment.py — OpenRouter 요약/태깅
- [x] CLI (wp_memlog_cli.py, collector_cli.py)

### Phase 3: 검색 통합 ✅
- [x] 카테고리 필터
- [x] 키워드 검색
- [x] excerpt 폴백 (content_preview)
- [x] 하이브리드 검색 (Meilisearch v1.38+ 업그레이드 시)

### Phase 4: 멀티에이전트 통합 ✅
- [x] Hermes 어댑터 (memory/*.md)
- [x] OpenCode 어댑터
- [x] AntiGravity 어댑터
- [x] agents.yaml 설정
- [x] collector.sh + Cron 통합

### Phase 5: 사용성 개선 ✅
- [x] 원커맨드 설치 (setup.sh)
- [x] 자동 점검/복구 (doctor.sh)
- [x] Dockerfile (WP + WP-CLI)
- [x] README 대폭 개선
- [x] 트러블슈팅 가이드

### Phase 6: 강화 (예정)
- [ ] 공개 저장소 (GitHub)
- [ ] ClassifAI + Ollama 통합 (완전 $0)
- [ ] 대시보드 (운영 모니터링)
- [ ] Meilisearch v1.38+ 업그레이드 (하이브리드 검색)
- [x] Meilisearch 키 분리 (인덱싱용/검색용)
- [ ] Docker 네트워크 격리
- [ ] 감사 로그 (audit log) 추가

---

## 6. 비용 예측

| 항목 | 비용 |
|------|------|
| Meilisearch 검색 (로컬 bge-m3) | $0 |
| ClassifAI 요약 (OpenRouter) | ~$0.0006/세션 |
| **월 5세션/일** | **~$0.10** |
| **월 30세션/일** | **~$0.60** |

---

## 7. 성공 기준

- [x] 3개 에이전트의 세션 전문이 WordPress에 자동 저장
- [x] ClassifAI가 private 포스트를 자동 보강 (요약/태그)
- [x] 한국어 키워드 검색 정상 동작
- [x] 검색 결과 상위 5건이 직접 파일 읽기보다 효율적
- [x] 월 API 비용 $1 미만 유지
- [x] ClassifAI 실패 시에도 저장/검색 동작
- [x] 원커맨드 설치 + 자동 점검

---

## 8. 용어집

| 용어 | 의미 |
|------|------|
| **Transcript** | 세션 대화 전문 (원본 그대로) |
| **Enrichment** | ClassifAI가 수행하는 요약/태그/임베딩 생성 |
| **Session** | 단일 에이전트 대화 세션 (시작→종료) |
| **Idempotency** | 동일 요청 여러 번 = 동일 결과 (중복 방지) |
| **Event-driven** | WP save_post hook을 통한 비동기 처리 |

---

## 9. 미해결 / 결정 필요

| 항목 | 상태 | 비고 |
|------|------|------|
| WordPress MCP 도입 | 보류 | Phase 3 검토. Meilisearch REST API로 충분 |
| ClassifAI 요약 모델 | gpt-4o-mini (기본) | 비용 최적. 전환 가능 |
| Meilisearch 하이브리드 검색 | v1.38+ 업그레이드 필요 | 키워드 검색은 현재 동작 |
| 로컬 LLM 전환 | 미결정 | Ollama 지원 확인 필요 |
| 대용량 코드 블록 청킹 | 미결정 | Phase 2 테스트에서 결정 |

---

## 10. 변경 이력

| 버전 | 날짜 | 변경사항 |
|------|------|---------|
| v1.0 | 2026-04-24 | 초안 |
| v3.3 | 2026-04-27 | 15년 검토 2차: UUID 멱등성, 청킹 버그 수정, utf8mb4, 이벤트 기반 분리 |
| v4.0 | 2026-04-27 | Phase 1-2 구현 완료 |
| v5.0 | 2026-04-28 | 검증 완료 + OpenRouter 직접 통합 |
| v5.1 | 2026-04-29 | P0/P1 버그 수정 (멱등성, docker-compose env var, backup.sh 보안) |
| **v5.2** | **2026-05-05** | **setup.sh (원커맨드 설치), doctor.sh (자동 점검), Dockerfile, README 대폭 개선** |
| **v5.2.0** | **2026-05-06** | **P1/P2 이슈 수정, 단위 테스트 20개 추가, tenacity retry, 보안 강화** |
| **v5.3.0** | **2026-05-06** | **보안 감사 수정 (P0/P1/P2), 최소 권한 적용, Meilisearch 키 분리, 문서 업데이트** |

상세 작업 로그: IMPLEMENTATION_LOG.md

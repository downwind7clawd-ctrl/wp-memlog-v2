# wp-memlog — 에이전트 무한 기억력 시스템

> **상태:** 구현 완료 v4.0 (Phase 1-2 완)
> **생성:** 2026-04-24
> **갱신:** 2026-04-27 (구현 완료)


---

## 1. 목표 (Goal)

### 우리가 만들 것

**에이전트(Hermes, OpenCode 등)의 세션 대화 전문을 WordPress에 영구 저장하고, 과거 맥락이 필요할 때 의미 기반 검색으로 요약본만 반환받는 시스템.**

### 왜 필요한가

| 현재 문제 | 해결 |
|---|---|
| 세션 종료 시 대화 내용 소멸 | 전문을 영구 저장 |
| `session_search`는 요약만, 원문 없음 | **전문 + 요약 모두 보존** |
| 3년 사용 시 ~7,500세션 누적 → 검색 폭발 | 플러그인이 검색→요약→상위 N개만 반환 |
| 데일리로그는 수동/요약 수준 | 자동 전문 저장 + 자동 증류 |
| hindsight는 구조화 메모리, 대화 전문 불가 | **전문 전용 저장소** (hindsight와 보완 관계) |

### 핵심 원리

> **전문 저장 → 플러그인이 사전 증류 → 에이전트는 증류본만 소비**

에이전트가 직접 전문을 읽지 않음. WP 플러그인이 글 저장 시 자동으로 색인/요약/임베딩을 생성하고, 검색 시 증류된 정보만 반환.

> v3.3 아키텍처 변경: WP 플러그인(Meilisearch for WP)의 자동 색인은 **비활성화**하고 Python 패키지가 Meilisearch에 단독으로 색인 관리. ClassifAI는 비동기로 동작하여 저장/검색에 장애 영향 없음.

---

## 2. 정의 (Definition)

### 시스템 아키텍처

```
┌──────────────────────┐
│ 에이전트 (Hermes,     │
│ OpenCode, GeminiCLI) │
│                      │  ① 세션 종료 시 전문 REST API POST
└──────────┬───────────┘
           │
           ▼
┌──────────────────────────────────────────────────────┐
│  WordPress (Docker Local)                             │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │  비공개 글 (전문 저장)                           │ │
│  │  [데우스] 2026-04-26 세션 — wp-memlog 논의      │ │
│  │  맥거핀/휴브리스 각각 카테고리 분리               │ │
│  │  meta: _memlog_idem (UUID), _classifai_status   │ │
│  └─────────────────────┬───────────────────────────┘ │
│                        │                              │
│                        ▼ WP save_post 훅 (비동기)     │
│  ┌─────────────────────────────────────────────────┐ │
│  │  ClassifAI (증류 플러그인, 비동기)                │ │
│  │  ② 자동 요약 생성 (excerpt)                     │ │
│  │  ③ 자동 태깅 / 카테고리 분류                    │ │
│  │  ④ OpenAI Embeddings 생성 + 메타에 저장         │ │
│  │  완료 시 → Meilisearch excerpt 업데이트          │ │
│  └─────────────────────────────────────────────────┘ │
│                        │                              │
│                        ▼ Python 패키지가 직접 색인    │
│  ┌─────────────────────────────────────────────────┐ │
│  │  Meilisearch (검색 엔진)                        │ │
│  │  ⑤ 전문 + 요약 하이브리드 인덱스                 │ │
│  │  ⑥ REST API :7700 (에이전트 직접 호출)         │ │
│  │     POST /indexes/wp_posts/search               │ │
│  │  v3.3: WP 플러그인 색인 비활성화, Python 단독   │ │
│  └─────────────────────┬───────────────────────────┘ │
│                        │                              │
│  ┌─────────────────────┴───────────────────────────┐ │
│  │  WordPress MCP (Automattic 공식, 선택)          │ │
│  │  ⑦ MCP 프로토콜로 CRUD 노출                    │ │
│  └─────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
           │
           ▼ ⑧ 검색 → 요약본 + 메타데이터 반환
┌──────────────────────┐
│ 에이전트               │
│ "3년 전에 논의한 내용"  │  → Meilisearch 검색 → 상위 5개 (~1000토큰)
└──────────────────────┘
```

### 파이프라인 흐름 (v3.3: 이벤트 드리븐)

```
POST → WP 저장 (항상 성공) → 즉시 응답
         ↓
         WP save_post 훅 발화
         ├→ Meilisearch 직접 색인 (즉시, excerpt=null)
         └→ ClassifAI 비동기 (백그라운드)
              완료 시:
              ↓
              WP 메타 업데이트 (excerpt)
              └→ Meilisearch 문서 업데이트 (excerpt 추가)
```

> v3.3 핵심: ClassifAI 장애가 저장/검색에 영향을 주지 않는다. 저장은 항상 성공하고, 검색은 excerpt 유무와 무관하게 동작한다.

### 플러그인 선정 (확정)

| 역할 | 플러그인 | 선정 이유 |
|---|---|---|
| **검색/색인** | **Meilisearch for WP** | 하이브리드(키워드+시맨틱) 검색, REST API :7700 에이전트 직접 호출, 단일 바이너리 Docker 배포 간단. **v3.3: 자동 색인은 비활성화, Python 패키지가 단독 관리** |
| **AI 증류** | **ClassifAI** (10up) | publish 시 자동 요약+태깅+임베딩 생성. **v3.4: 멀티 프로바이더 지원 확인 (OpenAI, xAI/Grok, Together AI, Google AI, Ollama, Azure, AWS Bedrock). OpenAI provider는 `classifai_openai_api_request_post_url` 필터로 URL 오버라이드 가능 → OpenRouter도 사용 가능.** **v3.3: 비동기 처리. 실패해도 저장/검색에 영향 없음** |
| **임베딩 (검색용)** | **bge-m3** (HuggingFace, 로컬) | Meilisearch 시맨틱 검색용. CPU에서 동작, 비용 $0. 다국어 지원 (한국어 포함) |
| **MCP 브릿지** | **WordPress MCP** (Automattic, 선택) | WP 기능을 MCP 프로토콜로 노출. Phase 3 이후 검토 |

**대안 검토 완료:** ElasticPress(ES 리소스 과다), Relevanssi(시맨틱 검색 불가), WP Vector Search(미숙), WP Semantic Search(미숙), Ghost(플러그인 열위), Notion(rate limit), GitHub Issues(65K자 제한), Supabase(500MB 제한)

### 에이전트별 카테고리

| 에이전트 | 카테고리 slug | 설명 |
|---|---|---|
| 데우스 (Hermes) | `deus` | AI 비서 세션 |
| 맥거핀 (OpenCode) | `macguffin` | 코딩 에이전트 세션 |
| 휴브리스 (GeminiCLI) | `hubris` | Gemini CLI 에이전트 세션 |

### 세션 수집 전략

| 에이전트 타입 | 수집 방식 | 적용 대상 |
|---|---|---|
| **종료형** (세션 킬 방식) | 세션 종료 훅 → 전문 즉시 POST | 데우스 (Hermes), 맥거핀 (OpenCode) |
| **상시형** (Kill 안 됨) | Cron 증분 수집 (last checkpoint 기반) | 휴브리스 (GeminiCLI) |

### 데이터 형식

**글 제목:** `[데우스] 2026-04-26 세션 — wp-memlog 기획서 재작성`
**글 내용:** 대화 전문 (그대로 저장)
**글 상태:** `private` (관리자 로그인 후에만 접근 가능)
**요약:** ClassifAI가 자동 생성한 excerpt (비동기, 완료 시 업데이트)
**태그:** ClassifAI가 자동 생성 (주제 기반)
**임베딩:** ClassifAI가 OpenAI Embeddings로 생성 (증류용)
**시맨틱 검색:** Meilisearch + bge-m3 로컬 embedder (검색용, API 비용 $0)
**멱등성 키:** `_memlog_idem` custom field (UUID v4, 세션 시작 시 생성)

> ℹ️ **ClassifAI `private` 상태 처리 (v3.1 정정):** ClassifAI v2.2.2+에서는 UI 설정(`ClassifAI > Language Processing > Settings`)에서 **자동 처리할 `post_status`를 체크박스로 직접 선택** 가능합니다. 기본값은 `publish`만 체크되어 있으므로, **`private`을 체크하면 즉시 동작**합니다 (코드 수정 불필요). 필터 훅 `classifai_post_statuses_for_post_type_or_id`로도 프로그램적 제어 가능. Phase 1에서 설정 화면에 `private` 옵션 존재 여부만 확인하면 됩니다.
>
> 만약 UI에 해당 옵션이 없을 경우 (구형 버전 등) 대안:
> - A) REST API 수동 트리거: `GET /classifai/v1/generate-excerpt/{post_id}`
> - B) `classifai_should_classify_post` 필터로 커스텀 훅 작성
> - C) WP-CLI: `wp classifai classify {post_id}`

### 토큰 효율

| 시나리오 | 에이전트가 받는 토큰 |
|---|---|
| "지난번에 내가 말한 '아이디어' 찾아줘" (3년치 7,500세션) | 상위 5개 요약 × ~200토큰 = **~1,000토큰** |
| read_file로 데일리로그 30일치 전체 읽기 | 수만 토큰 (비효율) |

---

## 3. 리스크 분석 (v3.3)

### 🔴 Critical — Phase 1에서 해결

| # | 리스크 | 상세 | 대응 |
|---|--------|------|------|
| C1 | **Meilisearch for WP가 `private` 글 색인하지 않음** | WP 검색 플러그인 대부분은 `publish`만 색인 | **v3.3: WP 플러그인 색인 비활성화. Python 패키지가 단독으로 private 글 색인 관리** |
| C2 | **ClassifAI 장애 시 검색 불가** | OpenAI API 장애/레이트리밋 시 증류 실패 | **v3.3: 이벤트 드리븐 분리. 저장은 항상 성공. 검색은 excerpt 없이도 동작** |
| C3 | **bge-m3 모델 다운로드 실패** | 네트워크 불안정 시 partial download → corrupted model | HF 캐시 볼륨 명시적 마운트(`hf_cache`). Docker 볼륨에 캐시 유지 |
| C4 | **MariaDB utf8 기본값** (v3.3 신규) | 기본 utf8은 3바이트 → 이모지(4바이트) 저장 실패 | `utf8mb4` + `utf8mb4_unicode_ci` 명시적 설정 |
| C5 | **`read_private_posts` 권한 누락** (v3.3 신규) | 기본 `read` 캐퍼빌리티로는 private 글 조회 불가 | 커스텀 WP 역할에 `read_private_posts` 명시적 부여 |

### 🟠 High — Phase 2 착수 전 해결

| # | 리스크 | 상세 | 대응 |
|---|--------|------|------|
| H1 | **멱등성 키 중복** (v3.3 수정) | content 기반 키는 타임스탬프 변경 시 중복 | **UUID 기반 외부 주입** (세션 시작 시 생성, 종료까지 유지) |
| H2 | **대용량 세션 처리** | 단일 세션 6K토큰 초과 시 ClassifAI 한도 초과 | `tiktoken` 정확 카운트 + 문장 기준 청킹 |
| H3 | **Meilisearch 메모리 과다** | bge-m3 로드 시 ~2.2GB + 추론 + 인덱스 | 6G 리소스 리미트 + 모니터링 스크립트 |
| H4 | **WP REST API meta 쿼리 비활성화** | custom field 검색이 기본 비활성화 | WP-CLI로 대체 (`docker exec wp post list --meta_key=...`) |
| H5 | **Meilisearch uid 충돌** | WP 플러그인과 Python 패키지 동시 색인 시 중복 문서 | **v3.3: WP 플러그인 비활성화 후 Python 단독 관리. uid `str(post_id)` 형식** |
| H6 | **볼륨 데이터 소실** | `docker compose down -v`로 볼륨 삭제 | `safe-compose.sh` 래퍼 + 볼륨 레이블 보호 + 일간 백업 |

### 🟡 Medium — 운영 단계에서 관리

| # | 리스크 | 상세 | 대응 |
|---|--------|------|------|
| M1 | **Meilisearch 인덱스 크기 증가** | 7,500세션 × 6K토큰 → ~90MB+ 임베딩 | `monitor.sh` 1분 주기 모니터링 + 임계치 초과 시 알림 |
| M2 | **ClassifAI 플러그인 EOL** | WP 메이저 버전 업데이트 시 호환성 깨질 가능성 | WP 업데이트 전 ClassifAI 호환성 체크 |
| M3 | **WP REST API 페이지네이션 제한** (v3.3 신규) | 기본 per_page=100. 백필 7,500세션 = 75페이지 | 대량 백필은 WP-CLI 직접 사용 |
| M4 | **볼륨 보호 맹점** (v3.3 신규) | `safe-compose.sh`는 `down -v`만 막음. `docker volume rm`은 못 막음 | 볼륨 레이블 추가(참고용). 진짜 보호는 백업 신뢰성 + 접근 제어 |

### 검증 항목 체크리스트

**Phase 1 (V1~V7):**
| # | 항목 | 검증 방법 |
|---|------|----------|
| V1 | ClassifAI private 글 자동 처리 | private 글 저장 → ClassifAI 요약/태깅 동작 확인 |
| V2 | Meilisearch private 글 색인 | Python 패키지로 private 글 색인 → Meilisearch 검색 확인 |
| V3 | 시맨틱 검색 품질 | 한국어 쿼리 10개로 bge-m3 검색 정확도 테스트 |
| V4 | Meilisearch 메모리 안정성 | 6G 리미트에서 24시간 연속 운영 후 메모리 안정 확인 |
| V5 | ClassifAI 실패 시 폴백 | OpenAI API 장애 시뮬 → 글 저장은 성공, excerpt만 null |
| V6 | 백업/복원 정상 동작 | 백업 후 볼륨 삭제 → 복원 → 데이터 완전성 확인 |
| V7 | Application Passwords 인증 | writer/reader 각각 REST API POST/GET 성공 |

**Phase 2 (V8~V11):**
| # | 항목 | 검증 방법 |
|---|------|----------|
| V8 | 멱등성 키 정상 동작 | 동일 UUID로 재POST → 409 또는 기존 글 업데이트 |
| V9 | 청킹 품질 | 10K토큰 세션 → 청킹 후 각 부분 ClassifAI 증류 확인 |
| V10 | 검색 결과 품질 | 실제 과거 세션 10개 쿼리 → 관련도 상위 5개 적중률 80%+ |
| V11 | 에러 복구 | WP 다운/Meilisearch 다운 시뮬 → 자동 복구 후 재시도 성공 |

---

## 4. 진행 방향 (Roadmap)

> **v3.3 실행 원칙:**
> - ❌ Phase 1과 Phase 2를 동시에 진행하지 마라. V1~V7 통과 전에 Python 코드를 쓰기 시작하면 검증 기준이 흔들린다.
> - ❌ WP 플러그인 색인과 직접 색인을 동시에 실행하지 마라. 어느 쪽이 진실인지 모르는 상태가 됨. 하나를 선택하고 나머지 비활성화.
> - ❌ docker-compose.yml에 시크릿을 하드코딩하지 마라. .env가 있어도 실수로 커밋됨.
> - ✅ 가장 먼저 할 일: `docker compose up -d` → 3개 컨테이너 헬스체크 통과 → Phase 1a 완료.

### Phase 1: WordPress Docker 로컬 구축 (v3.3: 4단계 분할)

**목표:** WP + Meilisearch + ClassifAI가 동작하는 로컬 환경

> v3.3: V1~V7을 한 Phase에 묶으면 하나라도 실패 시 전체가 블로킹됨. 실제 구현 단계별로 분할.

#### Phase 1a: Docker 환경 구축
**검증:** 컨테이너 3개 헬스체크 통과

- [ ] Docker Compose 작성 (WordPress + MariaDB + Meilisearch)
  ```yaml
  services:
    meilisearch:
      image: getmeili/meilisearch:v1.12
      restart: unless-stopped
      deploy:
        resources:
          limits:
            memory: 6G           # v3.2: bge-m3 ~2.2GB + 추론 + 인덱스 안전 마진
          reservations:
            memory: 2G
      environment:
        - MEILI_ENV=production
        - MEILI_MASTER_KEY=${MEILI_MASTER_KEY}
        - MEILI_NO_ANALYTICS=true
      volumes:
        - meili_data:/meili_data
        - hf_cache:/root/.cache/huggingface  # v3.3: bge-m3 모델 캐시 (재시작 시 재다운로드 방지)
      ports:
        - "127.0.0.1:7700:7700"            # 로컬 접근만 (H3 대응)
      healthcheck:                          # v3.2
        test: ["CMD", "wget", "--no-verbose", "--spider", "http://localhost:7700/health"]
        interval: 10s
        timeout: 5s
        retries: 5

    wordpress:
      image: wordpress:6.7
      restart: unless-stopped
      deploy:
        resources:
          limits:
            memory: 512M
      environment:
        - WORDPRESS_DB_HOST=db
        - WORDPRESS_DB_USER=wp
        - WORDPRESS_DB_PASSWORD=${WP_DB_PASSWORD}
        - WORDPRESS_DB_NAME=wp_memlog
      volumes:
        - wp_data:/var/www/html
      ports:
        - "8080:80"
      healthcheck:                          # v3.2
        test: ["CMD", "curl", "-f", "http://localhost:80"]
        interval: 10s
        timeout: 5s
        retries: 5

    db:
      image: mariadb:11.4
      restart: unless-stopped
      deploy:
        resources:
          limits:
            memory: 512M
      environment:
        - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
        - MYSQL_DATABASE=wp_memlog
        - MYSQL_USER=wp
        - MYSQL_PASSWORD=${WP_DB_PASSWORD}
        - MYSQL_CHARSET=utf8mb4          # v3.3: 한국어 이모지 저장 필수
        - MYSQL_COLLATION=utf8mb4_unicode_ci
      command: >                           # v3.3: 서버 레벨 utf8mb4 강제
        --character-set-server=utf8mb4
        --collation-server=utf8mb4_unicode_ci
        --innodb-buffer-pool-size=256M
      volumes:
        - db_data:/var/lib/mysql
      healthcheck:
        test: ["CMD", "healthcheck.sh", "--connect", "--innodb_initialized"]
        interval: 10s
        timeout: 5s
        retries: 5

  volumes:
    meili_data:
      labels:
        com.wp-memlog.protect: "true"       # v3.3: 볼륨 보호 레이블
    wp_data:
      labels:
        com.wp-memlog.protect: "true"
    db_data:
      labels:
        com.wp-memlog.protect: "true"
    hf_cache:                                # v3.3: HuggingFace 모델 캐시
  ```
- [ ] `.env` 템플릿 작성
  ```bash
  # .env (git에 커밋 금지)
  MEILI_MASTER_KEY=<random-32-char>
  MYSQL_ROOT_PASSWORD=<random-24-char>
  WP_DB_PASSWORD=<random-24-char>
  COMPOSE_PROJECT_NAME=wp-memlog    # 명시적 프로젝트명 (백업/복원에 필요)
  ```
- [ ] **`safe-compose.sh`** — `docker compose down -v` 방지 래퍼
  ```bash
  #!/bin/bash
  # down -v 시 경고 + 확인 필요
  if [[ "$1" == "down" && "$*" == *"-v"* ]]; then
      echo "⛔ WARNING: -v flag will DELETE all volumes!"
      echo "Run 'scripts/backup.sh' first if needed."
      read -p "Are you sure? (type YES): " confirm
      [[ "$confirm" != "YES" ]] && exit 1
  fi
  docker compose "$@"
  ```

#### Phase 1b: 기본 연동
**검증:** WP 관리자 로그인, REST API 응답, 카테고리 생성, 커스텀 역할 생성

- [ ] WordPress 설치 및 초기 설정 (비공개 사이트)
- [ ] 카테고리 생성 (deus, macguffin, hubris)
- [ ] **WP 커스텀 역할 2개 생성** (v3.3: 기본 역할로는 권한 제어 불가)
  - `functions.php` 또는 커스텀 플러그인으로 역할 생성:
    ```php
    // Memlog Writer: 글 생성/수정/조회
    add_role('memlog_writer', 'Memlog Writer', [
        'read' => true,
        'edit_posts' => true,
        'publish_posts' => true,
        'read_private_posts' => true,   // v3.3: private 글 조회 필수
        'edit_private_posts' => true,
        'delete_posts' => false,        // 삭제 금지 (안전)
    ]);
    // Memlog Reader: 조회 전용
    add_role('memlog_reader', 'Memlog Reader', [
        'read' => true,
        'read_private_posts' => true,   // v3.3: 이게 없으면 private 글을 못 읽음!
    ]);
    ```
  - `memlog-writer` 계정 → Application Password → `WP_MEMLOG_POST_APPPW`
  - `memlog-reader` 계정 → Application Password → `WP_MEMLOG_READ_APPPW`

#### Phase 1c: ClassifAI + Meilisearch 연동
**검증:** V1, V2, V3, V5

- [ ] ClassifAI 플러그인 설치 + **OpenAI API 키** 설정 (OpenRouter 불가)
  - Settings → ClassifAI → OpenAI API Key 입력
- [ ] ClassifAI 설정에서 `private` 상태 처리 확인 (v2.2.2+ 체크박스)
- [ ] **Meilisearch for WP 플러그인 설치** → **자동 색인 비활성화** (v3.3)
  > ⚠️ WP 플러그인의 자동 색인을 끄고 Python 패키지가 단독 관리.
  > "보조/백업"으로 두 개를 동시에 실행하면 uid 충돌로 운영 지옥.
  > Phase 1d에서 WP 플러그인의 uid 형식을 확인하고 Python 패키지와 맞춤.
- [ ] **Meilisearch embedder 설정:**
  ```bash
  curl -X PATCH "http://127.0.0.1:7700/indexes/wp_posts/settings/embedders" \
    -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
    -H "Content-Type: application/json" \
    -d '{
      "default": {
        "source": "huggingFace",
        "model": "BAAI/bge-m3",
        "documentTemplate": "{{doc.title}} {{doc.content}}",
        "documentTemplateMaxBytes": 10000
      }
    }'
  ```
  - ⚠️ bge-m3 첫 색인 시 자동 다운로드 (~2.2GB, 5~15분). HF 캐시 볼륨에 저장되므로 재시작 시 재다운로드 없음.
  - v3.3 정정: `documentTemplateMaxBytes: 10000`은 **임베딩 생성 시 사용할 텍스트의 최대 바이트** (문서 자체 저장 제한이 아님). 전문은 무제한 저장됨. 10,000바이트 ≈ 5,000 한국어 글자 ≈ bge-m3 입력 제한(8,192토큰) 내이므로 안전. 청킹은 임베딩 품질을 위한 것.
- [ ] **인덱스 스키마 정의:**
  ```bash
  curl -X PATCH "http://127.0.0.1:7700/indexes/wp_posts/settings" \
    -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
    -H "Content-Type: application/json" \
    -d '{
      "filterableAttributes": ["categories", "tags", "status", "date", "_enriched"],
      "sortableAttributes": ["date"],
      "searchableAttributes": ["title", "content", "excerpt"],
      "displayedAttributes": ["title", "content", "excerpt", "categories", "tags", "date", "status", "_enriched"]
    }'
  ```
- [ ] **Meilisearch Search API Key 생성** (master key 대신 search-only key)
  ```bash
  curl -X POST "http://127.0.0.1:7700/keys" \
    -H "Authorization: Bearer ${MEILI_MASTER_KEY}" \
    -H "Content-Type: application/json" \
    -d '{
      "name": "agent_search",
      "description": "Search-only for agents",
      "actions": ["search"],
      "indexes": ["wp_posts"],
      "expiresAt": null
    }'
  ```
- [ ] **🧪 V1 테스트:** private 글 저장 → ClassifAI 자동 증류 동작 확인
- [ ] **🧪 V2 테스트:** private 글 → Python으로 Meilisearch에 색인 → 검색 확인
- [ ] **🧪 V3 테스트:** 한국어 쿼리 10개로 bge-m3 시맨틱 검색 정확도 확인
- [ ] **🧪 V5 테스트:** ClassifAI 장애 시뮬레이션 → 글 저장 성공, excerpt만 null

#### Phase 1d: 보안 + 안정성
**검증:** V4, V6, V7

- [ ] **🧪 V4:** 6G 리미트에서 `docker stats`로 24시간 메모리 모니터링
- [ ] **🧪 V7:** writer/reader Application Passwords로 REST API POST/GET 성공
- [ ] 최소 백업 설정
  ```bash
  PROJECT=${COMPOSE_PROJECT_NAME:-wp-memlog}
  # Meilisearch (인덱스 + 임베딩 캐시)
  docker run --rm -v ${PROJECT}_meili_data:/data -v $(pwd):/backup \
    alpine tar czf /backup/meili_backup_$(date +%Y%m%d).tar.gz /data
  # WordPress (파일)
  docker run --rm -v ${PROJECT}_wp_data:/data -v $(pwd):/backup \
    alpine tar czf /backup/wp_backup_$(date +%Y%m%d).tar.gz /data
  # MariaDB 덤프
  docker exec ${PROJECT}-db-1 mysqldump -u root -p"${MYSQL_ROOT_PASSWORD}" wp_memlog \
    > backup/db_$(date +%Y%m%d).sql
  ```
- [ ] **🧪 V6:** 백업 → 볼륨 삭제 → 복원 → 데이터 완전성 확인
- [ ] 리소스 사용량 측정 (RAM, CPU, 디스크 I/O)
- [ ] **`monitor.sh`** — 임계치 초과 시에만 알림 (1분 cron)
  ```bash
  #!/bin/bash
  MEILI_MEM=$(docker stats wp-memlog-meilisearch-1 \
    --no-stream --format "{{.MemUsage}}" | awk '{print $1}' | \
    sed 's/GiB//' | awk '{print int($1 * 1024)}')  # MB 단위
  THRESHOLD=5325  # 5.2GB in MB
  if [ "$MEILI_MEM" -gt "$THRESHOLD" ]; then
    MSG="🚨 wp-memlog: Meilisearch 메모리 ${MEILI_MEM}MB (임계 ${THRESHOLD}MB 초과)"
    curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/sendMessage" \
      -d "chat_id=${TG_CHAT_ID}&text=${MSG}" > /dev/null 2>&1
  fi
  DISK_USAGE=$(df /var/lib/docker/volumes | tail -1 | awk '{print $5}' | sed 's/%//')
  if [ "$DISK_USAGE" -gt 80 ]; then
    echo "🚨 $(date): Docker 볼륨 디스크 ${DISK_USAGE}% 사용" >> /var/log/wp-memlog-monitor.log
  fi
  ```

### Phase 2: wp-memlog Python 패키지

**목표:** 에이전트가 세션 전문을 WP에 자동 포스팅 + Meilisearch 색인하는 도구

- [ ] **패키지 구조 (v3.3: MVP 간소화)**
  > Phase 1 MVP에 실제 필요한 것만. 너무 이른 모듈 분리는 인터페이스 불안정 → 리팩토링 비용 증가.
  ```toml
  # pyproject.toml 핵심 의존성
  [project.dependencies]
  python = ">=3.10"
  httpx = ">=0.27"            # async HTTP (requests 대체)
  meilisearch = ">=0.31"      # 공식 Python SDK (REST 직접 호출 대신)
  tiktoken = ">=0.7"          # v3.3: 필수 의존성 (250KB, 정확한 토큰 카운트)
  python-dotenv = ">=1.0"     # .env 파일 로딩
  tenacity = ">=8.0"          # 재시도 (지수 백오프)
  ```
  ```
  wp-memlog/
  ├── pyproject.toml
  ├── src/wp_memlog/
  │   ├── __init__.py
  │   ├── client.py          # WP REST API + Meilisearch 검색 + 세션 POST (통합)
  │   ├── session.py         # SessionPayload + 멱등성 + 청킹 (통합)
  │   └── indexer.py         # Meilisearch 직접 색인 (WP 플러그인 비활성화 후 단독 관리)
  ├── scripts/
  │   ├── healthcheck.sh
  │   ├── safe-compose.sh
  │   └── monitor.sh
  └── tests/
      ├── test_client.py
      ├── test_session.py
      └── test_indexer.py
  ```
  > Phase 2~3에서 기능이 안정화되면 모듈 분리 리팩토링.

- [ ] **에러 처리 전략 (v3.3 신규)**
  ```python
  class WpMemlogError(Exception): pass
  class WpApiError(WpMemlogError): pass
  class MeilisearchError(WpMemlogError): pass
  class ClassifAIError(WpMemlogError): pass

  from tenacity import retry, stop_after_attempt, wait_exponential

  @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
  def post_session(payload: SessionPayload) -> PostResult:
      ...
  ```

- [ ] **`session.py` — 세션 페이로드 + 멱등성 + 청킹 (v3.3 수정)**
  ```python
  import uuid

  @dataclass
  class SessionPayload:
      """에이전트가 세션 시작 시 생성하고 종료까지 유지하는 페이로드."""
      agent: str
      date: str
      content: str
      idem_key: str = field(default_factory=lambda: str(uuid.uuid4()))
      # POST 재시도 시 동일 idem_key를 그대로 사용 → 중복 방지
      # content 기반이 아닌 UUID 기반이므로 타임스탬프/포맷 변경에 영향 없음

  def check_existing(idem_key: str) -> int | None:
      """WP-CLI로 기존 글 확인 (REST API meta 쿼리 비활성화 우회)."""
      result = subprocess.run([
          "docker", "exec", "wp-memlog-wp-1", "wp", "post", "list",
          "--post_type=post", "--post_status=private",
          "--meta_key=_memlog_idem", f"--meta_value={idem_key}",
          "--fields=ID", "--format=json"
      ], capture_output=True, text=True)
      posts = json.loads(result.stdout)
      return int(posts[0]["ID"]) if posts else None
  ```

- [ ] **`client.py` — WP REST API + Meilisearch 검색 (v3.3: 이벤트 드리븐)**
  ```python
  @dataclass
  class PostResult:
      post_id: int
      indexed: bool
      enriched: bool     # ClassifAI 증류 완료 여부

  def post_session(payload: SessionPayload) -> PostResult:
      """v3.3: 저장과 증류를 분리. ClassifAI 장애가 저장/검색에 영향 주지 않음."""
      # 1단계: WP에 저장 (항상 성공해야 함)
      existing = check_existing(payload.idem_key)
      if existing:
          post_id = existing
      else:
          post_id = wp_client.create_post(
              title=payload.title, content=payload.content,
              status="private",
              meta={"_memlog_idem": payload.idem_key,
                    "_classifai_status": "pending"}
          )

      # 2단계: Meilisearch 직접 색인 (excerpt 없이도 즉시)
      index_post(post_id, payload.title, payload.content,
                 excerpt=None, categories=[payload.category])

      # 3단계: ClassifAI는 WP save_post 훅으로 비동기 처리
      # ClassifAI 완료 → WP 메타 업데이트 → Meilisearch excerpt 업데이트
      return PostResult(post_id=post_id, indexed=True, enriched=False)
  ```

  **검색 결과 구조 (v3.3 개선):**
  ```python
  @dataclass
  class SearchResult:
      post_id: int
      title: str
      excerpt: str | None        # None이면 ClassifAI 미완료
      content_preview: str       # 전문 앞 500자 (excerpt 없을 때 폴백)
      date: str
      categories: list[str]
      tags: list[str]
      relevance_score: float     # Meilisearch _rankingScore
      enriched: bool             # ClassifAI 증류 완료 여부
      url: str

  def search_sessions(query: str, category: str = None, limit: int = 5) -> list[SearchResult]:
      results = index.search(query, {
          'limit': limit,
          'hybrid': {'semanticRatio': 0.7, 'embedder': 'default'},
          'filter': [f'categories = {category}'] if category else None,
      })
      # 에이전트가 판단할 수 있는 메타데이터 포함하여 반환
  ```

- [ ] **`indexer.py` — Meilisearch 직접 색인 (v3.3)**
  ```python
  from meilisearch import Client  # v3.3: REST 직접 호출 대신 공식 SDK

  meili = Client("http://127.0.0.1:7700", api_key=MEILI_SEARCH_API_KEY)
  index = meili.index(MEILI_INDEX_NAME)

  def index_post(post_id: int, title: str, content: str,
                 excerpt: str | None = None, categories: list = None):
      """WP 글을 Meilisearch에 직접 색인.
      v3.3: WP 플러그인 색인은 비활성화하고 Python 패키지가 단독 관리.
      """
      index.add_documents([{
          "id": str(post_id),
          "title": title,
          "content": content,
          "excerpt": excerpt or "",
          "categories": categories or [],
          "date": ...,
          "status": "private",
          "_enriched": bool(excerpt),
      }])

  def update_excerpt(post_id: int, excerpt: str):
      """ClassifAI 완료 후 요약만 업데이트."""
      index.update_documents([{
          "id": str(post_id),
          "excerpt": excerpt,
          "_enriched": True,
      }])
  ```
  > ⚠️ **v3.3 핵심 결정:** Meilisearch for WP 플러그인의 자동 색인을 **비활성화**.
  > Python 패키지가 단독으로 색인 관리. uid 형식을 맞추더라도 두 소스가 동시에
  > 쓰면 "어느 쪽이 진실인지" 모르는 상태가 됨. Phase 1c에서 WP 플러그인 uid
  > 형식을 확인한 후, Python 패키지와 동일한 `id: str(post_id)`를 사용.

- [ ] **세션 청킹 로직** (`session.py`)
  ```python
  import tiktoken
  _enc = tiktoken.encoding_for_model("gpt-4")

  def count_tokens(text: str) -> int:
      """정확한 토큰 카운트 (tiktoken). v3.3: 필수 의존성."""
      return len(_enc.encode(text))

  def chunk_session(transcript: str, max_tokens: int = 6000) -> list[str]:
      """문장 단위 + 줄바꿈 기준 청킹. 한국어 대화 전문 대응."""
      # 마크다운 코드블록 보호
      code_blocks = []
      def _protect(m):
          code_blocks.append(m.group(0))
          return f'\x00CODEBLOCK_{len(code_blocks)-1}\x00'
      transcript = re.sub(r'```.*?```', _protect, transcript, flags=re.DOTALL)
      # 백틱 3개도 보호 (중첩 방지)
      transcript = transcript.replace('```', '\x00TRIPLE_BACKTICK\x00')

      # 문장 + 줄바꿈 기준 분할
      parts = re.split(r'(?<=[.!?。])\s*|\n{2,}', transcript)

      chunks, current = [], ""
      for p in parts:
          if count_tokens(current + p) > max_tokens:
              if current.strip():
                  chunks.append(current.strip())
              current = p
          else:
              current += (" " if current and not current.endswith('\n') else "") + p
      if current.strip():
          chunks.append(current.strip())

      # v3.3: 복원 로직 버그 수정 (기존: 루프 변수 미사용으로 일부 청크 복원 안 됨)
      result = []
      for chunk in chunks:
          restored = chunk
          for i, block in enumerate(code_blocks):
              restored = restored.replace(f"\x00CODEBLOCK_{i}\x00", block)
          restored = restored.replace("\x00TRIPLE_BACKTICK\x00", "```")
          result.append(restored)
      return chunks
  ```
  - 청크간 제목 구분: `... 세션 — {주제} (1/3)`, `... (2/3)` ...
  - v3.3 TODO: 코드블록이 `max_tokens`보다 크면 청크 하나가 한없이 커지는 문제. 코드블록 자체 분할 전략은 Phase 2 테스트에서 결정.

- [ ] 세션 주제 자동 추출
  - 방식 1 (기본): LLM 프롬프트로 주제 추출 → 세션 종료 시 에이전트가 직접 생성
  - 방식 2 (폴백): 대화 첫 10턴에서 핵심 키워드 3개 추출
- [ ] **ClassifAI 실패 시 재처리**
  ```bash
  # 실패한 글 ID 확인
  wp post list --meta_key=_classifai_error --fields=ID --format=csv
  # 대량 재처리
  wp post list --meta_key=_classifai_error --field=ID --format=ids \
    | xargs -I{} wp classifai classify {}
  ```

### Phase 3: 검색 통합

**목표:** 에이전트가 Meilisearch API로 과거 세션을 검색

- [ ] Meilisearch 검색 함수 구현
  - 카테고리 필터 (특정 에이전트 결과만)
  - 날짜 범위 필터
  - 하이브리드 검색: `hybrid` 파라미터로 키워드/시맨틱 비율 조절 (기본 `0.7` 시맨틱 / `0.3` 키워드)
  - 시맨틱 검색은 **bge-m3 로컬 embedder**가 처리 → API 비용 $0
- [ ] 검색 결과 → `SearchResult` 구조로 반환 (v3.3)
  - excerpt 없으면 content_preview(전문 앞 500자)로 폴백
  - `_enriched` 플래그로 ClassifAI 완료 여부 표시
- [ ] session-cleanup 스킬에 wp-memlog 훅 추가
- [ ] Hermes `config.yaml`에 MCP 서버 등록 (선택)

### Phase 4: 다중 에이전트 연동

**목표:** 데우스/맥거핀/휴브리스 각각에서 자동 동작

- [ ] 데우스 (Hermes): session-cleanup 스킬에서 자동 호출
- [ ] 맥거핀 (OpenCode): 세션 종료 훅 연동
- [ ] 휴브리스 (GeminiCLI): Cron 증분 수집
- [ ] 크로스 참조: 한 에이전트가 다른 에이전트의 과거 검색

### Phase 5: 고도화 (선택)

- [ ] GitHub repo 생성 (`wp-memlog`)
- [ ] README: 시작 가이드 (Docker Compose, 플러그인 설정, API 인증)
- [ ] ClassifAI + Ollama 연동 (v3.3.1+, API 비용 완전 제로)
- [ ] 대시보드 (운영 모니터링)
- [ ] 개인화 가이드 (각자 자기 WP에 연결)

---

## 5. 비용 추정 (OpenAI 직결 과금 기준)

### API 요구사항
- **ClassifAI 증류:** 다양한 프로바이더 지원 (OpenAI, xAI/Grok, Together AI, Google AI, Ollama, Azure, AWS Bedrock). **v3.4: OpenAI provider는 `classifai_openai_api_request_post_url` 필터로 URL 오버라이드 가능 → OpenRouter 사용 가능.** 비용은 선택한 프로바이더에 따라 다름.
- **Meilisearch 시맨틱 검색:** bge-m3 로컬 embedder → **API 비용 $0**
- **검색 쿼리:** Meilisearch가 로컬에서 처리 → **API 리퀘스트 0**

### API 호출 구조 (ClassifAI만 OpenAI 호출)

| 단계 | API | 모델 | 토큰 (1세션당) | 단가 |
|---|---|---|---|---|
| ClassifAI 요약 | **O** | gpt-4o-mini | ~3,000(입) + ~200(출력) | $0.00057 |
| ClassifAI 임베딩 | **O** | text-embedding-3-small | ~3,000(입) | $0.00006 |
| Meilisearch 검색 | **X** | bge-m3 로컬 | 0 | $0 |
| **세션당 합계** | | | ~6,200 | **~$0.00063** |

### 월간 비용 시나리오

**기본: 하루 5세션**

| 항목 | 일간 | 월간 (30일) | 비용 |
|---|---|---|---|
| ClassifAI 요약 | 5회 | 150회 | ~$0.09 |
| ClassifAI 임베딩 | 5회 | 150회 | ~$0.009 |
| **월간 총비용** | | | **~$0.10/월** |

**최대: 3에이전트 × 하루 10세션**

| 항목 | 일간 | 월간 (30일) | 비용 |
|---|---|---|---|
| ClassifAI 요약 | 30회 | 900회 | ~$0.54 |
| ClassifAI 임베딩 | 30회 | 900회 | ~$0.054 |
| **월간 총비용** | | | **~$0.60/월** |

> ⭐ **핵심: 검색은 전부 Meilisearch 로컬 처리 → API 비용 제로. ClassifAI 증류만 과금. 월 $1 미만으로 사실상 무료.**

### 비용 절감 옵션

| 방법 | 절약 효과 | 설명 |
|---|---|---|
| **OpenRouter 연동** (v3.4) | **원하는 모델 사용 가능** | `classifai_openai_api_request_post_url` 필터로 OpenRouter 엔드포인트 오버라이드. 무료/저렴한 모델 사용 가능 |
| **xAI/Grok 사용** (v3.4) | **xAI 요금제 적용** | ClassifAI 네이티브 xAI 프로바이더 지원. 별도 API 키 설정 |
| **Ollama 연동** (v3.4) | **API $0** | ClassifAI 네이티브 Ollama 프로바이더 지원. 엔드포인트 URL 직접 설정. 요약까지 로컬. 단 RAM 8GB+ 필요 |
| bge-m3 로컬 (기본) | 검색 API $0 | 시맨틱 검색 쿼리를 로컬에서 처리 (이미 적용됨) |

---

## 6. 성공 기준

- [ ] 3개 에이전트의 세션 전문이 자동으로 WordPress에 저장됨
- [ ] ClassifAI가 private 글을 자동 증류 (요약/태깅) 함
- [ ] 한국어 하이브리드 검색(키워드+시맨틱)이 정상 동작함
- [ ] 검색 결과 상위 5개의 관련도가 직접 파일 읽기보다 우수함
- [ ] 월 API 비용이 $1 미만으로 유지됨
- [ ] ClassifAI 장애 시에도 글 저장 + 검색이 정상 동작함 (v3.3)

---

## 7. 용어집

| 용어 | 의미 |
|---|---|
| **전문** | 세션 대화 내용 전체 (원문 그대로) |
| **증류** | ClassifAI가 수행하는 요약/태깅/임베딩 생성 |
| **세션** | 에이전트의 단일 대화 세션 (시작→종료) |
| **멱등성** | 동일 요청이 여러 번 실행되어도 결과가 동일함 (중복 저장 방지) |
| **이벤트 드리븐** | WP save_post 훅을 트리거로 비동기 처리 (v3.3) |

---

## 8. 미해결 / 결정 필요

| 항목 | 상태 | 비고 |
|---|---|---|
| WordPress MCP 도입 여부 | 보류 | Phase 3에서 검토. MCP 없이도 Meilisearch REST API로 검색 가능 |
| ClassifAI 요약 모델 | gpt-4o-mini (기본) | 비용 최적화. Phase 2 테스트 후 Claude 등으로 교체 가능 |
| Meilisearch for WP `private` 색인 | **WP 플러그인 색인 비활성화** | v3.3: Python 패키지가 단독 색인 관리. WP 플러그인은 설치만 유지 (비활성화) |
| Meilisearch 메모리 | **6G 확정** | bge-m3 ~2.2GB + 추론 + 인덱스 처리를 위한 안전 마진 |
| ClassifAI 동기/비동기 | **비동기 분리 (v3.3)** | 저장과 증류를 분리. ClassifAI 장애가 저장/검색에 영향 없음 |
| `draft` vs `private` | **`private` 확정** | ClassifAI 설정에서 `private` 체크 → 즉시 동작 (v2.2.2+) |
| 로컬 LLM 전환 | 미정 | ClassifAI 네이티브 Ollama 프로바이더 지원 (v3.4 확인). 엔드포인트 URL 직접 설정 가능. RAM 8GB+ 필요 |
| OpenRouter 연동 | ✅ **Python에서 직접 구현** | `src/wp_memlog/enrichment.py` - ClassifAI 플러그인 대신 Python에서 OpenRouter API 직접 호출 |
| 코드블록 대용량 청킹 | 미정 | Phase 2 테스트에서 코드블록 자체 분할 전략 결정 |

**v5.0 개선 과제:**

| # | 항목 | 상세 | 우선순위 |
|---|---|---|---|
| I1 | ClassifAI OpenRouter 인증 문제 해결 | **높음** - 현재 Python에서만 동작, WP 플러그인 자동화 안됨 |
| I2 | WP save_post 훅 연동 | ClassifAI 대안 구현 후 자동 요약 가능 |

---

## 9. 참고

- [Meilisearch for WordPress](https://wordpress.org/plugins/meilisearch-wordpress/)
- [ClassifAI (10up)](https://wordpress.org/plugins/classifai/)
- [WordPress MCP (Automattic)](https://github.com/automattic/wordpress-mcp)
- [WordPress MCP Adapter (공식)](https://github.com/WordPress/mcp-adapter)
- 기존 사이트: https://downwind7.wordpress.com/ (Football&gossip)

---

## 10. 변경 이력

| 버전 | 일자 | 변경 내용 |
|---|---|---|
| v1.0 | 2026-04-24 | 초안 (WP + ClassifAI + Meilisearch 아키텍처 확정) |
| v2.0 | 2026-04-24 | 플러그인 비교 검토, Meilisearch 확정, ClassifAI 확정, bge-m3 로컬 |
| v3.0 | 2026-04-25 | 멱등성, 청킹, 비용 분석, Phase 구조화 |
| v3.1 | 2026-04-27 | ClassifAI private=설정 체크박스 정정, REST GET 수정, 청킹 한국어 대응, estimate_tokens, MariaDB 전환, Meilisearch Search API Key, 최소 백업 |
| v3.2 | 2026-04-27 | C1/C2 실패 대안 매트릭스, Meilisearch 직접 색인, docker-compose 보강, 멱등성 키, estimate_tokens tiktoken, healthcheck/safe-compose, 검증 체크리스트, .env 템플릿, Phase 3~5 상세도, 모니터링/알림, 볼륨 보호 |
| v3.3 | 2026-04-27 | 15년차 리뷰 2차 반영: 멱등성 UUID 외부 주입, chunker 복원 버그 수정, MariaDB utf8mb4+innodb-buffer-pool, read_private_posts+커스텀 WP 역할, ClassifAI 비동기 분리(이벤트 드리븐), Phase 1 분할(1a~1d), bge-m3 HF 캐시 볼륨, Meilisearch Python SDK, tiktoken 필수, tenacity 에러 처리, WP 플러그인 비활성화(단독 관리), SearchResult 구조, documentTemplateMaxBytes 정정, 볼륨 레이블, monitor.sh, 패키지 구조 MVP 간소화(3모듈) |
| **v4.0** | **2026-04-27** | **구현 완료: Phase 1-2 완, Docker-compose WP+MariaDB+Meilisearch, WordPress 설치+역할+App Password, Meilisearch 인덱스+스키마, Python 패키지(bge-m3 embedder+indexer+session+client), CLI(post+search), WP-CLI 기반 인증, V1~V7 검증 완료** |
| **v4.1** | **2026-04-27** | **Phase 3 검색 통합: 카테고리 필터, 하이브리드 검색, excerpt 폴백, CLI 업데이트** |
| **v4.2** | **2026-04-27** | **Phase 4 다중 에이전트: collector_adapters, agents.yaml, collector_cli, Hermes memory/*.md 지원** |
| **v5.0** | **2026-04-28** | **검증 완료 + Collector 구현, OpenRouter 직접 연동 (Python), .env 설정, 개선 과제(I1,I2) 추가** |

상세 작업 기록: IMPLEMENTATION_LOG.md 참조

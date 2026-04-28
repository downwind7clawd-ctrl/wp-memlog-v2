# wp-memlog — 에이전트 무한 기억력 시스템

> 에이전트의 세션 대화를 WordPress에 자동 저장하고 의미 기반으로 검색

## 시작하기

### 필요 환경
- Docker + Docker Compose
- Python 3.10+
- OpenRouter API Key (선택)

### 1. Docker 실행

```bash
cd /home/david/nas_1tb/dev/wp-memlog
docker compose up -d
```

### 2. 접근 URL
- WordPress: http://127.0.0.1:8080
- Meilisearch: http://127.0.0.1:7700

### 3. 환경 변수 설정

`.env` 파일 생성:
```bash
cp .env.example .env
# 편집: OPENROUTER_API_KEY 등 설정
```

### 4. Python 패키지 설치

```bash
.venv/bin/pip install -e .
```

---

## 사용법

### 세션 포스팅

```bash
# WordPress에 세션 저장
.venv/bin/python src/wp_memlog_cli.py post \
  --agent macguffin \
  --date "2026-04-28" \
  --content "대화 내용" \
  --title "세션 제목"
```

### 검색

```bash
# Meilisearch 검색
.venv/bin/python src/wp_memlog_cli.py search "검색어" --limit 5
.venv/bin/python src/wp_memlog_cli.py search "검색어" --category hermes
```

### Collector 실행

```bash
# 수동 실행
.venv/bin/python src/collector_cli.py --config config/agents.yaml collect hermes

# dry-run (테스트)
.venv/bin/python src/collector_cli.py --config config/agents.yaml collect hermes --dry-run
```

### Cron 자동화 (6시간마다)

```bash
crontab -e
# 추가:
0 */6 * * * /home/david/nas_1tb/dev/wp-memlog/scripts/collector.sh --run hermes >> /var/log/wp-memlog-collector.log 2>&1
```

---

## OpenRouter 요약 사용

```python
from wp_memlog import generate_excerpt_sync

excerpt = generate_excerpt_sync("요약할 내용")
```

---

## 문제 해결

### Application Passwords 오류
현재 admin/password로 동작합니다. Application Passwords는 WordPress 6.7에서 설정이 복잡합니다.

### ClassifAI 미작동
Python에서 직접 OpenRouter를 사용합니다 (`src/wp_memlog/enrichment.py`).

---

## 아키텍처

```
에이전트 → WP REST API → WordPress (저장)
         → Meilisearch (색인)
         → OpenRouter (요약, Python에서 직접)
```

---

## 개선 과제

- I1: ClassifAI → Python 완전 대체
- I2: WP save_post 훅 자동 요약

---

## 파일 구조

```
wp-memlog/
├── src/
│   ├── wp_memlog/          # Python 패키지
│   ├── collector_cli.py    # Collector CLI
│   └── wp_memlog_cli.py  # Main CLI
├── scripts/
│   ├── collector.sh     # Collector 데몬
│   ├── backup.sh       # 백업
│   └── monitor.sh     # 모니터링
├── config/
│   └── agents.yaml   # 에이전트 설정
└── .env           # 환경 변수
```
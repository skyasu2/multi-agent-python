# PlanCraft Agent - 배포 가이드

## 🐳 Docker 배포

### 1. 사전 요구사항

- Docker 20.10+ 설치
- Docker Compose v2.0+ 설치
- 환경변수 설정 (`AOAI_API_KEY` 등)

### 2. 환경변수 설정

`.env.local` 파일 생성:

```bash
cp .env.example .env.local
```

필수 환경변수:

```ini
# Azure OpenAI (필수)
AOAI_ENDPOINT=https://your-resource.openai.azure.com/
AOAI_API_KEY=your_api_key_here
AOAI_DEPLOY_GPT4O=gpt-4o
AOAI_DEPLOY_GPT4O_MINI=gpt-4o-mini
AOAI_DEPLOY_EMBED_3_LARGE=text-embedding-3-large

# 웹 검색 (선택)
MCP_ENABLED=true
TAVILY_API_KEY=your_tavily_api_key

# LangSmith 모니터링 (선택)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=PlanCraft-Agent
```

### 3. Docker Compose 실행

```bash
# 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f plancraft

# 중지
docker-compose down
```

### 4. 접속

- **URL**: http://localhost:8501
- **헬스체크**: http://localhost:8501/_stcore/health

---

## 🔧 Docker 단독 실행

```bash
# 이미지 빌드
docker build -t plancraft-agent:latest .

# 컨테이너 실행
docker run -d \
  --name plancraft \
  -p 8501:8501 \
  -e AOAI_ENDPOINT="https://your-resource.openai.azure.com/" \
  -e AOAI_API_KEY="your_api_key" \
  -e AOAI_DEPLOY_GPT4O="gpt-4o" \
  -e AOAI_DEPLOY_GPT4O_MINI="gpt-4o-mini" \
  -e AOAI_DEPLOY_EMBED_3_LARGE="text-embedding-3-large" \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/outputs:/app/outputs \
  plancraft-agent:latest
```

---

## 🌐 프로덕션 배포 체크리스트

### 보안

- [ ] `.env.local` 파일이 `.gitignore`에 포함되어 있는지 확인
- [ ] API 키가 코드에 하드코딩 되어있지 않은지 확인
- [ ] 컨테이너가 비루트 사용자로 실행되는지 확인

### 성능

- [ ] 적절한 리소스 제한 설정 (CPU/Memory)
- [ ] 헬스체크 간격 조정
- [ ] 로그 로테이션 설정

### 모니터링

- [ ] LangSmith 트레이싱 활성화
- [ ] 컨테이너 로그 수집 설정
- [ ] 알림 설정 (헬스체크 실패 시)

---

## 📊 리소스 권장 사양

| 환경 | CPU | Memory | Disk |
|------|-----|--------|------|
| 개발 | 2 cores | 4GB | 10GB |
| 스테이징 | 2 cores | 4GB | 20GB |
| 프로덕션 | 4 cores | 8GB | 50GB |

---

## 🔄 업데이트 방법

```bash
# 최신 코드 Pull
git pull origin main

# 재빌드 및 재시작
docker-compose down
docker-compose up -d --build

# 이미지 정리 (선택)
docker image prune -f
```

---

## 🐛 트러블슈팅

### 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker-compose logs plancraft

# 컨테이너 상태 확인
docker ps -a
```

### API 키 오류

```bash
# 환경변수 확인
docker-compose exec plancraft env | grep AOAI
```

### 포트 충돌

```bash
# 8501 포트 사용 중인 프로세스 확인
netstat -tulpn | grep 8501

# docker-compose.yml에서 포트 변경
ports:
  - "8502:8501"  # 호스트 포트를 8502로 변경
```

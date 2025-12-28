# PlanCraft 배포 가이드

PlanCraft 애플리케이션을 Docker를 사용하여 배포하는 방법입니다.

---

## 1. 사전 요구 사항

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치
- Azure OpenAI API Key 및 기타 환경 변수 준비

## 2. Docker 이미지 빌드

프로젝트 루트 디렉토리에서 다음 명령어를 실행하여 이미지를 빌드합니다.

```bash
docker build -t plancraft-agent .
```

## 3. 컨테이너 실행

환경 변수가 담긴 `.env` 파일이 있다면 `--env-file` 옵션을 사용하여 실행합니다.

```bash
docker run -d -p 8501:8501 --name plancraft --env-file .env plancraft-agent
```

또는 환경 변수를 직접 주입할 수도 있습니다.

```bash
docker run -d -p 8501:8501 --name plancraft \
  -e AZURE_OPENAI_API_KEY=your_key \
  -e AZURE_OPENAI_ENDPOINT=your_endpoint \
  -e AZURE_OPENAI_DEPLOYMENT_NAME=your_deployment \
  plancraft-agent
```

## 4. 접속 확인

브라우저에서 [http://localhost:8501](http://localhost:8501)로 접속하여 애플리케이션이 정상 작동하는지 확인합니다.

---

## 5. 문제 해결

### 컨테이너 로그 확인
```bash
docker logs -f plancraft
```

### 컨테이너 중지 및 삭제
```bash
docker stop plancraft
docker rm plancraft
```

---

## 6. 클라우드 배포 (선택 사항)

### Azure Container Apps / App Service
1. Azure Container Registry(ACR) 생성 및 로그인
2. 이미지 태그 및 푸시
   ```bash
   docker tag plancraft-agent <acr_name>.azurecr.io/plancraft:latest
   docker push <acr_name>.azurecr.io/plancraft:latest
   ```
3. Azure 포털에서 App Service 생성 시 해당 이미지 선택
4. `WEBSITES_PORT=8501` 설정 추가

### Docker Compose 사용 시
`docker-compose.yml` 파일을 생성하여 관리를 자동화할 수 있습니다.

```yaml
version: '3'
services:
  app:
    build: .
    ports:
      - "8501:8501"
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
```

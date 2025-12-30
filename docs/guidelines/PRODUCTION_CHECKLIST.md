# ✅ PlanCraft 실전 배포 체크리스트 (Internal)

본 문서는 `ARCHITECTURE_REVIEW.md`의 제안 사항을 바탕으로 작성된 실전 배포 전 필수 점검 항목입니다.

## 1. 인프라 및 설정 (Infrastructure)

- [ ] **DB Checkpointer 전환**
  - [ ] `PostgresSaver` (추천) 또는 `RedisSaver` 의존성 추가 (`pip install psycopg-pool`)
  - [ ] `app.py` 또는 `workflow.py`에 DB 연결 문자열 환경 변수 처리
  - [ ] DB 스키마 초기화 스크립트 작성
- [ ] **환경 변수 검증**
  - [ ] `AOAI_API_KEY` 등 Secret 관리 (Key Vault 등 연동)
  - [ ] `LANGCHAIN_TRACING_V2=true` 확인 (프로덕션 모니터링)

## 2. 코드 및 로직 (Code Logic)

- [ ] **Input Validation Loop 적용**
  - [ ] `option_pause_node`에 입력값 유효성 검사 로직 추가 (필수 선택 등)
- [ ] **Error Handling 강화**
  - [ ] LLM API 타임아웃/RateLimit 발생 시 Backoff 재시도 로직 확인
  - [ ] 치명적 오류 발생 시 사용자에게 "죄송합니다" 메시지 및 관리자 알림(Sentry 등) 연동

## 3. 운영 및 모니터링 (Ops)

- [ ] **Logging Strategy**
  - [ ] 파일 로그 외에 ELK 스택 또는 CloudWatch 등으로 로그 전송 설정
- [ ] **Health Check**
  - [ ] `/health` 엔드포인트 생성 (Streamlit의 경우 별도 모니터링 포트 확인)

## 4. 확장성 (Scalability Test)

- [ ] **Load Testing**
  - [ ] locust 등을 사용하여 100+ 동시 세션 처리 시 Checkpointer 성능 확인
- [ ] **Recovery Testing**
  - [ ] 실행 도중 프로세스 강제 종료 후 재시작 시 상태 복구 여부 검증

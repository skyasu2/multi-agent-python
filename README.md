# 📋 PlanCraft Agent

> **AI 기반 웹/앱 서비스 기획서 자동 생성 Multi-Agent 시스템**

[![LangGraph](https://img.shields.io/badge/LangGraph-v0.5+-blue)](https://langchain-ai.github.io/langgraph/)
[![Python](https://img.shields.io/badge/Python-3.11+-green)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red)](https://streamlit.io/)
[![License](https://img.shields.io/badge/License-MIT-yellow)](./LICENSE)

---

## 🎯 핵심 기능

### 1. **6개 전문 AI Agent 협업**
```
Analyzer → Structurer → Writer → Reviewer → Refiner → Formatter
```

| Agent | 역할 |
|-------|------|
| **Analyzer** | 요구사항 분석 + HITL 트리거 |
| **Structurer** | 기획서 목차/구조 설계 |
| **Writer** | 섹션별 상세 콘텐츠 작성 |
| **Reviewer** | 품질 평가 및 라우팅 결정 |
| **Refiner** | 개선 전략 수립 |
| **Formatter** | 최종 마크다운 포맷팅 |

### 2. **Human-in-the-Loop (HITL)**
- 🔄 짧은 요청 시 AI가 컨셉을 제안하고 사용자 확인
- 📝 제안된 주제/목적/기능 미리보기 후 진행
- 💬 채팅으로 추가 요구사항 전달 가능

### 3. **AI 브레인스토밍 (New)**
- 🎲 **8개 카테고리**: IT/금융/F&B/헬스케어/교육/라이프스타일/제조/랜덤
- 🔢 **LLM 호출 제한**: 세션당 10회 초과 시 Static Pool 사용
- 📅 **시간 인식**: 현재 연도/분기 기반 아이디어 제안

### 4. **동적 라우팅 (RunnableBranch)**
```python
# Reviewer 평가 기반 자동 분기
< 5점 (FAIL)   → Analyzer 복귀 (최대 2회)
5~8점 (REVISE) → Refiner 실행 (최대 3회)
≥ 9점 (PASS)   → Formatter 완료
```

### 5. **RAG + 웹 검색 병렬 처리**
| 소스 | 역할 |
|------|------|
| RAG (FAISS) | 불변 정보 (작성 가이드, 체크리스트) |
| 웹 검색 (Tavily) | 실시간 정보 (시장 규모, 트렌드) |

### 6. **운영 안정성**
- ✅ Interrupt-First 설계 (Side-effect 없는 일시 중단)
- ✅ 무한 루프 방지 (3중 안전장치)
- ✅ 체크포인터 (Memory/PostgreSQL/Redis)
- ✅ `ensure_dict()` 유틸리티로 Pydantic/Dict 일관성 보장

---

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone https://github.com/skyasu2/skax.git
cd skax

# 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경변수 설정

```bash
cp .env.example .env
# .env 파일 편집 (API 키 입력)
```

**필수 환경변수:**
```env
# Azure OpenAI
AOAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AOAI_API_KEY=your_api_key
AOAI_DEPLOY_GPT4O=gpt-4o
AOAI_DEPLOY_GPT4O_MINI=gpt-4o-mini
AOAI_DEPLOY_EMBED_3_LARGE=text-embedding-3-large

# (선택) 웹 검색
TAVILY_API_KEY=your_tavily_key

# (선택) LangSmith 트레이싱
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_key
```

### 3. 실행

```bash
streamlit run app.py
```

브라우저에서 `http://localhost:8501` 접속

---

## 🐳 Docker 배포

```bash
# Docker Compose (권장)
docker-compose up -d

# 또는 직접 실행
docker build -t plancraft-agent .
docker run -d -p 8501:8501 --env-file .env plancraft-agent
```

---

## 🏗️ 시스템 아키텍처

```
User Input
    ↓
[RAG + Web Search] ─── 병렬 컨텍스트 수집
    ↓
Analyzer ─── HITL (짧은 입력 시 옵션 제시)
    ↓
Structurer ─── 목차 설계
    ↓
Writer ─── Self-Check (섹션 9개 이상 검증)
    ↓
Reviewer ─── 품질 게이트
    ├─ PASS (≥9점) → Formatter → 완료
    ├─ REVISE (5-8점) → Refiner → Writer (최대 3회)
    └─ FAIL (<5점) → Analyzer (최대 2회)
```

---

## 📁 프로젝트 구조

```
plancraft-agent/
├── app.py                  # Streamlit 메인
├── agents/                 # 6개 전문 Agent
├── graph/                  # LangGraph 워크플로우
│   ├── workflow.py         # 메인 그래프 + RunnableBranch
│   ├── state.py            # TypedDict 상태 + ensure_dict
│   └── interrupt_utils.py  # HITL 유틸리티
├── prompts/                # 에이전트 프롬프트
├── rag/                    # RAG (FAISS + MMR)
│   └── documents/          # 불변 가이드 문서 3개
├── ui/                     # Streamlit 컴포넌트
│   ├── styles.py           # CSS Design Tokens
│   └── components.py       # 진행률 바 등
├── utils/
│   ├── idea_generator.py   # AI 브레인스토밍
│   ├── prompt_examples.py  # 8개 카테고리 예제
│   └── time_context.py     # 연도/분기 인식
├── tests/                  # pytest 테스트
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 🧪 테스트

```bash
# 전체 테스트
pytest tests/ -v

# CI 환경
PYTHONPATH=$(pwd) pytest tests/test_scenarios.py -v
```

---

## 📚 주요 기술 스택

| 영역 | 기술 |
|------|------|
| **Agent Framework** | LangGraph (StateGraph, RunnableBranch) |
| **LLM** | Azure OpenAI (GPT-4o, GPT-4o-mini) |
| **RAG** | FAISS + MMR Search |
| **UI** | Streamlit + CSS Design Tokens |
| **Structured Output** | Pydantic + with_structured_output |
| **상태 관리** | TypedDict + ensure_dict 패턴 |

---

## 📝 라이선스

MIT License

---

**Made with ❤️ using LangGraph + Streamlit**

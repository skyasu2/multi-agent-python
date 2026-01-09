# PlanCraft Agent

Multi-Agent 시스템 기반 서비스 기획서 생성 도구

[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.5+-8957e5?style=flat-square)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-ff4b4b?style=flat-square)](https://streamlit.io/)

## Overview

사용자가 서비스 아이디어를 입력하면 10개의 AI 에이전트가 협업하여 기획서를 생성합니다.

**주요 구성**:
- **LangGraph StateGraph**: 워크플로우 오케스트레이션
- **Plan-and-Execute 패턴**: Supervisor가 Specialist 에이전트들을 조율
- **Human-in-the-Loop**: `interrupt()` 기반 사용자 개입
- **RAG + Web Search**: 내부 문서 검색 + 실시간 웹 검색

## Architecture

```
User Input → Analyzer → Structurer → Supervisor → Specialists (병렬)
                                                      ↓
                        Formatter ← Reviewer ← Writer
                            ↓           ↓
                         Output    Refiner (품질 미달 시)
```

### Agents

| Agent | 역할 |
|-------|------|
| Analyzer | 사용자 입력 분석, 요구사항 추출 |
| Structurer | 기획서 목차 설계 |
| Supervisor | Specialist 작업 계획 및 실행 |
| Market Agent | 시장 분석 (TAM/SAM/SOM) |
| BM Agent | 비즈니스 모델 설계 |
| Risk Agent | 리스크 분석, SWOT |
| Tech Agent | 기술 스택 설계 |
| Writer | 섹션별 콘텐츠 작성 |
| Reviewer | 품질 평가 (1-10점) |
| Refiner | 피드백 기반 개선 |

## Quick Start

### 1. 설치

```bash
git clone <repository-url>
cd plancraft-agent

python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### 2. 환경변수

```bash
cp .env.example .env
```

`.env` 파일 편집:
```bash
# 필수
AOAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AOAI_API_KEY=your_api_key

# 선택
TAVILY_API_KEY=your_tavily_key      # 웹 검색
LANGCHAIN_TRACING_V2=true           # LangSmith 트레이싱
LANGCHAIN_API_KEY=your_key
```

### 3. 실행

```bash
streamlit run app.py
```

http://localhost:8501 접속

## Features

### Quality Presets

| Mode | Model | 특징 |
|------|-------|------|
| Fast | GPT-4o-mini | 빠른 초안 생성 |
| Balanced | GPT-4o | 기본값, Writer ReAct 활성화 |
| Quality | GPT-4o | 심층 분석, 최대 3회 개선 루프 |

### Human-in-the-Loop

- 모호한 입력 감지 시 옵션 제시
- 사용자 선택이 모든 에이전트에 전파
- LangGraph `interrupt()` 패턴 사용

### RAG + Web Search

- **RAG**: FAISS 기반 내부 문서 검색
- **Web**: Tavily API를 통한 실시간 검색
- Writer가 ReAct 패턴으로 필요시 도구 호출

## Project Structure

```
├── app.py                 # Streamlit 진입점
├── api/                   # FastAPI 백엔드
│   ├── main.py
│   └── routers/
├── agents/                # AI 에이전트
│   ├── analyzer.py
│   ├── structurer.py
│   ├── supervisor.py
│   ├── writer.py
│   ├── reviewer.py
│   └── specialists/
├── graph/                 # LangGraph 워크플로우
│   ├── workflow.py
│   ├── state.py
│   └── nodes/
├── rag/                   # FAISS 벡터스토어
├── tools/                 # 웹 검색 도구
├── prompts/               # LLM 프롬프트
├── ui/                    # Streamlit 컴포넌트
└── tests/                 # pytest 테스트
```

## Tech Stack

- **Orchestration**: LangGraph, LangChain
- **LLM**: Azure OpenAI (GPT-4o, GPT-4o-mini)
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **Vector DB**: FAISS
- **Search**: Tavily API
- **Testing**: pytest (318+ tests)

## Documentation

- [SYSTEM_DESIGN.md](docs/SYSTEM_DESIGN.md) - 시스템 설계
- [MULTI_AGENT_DIAGRAM.md](docs/MULTI_AGENT_DIAGRAM.md) - 에이전트 구성도
- [USER_MANUAL.md](docs/USER_MANUAL.md) - 사용자 가이드

## Testing

```bash
# 전체 테스트
python -m pytest tests/ -v

# 커버리지
python -m pytest tests/ --cov=. --cov-report=html
```

## License

MIT

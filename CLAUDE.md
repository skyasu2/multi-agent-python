# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PlanCraft Agent는 LangGraph, Azure OpenAI, Streamlit 기반의 AI 멀티 에이전트 사업계획서 자동 생성 시스템입니다. 6개의 전문 에이전트가 협력하여 고품질 사업계획서를 생성하며, Human-in-the-Loop (HITL) 상호작용을 지원합니다.

## Commands

### 실행
```bash
# 개발 모드
streamlit run app.py

# Docker
docker-compose up -d
```

### 테스트
```bash
# 전체 테스트
pytest tests/ -v

# 특정 테스트
pytest tests/test_scenarios.py -v

# CI 환경 (PYTHONPATH 설정 필요)
PYTHONPATH=$(pwd) pytest tests/ -v
```

### 의존성
```bash
pip install -r requirements.txt
```

## Architecture

### Agent Pipeline
```
User Input → [RAG + Web Search (병렬)] → Analyzer → Structurer → Writer → Reviewer → Refiner → Formatter → Output
```

### 핵심 컴포넌트

| 컴포넌트 | 위치 | 역할 |
|---------|------|------|
| State 관리 | `graph/state.py` | TypedDict 기반 상태 스키마 (PlanCraftState) |
| 워크플로우 | `graph/workflow.py` | LangGraph StateGraph 오케스트레이션 |
| 에이전트 | `agents/*.py` | 6개 전문 에이전트 (Analyzer, Structurer, Writer, Reviewer, Refiner, Formatter) |
| LLM 설정 | `utils/llm.py` | Azure OpenAI 클라이언트 팩토리 |
| 설정 | `utils/settings.py` | 중앙집중식 프로젝트 설정 |
| RAG | `rag/*.py` | FAISS 벡터 기반 문서 검색 |
| 에러 처리 | `utils/error_handler.py` | 5가지 카테고리 예외 처리 |

### Reviewer 라우팅 로직
- `< 5점 (FAIL)`: Analyzer로 복귀 (최대 2회)
- `5-8점 (REVISE)`: Refiner로 라우팅 (최대 3회 루프)
- `≥ 9점 (PASS)`: Formatter로 완료

### HITL (Human-in-the-Loop)
- Analyzer에서 짧은 입력 감지 시 interrupt 발생
- 사용자가 topic, purpose, features 옵션 확인 후 진행

## Key Patterns

### State 업데이트 (불변성 유지)
```python
from graph.state import update_state, safe_get

new_state = update_state(state, current_step="analyze", analysis=result)
topic = safe_get(analysis, "topic", "Unknown")
```

### 에이전트 구현 패턴
```python
from graph.state import PlanCraftState, update_state

def run(state: PlanCraftState) -> PlanCraftState:
    user_input = state.get("user_input", "")
    result = llm.invoke(...)
    return update_state(state, current_step="name", output=result)
```

### 에러 핸들링 데코레이터
```python
from utils.error_handler import handle_node_error

@handle_node_error
def node_function(state: PlanCraftState) -> PlanCraftState:
    pass
```

## Configuration

### 필수 환경변수 (.env)
```env
AOAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AOAI_API_KEY=your_api_key
AOAI_DEPLOY_GPT4O=gpt-4o
AOAI_DEPLOY_GPT4O_MINI=gpt-4o-mini
AOAI_DEPLOY_EMBED_3_LARGE=text-embedding-3-large
```

### 선택 환경변수
```env
TAVILY_API_KEY=...           # 웹 검색
LANGCHAIN_TRACING_V2=true    # LangSmith 추적
CHECKPOINTER_TYPE=memory     # memory|postgres|redis
```

## File Modification Guide

| 작업 | 수정 파일 |
|-----|----------|
| 에이전트 로직 변경 | `agents/{agent_name}.py` |
| 프롬프트 수정 | `prompts/{agent_name}_prompt.py` |
| State 필드 추가 | `graph/state.py` |
| 라우팅 로직 변경 | `graph/workflow.py` (should_refine_or_restart) |
| UI 컴포넌트 추가 | `ui/components.py` |
| RAG 문서 추가 | `rag/documents/*.md` |

## Notes

- TypedDict 사용: Pydantic 대신 가벼운 TypedDict로 LangGraph 상태 관리
- 항상 `update_state()` 사용하여 새로운 state dict 생성 (불변성)
- 로깅: `get_file_logger()` 사용 (/logs/ 디렉토리에 저장)
- 모든 노드에 `@handle_node_error` 데코레이터 적용
- Writer: 최소 9개 섹션 검증, 마크다운 테이블 자동 수정, 최대 3회 재시도

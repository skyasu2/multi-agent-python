# End-to-End AI Agent 서비스 개발 과제 결과 보고서

## 1. 프로젝트 개요 (Overview)
- **프로젝트명**: PlanCraft Agent
- **한줄 소개**: AI 기반 웹/앱 서비스 기획서 자동 생성 Multi-Agent 시스템
- **개발 목적**: 기획 초기 단계의 막막함 해소 및 표준화된 기획 문서 자동화
- **핵심 가치**: 10년차 기획자 페르소나의 AI가 RAG(불변 가이드)와 Web(실시간 트렌드)를 결합하여 실전 수준의 문서 제공

### 서비스 핵심 흐름
| 입력 유형 | 처리 방식 |
|----------|----------|
| 간단한 질문 | AI 직접 답변 (기획서 생성 X) |
| 부실한 입력 | **프롬프트 증폭기** - AI가 유사 컨셉 확장 제안 |
| 기획 요청 | 6개 Agent 협업 → 1차 기획안 → 사용자 수정 (최대 3회) |
| 브레인스토밍 | 아이디어 없을 때 사용하는 **보조 기능** |

---

## 2. 아키텍처 및 기술적 구현 (Technical Implementation)

### 2.1 Agent 구조 설계 (LangGraph 기반 Multi-Agent)
**6개의 전문 Agent**가 책임 분리 원칙(SRP)에 따라 협업:

| Agent | 역할 | Temperature |
|-------|------|-------------|
| **Analyzer** | 요구사항 분석 + HITL 트리거 | 0.3 |
| **Structurer** | 기획서 목차/구조 설계 | 0.2~0.6 (동적) |
| **Writer** | 섹션별 상세 콘텐츠 작성 | 0.7 |
| **Reviewer** | 품질 평가 및 라우팅 결정 | 0.1 |
| **Refiner** | 개선 전략 수립 | 0.4 |
| **Formatter** | 최종 마크다운 포맷팅 | - |

### 2.2 RAG (Retrieval-Augmented Generation) 구현
- **Vector DB**: FAISS (로컬 임베딩)
- **검색 전략**: MMR (Maximal Marginal Relevance) - 유사도 + 다양성 균형
- **역할 분리**:
  - RAG: 불변 정보 (작성 가이드, 체크리스트, 예시)
  - 웹 검색: 실시간 정보 (시장 규모, 트렌드, 경쟁사)

### 2.3 고급 기술 요소 (Advanced Features)
- **RunnableBranch 패턴**: Reviewer 평가 기반 동적 라우팅
  ```python
  _is_max_restart_reached(state)  # 최대 복귀 횟수
  _is_quality_fail(state)          # score < 5 또는 FAIL
  _is_quality_pass(state)          # score >= 9 및 PASS
  ```
- **ensure_dict 유틸리티**: Pydantic/Dict 일관성 보장
- **Structured Output**: `with_structured_output` 사용
- **프롬프트 증폭기 (HITL)**: 부실한 입력 시 AI가 컨셉 확장 제안, LangGraph `interrupt()` 활용
- **병렬 컨텍스트 수집**: RAG + 웹 검색 동시 실행

---

## 3. 과제 요구사항 충족 여부 (Compliance Matrix)

| 구분 | 필수 요건 | 구현 내용 | 충족 |
|------|-----------|----------|------|
| **Prompt** | 역할 기반 설계 | `prompts/` 6개 전용 프롬프트 + CoT | ✅ |
| **Agent** | Multi-Agent | 6개 Agent 협업 구조 (`graph/workflow.py`) | ✅ |
| **Agent** | Memory 활용 | LangGraph Checkpointer + Thread-ID | ✅ |
| **Agent** | Tool Calling | `with_structured_output()` Function Calling | ✅ |
| **Agent** | ReAct 기반 | `should_search_web` LLM 판단 후 실행 | ✅ |
| **RAG** | Vector DB | FAISS + MMR 검색 (`rag/`) | ✅ |
| **Service** | UI 패키징 | Streamlit + CSS Design Tokens | ✅ |
| **Advanced** | Structured Output | Pydantic + ensure_dict 패턴 | ✅ |
| **Advanced** | A2A 협업 | Reviewer→Refiner→Writer 순환 구조 | ✅ |
| **Advanced** | 동적 라우팅 | RunnableBranch 조건 분기 | ✅ |

---

## 4. 서비스 워크플로우 (End-to-End)

```
User Input
    ↓
[간단한 질문?] ─YES→ AI 직접 답변 (기획서 생성 X)
    │NO
    ↓
[입력이 부실?] ─YES→ 프롬프트 증폭기 (AI가 컨셉 확장 제안)
    │NO
    ↓
[RAG + Web Search] ─── 병렬 컨텍스트 수집
    ↓
Analyzer → Structurer → Writer
    ↓
Reviewer ─── 내부 품질 게이트 (자동)
    ├─ PASS (≥9점) → Formatter → 1차 기획안 완성
    ├─ REVISE (5-8점) → Refiner → Writer (최대 3회)
    └─ FAIL (<5점) → Analyzer 복귀 (최대 2회)
    ↓
1차 기획안 완성
    ↓
[사용자 추가 수정 요청] → 최대 3회 개선 가능
```

**핵심 포인트**:
- Reviewer 품질 게이트: **내부 자동 루프** (사용자 개입 없음)
- 사용자 수정 3회: 1차 완성 **후** 사용자가 피드백 전달 가능

---

## 5. 주요 기술 스택

| 영역 | 기술 |
|------|------|
| Agent Framework | LangGraph (StateGraph, RunnableBranch) |
| LLM | Azure OpenAI (GPT-4o, GPT-4o-mini) |
| RAG | FAISS + MMR Search |
| UI | Streamlit + CSS Design Tokens |
| Structured Output | Pydantic + with_structured_output |
| 상태 관리 | TypedDict + ensure_dict 패턴 |
| CI/CD | GitHub Actions + LangSmith Tracing |

---

## 6. 결론 및 기대효과

본 서비스는 단순한 LLM 래퍼가 아니라, **실제 업무 프로세스(분석-작성-검토-수정)**를 모방한 Agentic Workflow를 구현했습니다.

### 핵심 성과
- **6개 전문 Agent** 협업으로 품질 보장
- **RunnableBranch** 기반 동적 라우팅으로 확장성 확보
- **RAG vs 웹검색 역할 분리**로 정확성 향상
- **HITL 통합**으로 사용자 의도 반영
- **3중 안전장치**로 무한 루프 방지

LangGraph의 주도적인 제어 흐름과 Streamlit의 편리한 UI를 결합하여, 실무에서도 즉시 활용 가능한 수준의 완성도를 확보했습니다.

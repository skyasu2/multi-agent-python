# PlanCraft Agent: Frontend & UX Strategy

이 문서는 LangGraph 기반 시스템의 "이상적이고 실전적인 프론트엔드" 설계를 위한 개선 전략과 Best Practice를 정의합니다.

## 1. 개요 및 목표
**Core Goal**: 백엔드(LangGraph)의 상태(State)와 이벤트(Event) 흐름을 프론트엔드 UX와 "1:1로 동기화"하여, 투명하고 제어 가능한 AI 에이전트 시스템을 구축한다.

### 현재 Backend 강점
- SRP 기반 모듈화 및 불변 상태(Immutable State) 관리
- Pydantic/TypedDict를 통한 엄격한 타입 및 Validation
- Checkpoint, Fallback, Interrupt 등 LangGraph 고급 기능 내장

### Frontend 개선 필요 사항
- 상태 분기, 에러, Interrupt 상황의 UI 동기화 부족
- Checkpoint 기반의 Time-travel(History) 및 Rollback UX 미흡
- 동적 스키마 변경에 대응하는 Form 자동화 부족

---

## 2. Best Practice 기반 개선 전략

### [A] 상태(State) · 이벤트(Event) ↔ UI 연동 ("1:1 Sync")
LangGraph의 Step별 실행 결과와 상태 변화를 시각적으로 매핑한다.
- **Timeline View**: 각 Step의 실행 결과, 소요 시간, 상태 변화(Diff)를 타임라인으로 표현.
- **Real-time Stream**: WebSocket 또는 SSE를 통해 Step 이벤트를 실시간으로 수신하여 UI 갱신.
- **Checkpoint Browser**: 저장된 체크포인트를 탐색하고 특정 시점으로 되돌리는(Rewind) 기능.

### [B] State-Driven Dynamic Form (Schema-UI Sync)
백엔드의 `InputState` / `OutputState` 스키마(Pydantic)를 기반으로 UI 폼을 자동 생성한다.
- 스키마 변경 시 UI 코드 수정 없이 폼 레이아웃 자동 반영 (예: `react-jsonschema-form` 활용).
- Validation 로직을 프론트엔드와 백엔드가 공유(또는 동기화)하여 에러 최소화.

### [C] Human-in-the-loop UX (Interrupt & Resume)
LangGraph의 `interrupt` 신호를 즉각적인 UI 상호작용으로 변환한다.
- **Interrupt Modal**: AI가 사용자 개입을 요청할 때(예: 모호한 지시, 승인 필요) 자동으로 팝업 출력.
- **Structured Feedback**: 단순 텍스트 입력이 아닌, 선택지나 정형화된 폼을 통해 피드백 수집 후 `Command(resume=...)`로 전달.

### [D] Advanced Debugging Tools (Time-travel & Branching)
개발자 및 고급 사용자를 위한 강력한 디버깅 도구를 제공한다.
- **State History**: 전체 실행 히스토리를 시각화하고, 특정 노드에서의 상태 값 상세 조회.
- **Experimental Branching**: 과거 시점에서 새로운 파라미터로 분기(Fork)하여 실행 결과를 비교 실험.

### [E] Workflow Visualization (Graph View)
복잡한 에이전트 워크플로우를 시각화하여 현재 위치와 흐름을 직관적으로 보여준다.
- **Interactive Graph**: Mermaid.js 또는 Reactflow 등을 활용하여 그래프 구조 렌더링.
- **Active Node Highlighting**: 현재 실행 중인 노드, 에러가 발생한 노드 등을 색상으로 구분.

---

## 3. Implementation Roadmap (Streamlit & React)

### Phase 1: Foundation (Current)
- [x] Streamlit 기반 Chat Interface
- [x] Status Container를 통한 실시간 진행 상황 표시 (`StreamlitStatusCallback`)
- [x] 기본적인 Refinement(Human Feedback) Loop

### Phase 2: Enhanced Visibility (Next Step)
- [ ] **LangGraph Visualization**: `app.py` 내 Mermaid 그래프 연동.
- [ ] **State Inspector**: 현재 State의 상세 JSON 뷰어 제공 (Dev Tools).
- [ ] **Action History**: Agent의 Tool 사용 및 결정 내역을 타임라인 형태로 표시.

### Phase 3: Advanced Interaction
- [ ] **Dynamic Interrupt Handling**: 백엔드 Interrupt 신호 감지 및 UI 모달 연동.
- [ ] **Checkpoint Manager**: 과거 대화 시점으로 롤백 기능 구현.
- [ ] **Schema-driven Forms**: Pydantic 모델을 `st.form`으로 자동 변환하는 유틸리티 개발.

---
*Created based on expert feedback on 2025-12-28.*

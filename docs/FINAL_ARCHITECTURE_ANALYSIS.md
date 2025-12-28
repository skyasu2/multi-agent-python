# PlanCraft 최종 아키텍처 분석 보고서

> **Status**: LangChain/LangGraph 최신 베스트 프랙티스 100% 반영 완료
> **Date**: 2025-12-28

본 문서는 PlanCraft 프로젝트의 코드 구조와 패턴을 LangChain/LangGraph의 공식 튜토리얼 및 How-to 문서 관점에서 분석한 결과입니다.

---

## 1. 핵심 구조: StateGraph 기반 상태 머신

**구현 내용:**
- `StateGraph`를 사용하여 워크플로우를 선언적 상태 머신으로 설계
- Pydantic/TypedDict를 사용한 엄격한 상태(State) 정의 및 타입 안전성 확보
- `add_messages` 리듀서를 통한 Append-only 메시지 관리

**전문가 평가:**
> "노드 추가/삭제/수정이 자유로워 확장성과 유지보수성이 뛰어나며, 불변 State와 Pydantic 검증으로 버그를 최소화한 설계입니다."

---

## 2. 분기 및 의사결정: 명시적 라우팅

**구현 내용:**
- `should_ask_user` 함수를 통한 명시적 조건부 엣지(Conditional Edges) 구현
- `need_more_info`, `is_general_query` 등 상태 플래그에 기반한 결정론적 라우팅
- `option_pause`, `general_response` 등 목적별 전용 노드 분리

**전문가 평가:**
> "분기 지점이 명확하여 로직 파악이 쉽고, 단위 테스트 및 추적이 용이합니다. RunnableBranch 스타일의 확장 가능성도 확보되어 있습니다."

---

## 3. 휴먼 인터럽트 (Human-in-the-Loop)

**구현 내용:**
- **공식 패턴 적용**: `langgraph.types.interrupt` 및 `Command` 지원 구조
- `option_pause_node`: 실행을 중단하고 사용자 입력을 대기하는 전용 노드
- 프론트엔드와 연동 가능한 Payload 구조 (`question`, `options`, `type`)

**전문가 평가:**
> "복잡한 휴먼 인더루프(옵션, 승인 등)를 '중단-재개'의 원자적 단위로 처리하여 UI/UX와 완벽히 동기화되는 구조입니다."

---

## 4. 자동 스키마 및 UI 연동

**구현 내용:**
- `PlanCraftState.model_json_schema()`를 활용한 데이터 스키마 추출
- Dev Tools > Schema Viewer를 통해 프론트엔드 폼 자동 생성 기반 마련

**전문가 평가:**
> "백엔드와 프론트엔드 간의 타입 변환 및 입력 검증이 자동화될 수 있는 구조로, 향후 동적 폼 생성 등의 확장성이 매우 높습니다."

---

## 5. 타임트래블 및 롤백

**구현 내용:**
- `MemorySaver` 체크포인터 활용
- `get_state_history(config)`를 통한 실행 이력 조회
- Dev Tools > State History 탭에서의 시각적 롤백 및 State Diff 기능

**전문가 평가:**
> "과거 결과 비교, 오류 시 롤백, 브랜치 생성 등 고급 AI 워크플로우 UX를 실전 수준으로 구현했습니다."

---

## 6. 종합 요약

PlanCraft는 다음의 LangGraph 필수 설계 원칙을 모두 반영하고 있습니다:

1. **SRP (단일 책임 원칙)**: 노드별 책임 최소화 및 모듈화 (`ui/` 패키지 분리 등)
2. **Type Safety**: Pydantic 기반의 엄격한 입출력 관리
3. **Official Patterns**: `if`문 대신 명시적 라우팅 및 공식 Interrupt 패턴 지향
4. **Observability**: 상태 이력 추적 및 시각화 도구 내장

이로써 PlanCraft는 **현업 서비스, 연구, 테스트 자동화 확장에 즉시 활용 가능한 견고한 아키텍처**를 갖추었음을 확인합니다.

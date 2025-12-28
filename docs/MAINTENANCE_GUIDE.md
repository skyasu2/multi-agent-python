# PlanCraft 실전 고도화 및 유지보수 가이드

본 문서는 LangChain/LangGraph 공식 패턴에 기반한 **프로젝트 고도화 및 유지보수 전략**을 기술합니다.

---

## 1. 실전 How-to 아키텍처 매핑

### (1) LangChain Structured Output (100% 적용됨)
- **패턴**: `.with_structured_output(PydanticModel)`
- **효과**: 자동 파싱 및 검증, 타입 안정성 확보
- **팁**: 복잡한 경우 `Union` 타입이나 다중 스키마 활용 가능

### (2) 분기/휴먼 인터럽트 공식 패턴 (확장 준비됨)
- **RunnableBranch**: 복잡한 조건부 분기를 직관적으로 추상화
- **Interrupt/Command**: `langgraph.types.interrupt`를 사용한 공식 휴먼 인터럽트
- **코드 위치**: `graph/workflow.py` 내 `create_routing_branch` 및 `graph/interrupt_utils.py`

### (3) 타임트래블, 롤백, 서브그래프 (구현됨)
- **MemorySaver**: 메모리 체크포인팅
- **get_state_history**: 실행 이력 조회 및 롤백 (Dev Tools에서 활용 중)
- **UI 연동**: State Diff 및 롤백 기능이 프론트엔드(`ui/dialogs.py`)에 구현됨

### (4) 입출력 스키마 → 자동 폼 (활용 가능)
- **JSON Schema**: `PlanCraftState.model_json_schema()` 활용
- **자동화**: `react-jsonschema-form` 등과 연동하여 UI 폼 자동 생성 가능

---

## 2. 실전 고도화 제안 (Action Items)

### a. RunnableBranch 기반 분기 고도화
분기 조건이 복잡해질 경우 `if/else` 대신 `RunnableBranch`를 활용하세요.

```python
from langchain_core.runnables import RunnableBranch

# 예시: 분기 체인 정의
main_flow = RunnableBranch(
    (lambda x: x.need_more_info, option_pause_node),
    (lambda x: x.analysis.is_general_query, general_answer_node),
    main_workflow_node
)
```

### b. 휴먼 인터럽트 패턴 100% 통합
조건부 옵션 외에도 설문, 파일 업로드 등 다양한 인터럽트에 공식 패턴을 적용하세요.

```python
from langgraph.types import interrupt

def option_pause_node(state):
    # 실행 중단 및 응답 대기
    resp = interrupt({"question": state.option_question, "options": state.options})
    # 이후 Command(resume=...)로 전달된 값 처리
    return handle_user_response(state, resp)
```

### c. Input/Output Schema 활용
- Pydantic 모델을 JSON Schema로 변환하여 프론트엔드 폼 생성에 활용
- 테스트 케이스 자동 생성 및 커버리지 분석에 활용

### d. 타임트래블 및 분석 UI
- `get_state_history`를 활용한 심화 분석 도구 개발 (A/B 테스팅, 경로 분석)
- 이미 구현된 "Dev Tools > State History" 탭을 기반으로 확장

### e. 마이크로서비스화 (MSA)
- 독립적인 Subgraph(Context, Generation, QA)들을 별도 서비스로 배포 가능
- CI/CD 파이프라인에서 각 Subgraph 독립 테스트 수행 권장

---

## 3. 참고 코드
- `graph/workflow.py`: `create_routing_branch`, `option_pause_node` 참조
- `graph/interrupt_utils.py`: 인터럽트 데이터 핸들링 유틸리티
- `ui/dialogs.py`: Schema Viewer 및 History 관리 UI 구현체

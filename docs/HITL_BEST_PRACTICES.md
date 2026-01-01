# PlanCraft Human-in-the-Loop (HITL) 가이드

이 문서는 LangGraph 기반의 PlanCraft 애플리케이션에서 Human-in-the-Loop(HITL) 기능을 구현하고 운영할 때 준수해야 할 베스트 프랙티스와 시나리오별 처리 방식을 설명합니다.

## 1. HITL 핵심 원칙

### 1.1 Side-Effect 분리 (Separation of Side-Effects)
`interrupt()` 호출 전에는 외부 상태를 변경하거나 비용이 발생하는 작업(API 호출, DB 쓰기 등)을 최소화해야 합니다.
- **Why?**: 사용자가 입력을 제공하고 실행을 재개(Resume)할 때, 인터럽트가 발생한 노드(또는 직전 노드)부터 다시 실행될 수 있습니다. 이때 Side-Effect가 중복 실행되는 것을 방지해야 합니다.
- **Pattern**:
  ```python
  # (X) Bad: interrupt 전에 API 호출
  call_expensive_api()
  interrupt(...) 
  
  # (O) Good: interrupt 후 API 호출 또는 상태 체크로 멱등성 보장
  response = interrupt(...)
  call_expensive_api(response)
  ```

### 1.2 멱등성 (Idempotency) 보장
Resume 시나리오에서 노드가 다시 실행되더라도 결과가 동일하거나 안전해야 합니다.
- 특히 Subgraph 내에서 초기화 로직이 있다면, 이미 데이터가 존재하는지 확인해야 합니다.
- **Example (`graph/subgraphs.py`)**:
  ```python
  # Resume 시 기존 대화 이력 유지
  if not state.get("discussion_messages"):
      state = update_state(state, discussion_messages=[])
  ```

## 2. 주요 시나리오 및 처리 전략

### 2.1 단순 일시정지 및 승인 (Review & Approval)
- **흐름**: Agent 작업 완료 → Reviewer 평가 → (점수 미달 시) → **Interrupt (옵션 선택)** → 사용자 피드백 → Resume
- **구현**: `option_pause_node`를 사용하여 사용자에게 선택지를 제공하고, 선택에 따라 분기합니다.

### 2.2 추가 정보 요청 (Missing Info Injection)
- **흐름**: Analyzer 분석 중 정보 부족 → **Interrupt (Form 입력)** → 사용자 상세 정보 입력 → Resume → Analyze 재실행
- **전략**: `interrupt()`의 페이로드에 `input_schema_name`을 포함하여 UI가 적절한 폼을 렌더링하도록 유도합니다.

### 2.3 서브그래프 내 인터럽트 (Interrupt inside Subgraph)
- **주의사항**: 서브그래프 내부에서 `interrupt`가 발생하면, 부모 그래프는 해당 서브그래프 노드 상태에서 멈춥니다.
- **재개(Resume)**: 부모 그래프 레벨에서 `Command(resume=...)`를 전달하면, 서브그래프 내부의 멈춘 지점으로 정확히 전달됩니다.
- **상태 관리**: 서브그래프의 로컬 상태와 부모 그래프의 전역 상태 동기화에 주의해야 합니다. PlanCraft는 단일 `PlanCraftState`를 공유하므로 비교적 관리가 용이합니다.

## 3. UI/UX 가이드라인 (Streamlit)

### 3.1 인터럽트 감지
- LangGraph 실행 결과(`snapshot`)에서 `interrupts` 정보를 확인하여 UI를 전환합니다.
- `app.py`에서 `snapshot.tasks[0].interrupts`를 체크하고, `__interrupt__` 키로 프론트엔드에 전달합니다.

### 3.2 사용자 피드백 제출
- 사용자가 폼/버튼을 조작하면 `run_plancraft(..., resume_command={"resume": data})` 형태로 호출하여 워크플로우를 재개합니다.

## 4. 디버깅 및 테스트

- **Snapshot 시점**: 인터럽트 직전의 스냅샷을 검사하여 State가 의도한 대로 저장되었는지 확인합니다.
- **Time Travel**: 과거 스냅샷 ID로 되돌아가서 다른 분기를 선택해보는 테스트가 유용합니다.

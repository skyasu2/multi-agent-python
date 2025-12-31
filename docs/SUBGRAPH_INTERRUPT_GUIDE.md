# Subgraph Interrupt 동작 가이드

> LangGraph에서 Subgraph 내 interrupt() 발생 시 동작 원리 및 주의사항

## 핵심 개념

### Interrupt 재실행 규칙

LangGraph에서 `interrupt()`가 호출되면:

```
[Resume 시 재실행 범위]

┌─────────────────────────────────────┐
│           Main Graph                │
│  ┌────────────────────────────┐     │
│  │    Parent Node (전체 재실행) │ ◄── Resume 시 여기서부터 시작
│  │  ┌──────────────────────┐  │     │
│  │  │    Sub-graph         │  │     │
│  │  │  ┌────────────────┐  │  │     │
│  │  │  │ interrupt() ⚡  │  │  │     │
│  │  │  └────────────────┘  │  │     │
│  │  └──────────────────────┘  │     │
│  └────────────────────────────┘     │
└─────────────────────────────────────┘
```

**핵심 규칙**: Resume 시 interrupt가 발생한 노드의 **처음부터** 다시 실행됩니다.

## PlanCraft 적용 사례

### 1. option_pause_node (Interrupt 노드)

```python
def option_pause_node(state: PlanCraftState) -> Command:
    # ═══════════════════════════════════════════════════════════
    # [BEFORE INTERRUPT] 비효과적 코드만 (순수 함수)
    # ═══════════════════════════════════════════════════════════
    payload = create_option_interrupt(state)  # ✅ 순수 함수
    payload["type"] = "option_selector"       # ✅ 값 할당만

    # ═══════════════════════════════════════════════════════════
    # [INTERRUPT] 실행 중단
    # ═══════════════════════════════════════════════════════════
    user_response = interrupt(payload)  # ⚡ 여기서 중단

    # ═══════════════════════════════════════════════════════════
    # [AFTER INTERRUPT] Side-Effect 허용
    # ═══════════════════════════════════════════════════════════
    updated_state = handle_user_response(state, user_response)  # ✅ Resume 후 실행
    return Command(update=updated_state, goto="analyze")
```

### 2. Discussion SubGraph (중첩 구조)

```python
def run_discussion_subgraph(state: PlanCraftState) -> PlanCraftState:
    """
    ⚠️ 주의: 이 함수 내부에서 interrupt가 발생하면,
    Resume 시 run_discussion_subgraph 전체가 다시 실행됩니다.

    현재 Discussion SubGraph에는 interrupt가 없으므로 안전합니다.
    """
    # 대화 상태 초기화 (Resume 시 다시 실행될 수 있음)
    state = update_state(state, discussion_messages=[], ...)

    # 서브그래프 실행
    discussion_app = get_discussion_app()
    result = discussion_app.invoke(state)

    return result
```

## Side-Effect 배치 규칙

### 안전한 패턴 (권장)

```python
def my_node(state):
    # ═══════════════════════════════════════════════════
    # [BEFORE INTERRUPT] 순수 함수만
    # ═══════════════════════════════════════════════════
    payload = build_payload(state)  # ✅ 계산만

    # ═══════════════════════════════════════════════════
    # [INTERRUPT]
    # ═══════════════════════════════════════════════════
    response = interrupt(payload)

    # ═══════════════════════════════════════════════════
    # [AFTER INTERRUPT] Side-Effect OK
    # ═══════════════════════════════════════════════════
    save_to_database(response)      # ✅ Resume 후에만 실행
    call_external_api(response)     # ✅ 중복 실행 없음
    return update_state(state, ...)
```

### 위험한 패턴 (금지)

```python
def my_node(state):
    # ❌ DANGER: Resume 시 중복 실행됨!
    save_to_database(state)         # ❌ DB에 2번 저장
    result = call_external_api()    # ❌ API 2번 호출
    send_notification()             # ❌ 알림 2번 발송

    response = interrupt(payload)   # ⚡ 중단

    return update_state(state, ...)
```

## PlanCraft Side-Effect 분류

### 노드별 Side-Effect 현황

| 노드 | Side-Effect | interrupt 전 | 안전성 |
|------|-------------|-------------|--------|
| `option_pause_node` | X | 순수 함수만 | ✅ 안전 |
| `retrieve_context` | RAG 조회 | N/A | ✅ 멱등성 |
| `fetch_web_context` | 웹 API 호출 | N/A | ✅ 조회 전용 |
| `run_analyzer_node` | LLM 호출 | N/A | ✅ 멱등성 |
| `run_discussion_node` | SubGraph | interrupt 없음 | ✅ 안전 |

### 멱등성(Idempotency) 보장

모든 Agent 노드는 **멱등성**을 보장하도록 설계되었습니다:

```python
@handle_node_error
def run_analyzer_node(state: PlanCraftState) -> PlanCraftState:
    """
    Side-Effect: LLM 호출 (Azure OpenAI)
    - 멱등성: 동일 입력에 유사한 결과 (LLM 특성상 약간의 변동)
    - 재시도 안전: 상태 변경 없이 분석 결과만 반환
    """
    new_state = analyzer.run(state)
    return _update_step_history(new_state, "analyze", "SUCCESS", ...)
```

## SubGraph 내 Interrupt 발생 시 동작

### 시나리오: Discussion SubGraph에 interrupt 추가 시

```
Main Graph
    │
    ▼
┌─────────────────────────────────────┐
│ run_discussion_node (Parent)        │ ◄── Resume 시 여기서 재시작
│  │                                  │
│  ▼                                  │
│ ┌─────────────────────────────────┐ │
│ │ Discussion SubGraph             │ │
│ │  │                              │ │
│ │  ├─► reviewer_speak             │ │
│ │  │                              │ │
│ │  ├─► writer_respond             │ │
│ │  │      │                       │ │
│ │  │      └─► interrupt() ⚡      │ │ ◄── 중단 지점
│ │  │                              │ │
│ │  └─► check_consensus            │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**Resume 시**:
1. `run_discussion_node` 함수 처음부터 재실행
2. SubGraph 초기화 코드 재실행 (`discussion_messages=[]`)
3. `reviewer_speak` 재실행
4. `writer_respond` 재실행
5. `interrupt()` 지점에서 이전 응답 수신
6. 이후 정상 진행

### 권장 사항

SubGraph 내부에 interrupt를 추가하려면:

1. **초기화 코드 주의**: Resume 시 다시 실행되므로 부작용 없어야 함
2. **상태 복원 고려**: Checkpointer가 저장한 상태 활용
3. **문서화 필수**: 팀원에게 재실행 범위 명시

## 디버깅 팁

### 재실행 여부 확인 로그

```python
def my_interrupt_node(state):
    print(f"[DEBUG] Node entered at {datetime.now()}")  # Resume 시 2번 출력됨

    response = interrupt(payload)

    print(f"[DEBUG] After interrupt at {datetime.now()}")  # 1번만 출력됨
    return ...
```

### LangSmith 트레이싱

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=PlanCraft-Debug
```

LangSmith에서 노드 재실행 여부 시각적으로 확인 가능

## 참고 자료

- [LangGraph Human-in-the-loop Guide](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/)
- [LangGraph Interrupt Best Practices](https://langchain-ai.github.io/langgraph/concepts/low_level/#interrupt)
- [PlanCraft HITL 구현](../graph/interrupt_utils.py)

---

**Last Updated**: 2025-12-31

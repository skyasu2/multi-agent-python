"""
Writer Node
"""
from agents.writer import run
from graph.state import PlanCraftState
from graph.nodes.common import update_step_history
from utils.tracing import trace_node
from utils.error_handler import handle_node_error
from utils.decorators import require_state_keys

@trace_node("write", tags=["slow"])
@require_state_keys(["structure"])
@handle_node_error
def run_writer_node(state: PlanCraftState) -> PlanCraftState:
    """
    작성 Agent 실행 노드

    Side-Effect: LLM 호출 (Azure OpenAI)
    - 섹션별 상세 콘텐츠 작성 (가장 오래 걸리는 단계)
    - 재시도 안전: 콘텐츠만 생성, 외부 상태 변경 없음

    LangSmith: run_name="✍️ 콘텐츠 작성", tags=["agent", "llm", "generation", "slow"]
    """
    # [Event] 작성 시작 이벤트 로그
    import time
    from datetime import datetime
    
    start_time = time.time()
    
    # [FIX] 불변성 유지 - state 직접 수정 대신 update_state 사용
    from graph.state import update_state

    current_log = list(state.get("execution_log", []) or [])  # 복사본 생성
    current_log.append({
        "type": "writer_start",
        "timestamp": datetime.now().isoformat(),
        "message": "기획서 초안 작성을 시작합니다..."
    })

    # 불변성 유지: update_state로 새 상태 생성
    state_with_log = update_state(state, execution_log=current_log)

    new_state = run(state_with_log)
    draft = new_state.get("draft")
    draft_len = 0
    if draft:
        from graph.state import ensure_dict
        draft_dict = ensure_dict(draft)
        sections = draft_dict.get("sections", [])
        if sections:
            draft_len = sum(len(ensure_dict(s).get("content", "")) for s in sections)
    
    return update_step_history(
        new_state, "write", "SUCCESS", summary=f"초안 작성 완료 ({draft_len}자)", start_time=start_time
    )

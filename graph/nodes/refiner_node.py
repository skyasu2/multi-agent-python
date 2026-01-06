"""
Refiner Node
"""
from agents.refiner import run
from graph.state import PlanCraftState
from graph.nodes.common import update_step_history
from utils.tracing import trace_node
from utils.error_handler import handle_node_error

@trace_node("refine")
@handle_node_error
def run_refiner_node(state: PlanCraftState) -> PlanCraftState:
    """
    개선 Agent 실행 노드 (Strategy Planner)

    Side-Effect: LLM 호출 (Azure OpenAI)
    - Reviewer 피드백 기반 개선 전략 수립
    - 재시도 안전: 전략만 생성, 외부 상태 변경 없음

    LangSmith: run_name="✨ 개선 적용", tags=["agent", "llm", "refinement"]
    """
    import time
    start_time = time.time()
    
    new_state = run(state)
    refine_count = new_state.get("refine_count", 0)

    return update_step_history(
        new_state,
        "refine",
        "SUCCESS",
        summary=f"기획서 개선 완료 (Round {refine_count})",
        start_time=start_time
    )

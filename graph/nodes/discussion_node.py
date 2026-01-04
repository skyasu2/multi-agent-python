"""
Discussion Node
"""
from graph.subgraphs import run_discussion_subgraph
from graph.state import PlanCraftState
from graph.nodes.common import update_step_history
from utils.tracing import trace_node
from utils.error_handler import handle_node_error

@trace_node("discuss", tags=["subgraph", "collaboration"])
@handle_node_error
def run_discussion_node(state: PlanCraftState) -> PlanCraftState:
    """
    에이전트 간 대화 노드 (Reviewer ↔ Writer)

    Side-Effect: 다중 LLM 호출 (SubGraph 내부)
    - Reviewer가 피드백을 제시하고 Writer가 개선 계획을 설명
    - 최대 DISCUSSION_MAX_ROUNDS 라운드 진행
    - 재시도 안전: 대화 기록만 생성, 외부 상태 변경 없음

    LangSmith: run_name="💬 에이전트 토론", tags=["agent", "llm", "collaboration", "subgraph"]
    """
    new_state = run_discussion_subgraph(state)
    round_count = new_state.get("discussion_round", 0)
    consensus = new_state.get("consensus_reached", False)

    return update_step_history(
        new_state,
        "discussion",
        "SUCCESS",
        summary=f"에이전트 대화 {round_count}라운드, 합의: {'완료' if consensus else '미완료'}"
    )

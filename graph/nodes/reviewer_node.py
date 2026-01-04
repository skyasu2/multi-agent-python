"""
Reviewer Node
"""
from agents.reviewer import run
from graph.state import PlanCraftState
from graph.nodes.common import update_step_history
from utils.tracing import trace_node
from utils.error_handler import handle_node_error

@trace_node("review", tags=["evaluation"])
@handle_node_error
def run_reviewer_node(state: PlanCraftState) -> PlanCraftState:
    """
    검토 Agent 실행 노드

    Side-Effect: LLM 호출 (Azure OpenAI)
    - 품질 평가 및 verdict 결정 (PASS/REVISE/FAIL)
    - 재시도 안전: 평가 결과만 반환, 외부 상태 변경 없음

    LangSmith: run_name="🔎 품질 검토", tags=["agent", "llm", "evaluation"]
    """
    new_state = run(state)
    review = new_state.get("review")
    verdict = "N/A"
    score = 0
    if review:
        if isinstance(review, dict):
            verdict = review.get("verdict", "N/A")
            score = review.get("overall_score", 0)
        else:
            verdict = getattr(review, "verdict", "N/A")
            score = getattr(review, "overall_score", 0)

    return update_step_history(
        new_state, "review", "SUCCESS", summary=f"심사 결과: {verdict} ({score}점)"
    )

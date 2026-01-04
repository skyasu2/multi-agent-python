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
    new_state = run(state)
    draft = new_state.get("draft")
    draft_len = 0
    if draft:
        sections = draft.get("sections") if isinstance(draft, dict) else getattr(draft, "sections", [])
        if sections:
             # SectionContent 객체 or dict
             draft_len = sum(len(s.get("content", "") if isinstance(s, dict) else s.content) for s in sections)
    
    return update_step_history(
        new_state, "write", "SUCCESS", summary=f"초안 작성 완료 ({draft_len}자)"
    )

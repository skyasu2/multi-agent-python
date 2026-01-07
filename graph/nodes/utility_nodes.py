"""
Utility Nodes for PlanCraft
"""
from graph.state import PlanCraftState, update_state
from graph.nodes.common import update_step_history


# 인사 응답 템플릿
GREETING_RESPONSES = {
    "default": "안녕하세요! PlanCraft입니다. 🎯\n\n어떤 앱/서비스/사업을 기획해 드릴까요?\n예시: \"배달 앱\", \"독서 모임 플랫폼\", \"카페 창업\"",
    "help": "무엇을 도와드릴까요?\n\n저는 다음과 같은 기획서를 작성할 수 있어요:\n• 웹/앱 서비스 기획서\n• 사업 계획서\n• 플랫폼 구축 기획서\n\n아이디어를 말씀해주세요!",
    "thanks": "천만에요! 다른 기획이 필요하시면 언제든 말씀해주세요. 😊"
}


def general_response_node(state: PlanCraftState) -> PlanCraftState:
    """
    일반 질의 응답 노드

    [호출 경로]
    1. Router → greeting_response (intent=greeting): 인사/잡담
    2. Analyzer → general_response (is_general_query=True): Analyzer 판단 잡담

    analysis가 있으면 general_answer 사용, 없으면 기본 인사 응답.
    """
    user_input = state.get("user_input", "").lower()
    intent = state.get("intent")
    analysis = state.get("analysis")

    # 응답 결정 우선순위:
    # 1. analysis.general_answer (Analyzer가 생성한 응답)
    # 2. intent 기반 기본 응답 (Router 경로)
    answer = None

    # Analyzer 응답이 있으면 사용
    if analysis:
        if isinstance(analysis, dict):
            answer = analysis.get("general_answer")
        else:
            answer = getattr(analysis, "general_answer", None)

    # Analyzer 응답이 없으면 intent/키워드 기반 기본 응답
    if not answer:
        if "고마" in user_input or "감사" in user_input:
            answer = GREETING_RESPONSES["thanks"]
        elif "도움" in user_input or "help" in user_input or "뭘 할 수" in user_input:
            answer = GREETING_RESPONSES["help"]
        else:
            answer = GREETING_RESPONSES["default"]

    new_state = update_state(
        state,
        current_step="general_response",
        final_output=answer,
        # [FIX] greeting 경로에서 필요한 필드 설정
        need_more_info=False,
        options=[],
        option_question=None
    )

    return update_step_history(
        new_state,
        "general_response",
        "SUCCESS",
        summary=f"응답 완료 (intent={intent or 'analyzer'})"
    )

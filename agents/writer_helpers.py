"""
PlanCraft Agent - Writer Helper Functions (Facade)

This module re-exports helper functions extracted into `agents/helpers/`.
This ensures backward compatibility while the codebase is refactored into modular components.
"""
# Re-export modules
from agents.helpers.prompt_builder import (
    get_prompts_by_doc_type,
    build_review_context,
    build_refinement_context,
    build_visual_instruction,
    build_visual_feedback
)
from agents.helpers.executors import (
    execute_web_search,
    execute_specialist_agents  # [DEPRECATED] Supervisor 노드로 이동됨
)
from agents.helpers.validator import validate_draft


def get_specialist_context(state: dict, logger) -> str:
    """
    [NEW] Supervisor 노드에서 실행된 전문 에이전트 분석 결과를 가져옵니다.

    기존 execute_specialist_agents()는 Writer 내부에서 Supervisor를 직접 호출했지만,
    이제 workflow의 run_specialists 노드에서 미리 실행됩니다.
    이 함수는 state에서 결과를 추출하여 프롬프트용 컨텍스트 문자열로 변환합니다.

    Args:
        state: 워크플로우 상태 (specialist_analysis 필드 포함)
        logger: 로거 인스턴스

    Returns:
        str: 전문 에이전트 분석 결과 (integrated_context) 또는 빈 문자열
    """
    specialist_analysis = state.get("specialist_analysis")

    if not specialist_analysis:
        logger.info("[Writer] 전문 에이전트 분석 결과 없음 (Supervisor 노드 스킵됨)")
        return ""

    # integrated_context가 이미 있으면 사용
    if isinstance(specialist_analysis, dict):
        integrated_context = specialist_analysis.get("integrated_context", "")
        if integrated_context:
            logger.info("[Writer] ✓ 전문 에이전트 분석 결과 로드됨")
            return integrated_context

        # integrated_context가 없으면 _integrate_results 호출
        try:
            from agents.supervisor import NativeSupervisor
            supervisor = NativeSupervisor()
            integrated_context = supervisor._integrate_results(specialist_analysis)
            logger.info("[Writer] ✓ 전문 에이전트 분석 결과 통합됨")
            return integrated_context
        except Exception as e:
            logger.warning(f"[Writer] 분석 결과 통합 실패: {e}")
            return ""

    return ""

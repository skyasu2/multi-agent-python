"""
Supervisor Node - 전문 에이전트 오케스트레이션

전문 에이전트(Specialists)들의 작업을 조율하는 노드입니다.
structure 노드 후, write 노드 전에 실행됩니다.

[실행 조건]
- use_specialist_agents=True (기본값)
- refine_count == 0 (첫 작성 시에만)

[출력]
- specialist_analysis: 전문 에이전트 분석 결과 딕셔너리
"""
import time
from graph.state import PlanCraftState, update_state, ensure_dict
from graph.nodes.common import update_step_history
from utils.tracing import trace_node
from utils.error_handler import handle_node_error
from utils.file_logger import get_file_logger


@trace_node("run_specialists", tags=["supervisor", "specialists"])
@handle_node_error
def run_supervisor_node(state: PlanCraftState) -> PlanCraftState:
    """
    전문 에이전트(Supervisor) 오케스트레이션 노드

    Side-Effect: LLM 호출 (다중 Specialist 에이전트 병렬 실행)
    - Market, BM, Financial, Risk, Tech, Content 에이전트
    - 재시도 안전: 상태만 업데이트, 외부 변경 없음

    LangSmith: run_name="🤖 전문가 분석", tags=["supervisor", "specialists"]

    Returns:
        PlanCraftState: specialist_analysis 필드가 추가된 상태
    """
    logger = get_file_logger()
    start_time = time.time()

    refine_count = state.get("refine_count", 0)
    use_specialist_agents = state.get("use_specialist_agents", True)

    # 조건 체크: 개선 시에는 기존 결과 유지 (스킵)
    if refine_count > 0:
        logger.info("[Supervisor Node] 개선 모드 - 기존 분석 결과 유지")
        return update_step_history(
            state, "run_specialists", "SKIPPED",
            summary="개선 모드 (기존 결과 재사용)",
            start_time=start_time
        )

    # 조건 체크: Specialist 비활성화 시 스킵
    if not use_specialist_agents:
        logger.info("[Supervisor Node] 전문 에이전트 비활성화됨")
        return update_step_history(
            state, "run_specialists", "SKIPPED",
            summary="전문 에이전트 비활성화",
            start_time=start_time
        )

    # 입력 준비
    user_input = state.get("user_input", "")
    web_context = state.get("web_context", "")

    analysis_dict = state.get("analysis", {})
    if hasattr(analysis_dict, "model_dump"):
        analysis_dict = analysis_dict.model_dump()
    elif not isinstance(analysis_dict, dict):
        analysis_dict = {}

    target_market = analysis_dict.get("target_market", "일반 시장")
    target_users = analysis_dict.get("target_user", "일반 사용자")
    tech_stack = analysis_dict.get("tech_stack", "React Native + Node.js + PostgreSQL")
    user_constraints = analysis_dict.get("user_constraints", [])

    # 웹 컨텍스트를 검색 결과 형태로 변환
    web_search_list = []
    if web_context:
        for line in web_context.split("\n"):
            if line.strip():
                web_search_list.append({"title": "", "content": line[:500]})

    try:
        from agents.supervisor import NativeSupervisor

        logger.info("[Supervisor Node] 🤖 전문 에이전트 분석 시작...")

        supervisor = NativeSupervisor()
        specialist_results = supervisor.run(
            service_overview=user_input,
            target_market=target_market,
            target_users=target_users,
            tech_stack=tech_stack,
            development_scope="MVP 3개월",
            web_search_results=web_search_list,
            user_constraints=user_constraints,
            deep_analysis_mode=state.get("deep_analysis_mode", False)
        )

        # 실행된 에이전트 수 계산
        executed_agents = []
        for key in ["market_analysis", "business_model", "financial_plan", "risk_analysis", "tech_analysis", "content_strategy"]:
            if specialist_results.get(key):
                executed_agents.append(key.split("_")[0])

        agent_count = len(executed_agents)
        logger.info(f"[Supervisor Node] ✓ 전문 에이전트 분석 완료 ({agent_count}개 에이전트)")

        new_state = update_state(state, specialist_analysis=specialist_results)

        return update_step_history(
            new_state, "run_specialists", "SUCCESS",
            summary=f"전문가 {agent_count}명 분석 완료",
            start_time=start_time
        )

    except ImportError as e:
        logger.warning(f"[Supervisor Node] Supervisor 모듈 로드 실패: {e}")
        return update_step_history(
            state, "run_specialists", "SKIPPED",
            summary=f"모듈 로드 실패: {e}",
            start_time=start_time
        )
    except Exception as e:
        logger.error(f"[Supervisor Node] 전문 에이전트 분석 오류: {e}")
        return update_step_history(
            state, "run_specialists", "ERROR",
            summary=f"분석 오류: {str(e)[:50]}",
            start_time=start_time
        )

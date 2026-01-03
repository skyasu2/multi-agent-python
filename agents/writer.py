"""
PlanCraft Agent - Writer Agent
"""
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import get_llm
from utils.schemas import DraftResult
from utils.time_context import get_time_context, get_time_instruction
from graph.state import PlanCraftState, update_state, ensure_dict
from utils.settings import settings
from utils.file_logger import get_file_logger

# 헬퍼 함수 임포트 (Refactored)
from agents.writer_helpers import (
    get_prompts_by_doc_type,
    execute_web_search,
    execute_specialist_agents,
    build_visual_instruction,
    build_visual_feedback,
    build_review_context,
    build_refinement_context,
    validate_draft
)


def run(state: PlanCraftState) -> PlanCraftState:
    """
    초안 작성 에이전트 실행

    Args:
        state: 현재 워크플로우 상태 (structure 필수)

    Returns:
        PlanCraftState: draft 필드가 추가된 상태
    """
    logger = get_file_logger()

    # 1. 입력 검증
    user_input = state.get("user_input", "")
    structure = state.get("structure")
    if not structure:
        return update_state(state, error="구조화 데이터가 없습니다.")

    # 2. 설정 로드
    from utils.settings import get_preset
    active_preset = state.get("generation_preset", settings.active_preset)
    preset = get_preset(active_preset)
    refine_count = state.get("refine_count", 0)

    # 3. 컨텍스트 구성 (헬퍼 함수 위임)
    rag_context = state.get("rag_context", "")
    web_context = state.get("web_context", "")

    # 웹 검색 실행
    web_context = execute_web_search(user_input, rag_context, web_context, logger)

    # 전문 에이전트 분석
    specialist_context, state = execute_specialist_agents(
        state, user_input, web_context, refine_count, logger
    )

    # 4. 프롬프트 구성
    system_prompt, user_prompt_template = get_prompts_by_doc_type(state)
    visual_instruction = build_visual_instruction(preset, logger)

    # User Constraints 추출
    user_constraints_str = "없음"
    analysis_obj = state.get("analysis")
    if analysis_obj:
        u_constraints = analysis_obj.get("user_constraints", []) if isinstance(analysis_obj, dict) \
            else getattr(analysis_obj, "user_constraints", [])
        if u_constraints:
            user_constraints_str = "\n".join([f"- {c}" for c in u_constraints])

    # Web URLs 포맷팅
    web_urls = state.get("web_urls", [])
    web_urls_str = "\n".join([f"- {url}" for url in web_urls]) if web_urls else "없음"

    try:
        formatted_prompt = user_prompt_template.format(
            user_input=user_input,
            structure=str(structure),
            web_context=web_context if web_context else "없음",
            web_urls=web_urls_str,
            context=rag_context if rag_context else "없음",
            visual_instruction=visual_instruction,
            user_constraints=user_constraints_str
        )
        
        # [NEW] Quality 모드 전용 추가 지침 (양적 풍성함 강화)
        if preset.name == "quality":
            quality_instruction = """
\n=====================================================================
👑 **[Quality Mode] 최고 품질 작성 지침**
1. **핵심 기능(Key Features)**: 반드시 **6개 이상**의 핵심 기능을 상세히 기술하세요.
2. **섹션 분량**: 각 섹션은 최소 500자 이상, 깊이 있는 내용을 담으세요.
3. **참고 자료**: 인용된 모든 출처를 마지막에 '참고 자료' 섹션으로 정리하세요.
=====================================================================\n
"""
            formatted_prompt += quality_instruction

    except KeyError as e:
        return update_state(state, error=f"프롬프트 포맷 오류: {str(e)}")

    # 전문 에이전트 결과 주입
    if specialist_context:
        specialist_header = f"""
=====================================================================
🤖 전문 에이전트 분석 결과 (반드시 활용할 것!)
=====================================================================
{specialist_context}
=====================================================================
"""
        formatted_prompt = specialist_header + formatted_prompt

    # Refinement 컨텍스트 추가
    review_context = build_review_context(state, refine_count)
    refinement_context = build_refinement_context(refine_count, preset.min_sections)

    # Refinement Strategy
    strategy_msg = ""
    refinement_guideline = state.get("refinement_guideline")
    if refine_count > 0 and refinement_guideline:
        direction = refinement_guideline.get("overall_direction", "") if isinstance(refinement_guideline, dict) \
            else getattr(refinement_guideline, "overall_direction", "")
        guidelines = refinement_guideline.get("specific_guidelines", []) if isinstance(refinement_guideline, dict) \
            else getattr(refinement_guideline, "specific_guidelines", [])
        strategy_msg = f"🚀 방향: {direction}\n지침: {chr(10).join([f'- {g}' for g in guidelines])}\n"

    prepend_msg = strategy_msg + review_context + refinement_context
    formatted_prompt = prepend_msg + formatted_prompt + get_time_instruction()

    # 5. LLM 호출 (Self-Reflection Loop)
    messages = [
        {"role": "system", "content": get_time_context() + system_prompt},
        {"role": "user", "content": formatted_prompt}
    ]

    writer_llm = get_llm(
        model_type=preset.model_type,
        temperature=preset.temperature
    ).with_structured_output(DraftResult)

    max_retries = preset.writer_max_retries
    final_draft_dict = None
    last_draft_dict = None
    last_error = None

    for current_try in range(max_retries):
        try:
            logger.info(f"[Writer] 초안 작성 시도 ({current_try + 1}/{max_retries})...")
            draft_result = writer_llm.invoke(messages)
            draft_dict = ensure_dict(draft_result)
            last_draft_dict = draft_dict

            # Self-Reflection 검증 (헬퍼 함수 위임)
            validation_issues = validate_draft(
                draft_dict, preset, specialist_context, refine_count, logger
            )

            if validation_issues:
                logger.warning(f"[Writer] 검증 실패: {', '.join(validation_issues)}")

                # 시각적 요소 누락 시 구체적인 예시 피드백 추가
                visual_feedback = build_visual_feedback(validation_issues, preset)
                base_feedback = f"[검증 실패] {', '.join(validation_issues)}. 모든 섹션을 완전히 작성하세요."
                feedback = base_feedback + visual_feedback if visual_feedback else base_feedback

                messages.append({"role": "user", "content": feedback})
                last_error = f"검증 실패: {', '.join(validation_issues)}"
                continue

            # 통과
            final_draft_dict = draft_dict
            section_count = len(draft_dict.get("sections", []))
            logger.info(f"[Writer] ✅ Self-Check 통과 (섹션 {section_count}개)")
            break

        except Exception as e:
            logger.error(f"[Writer Error] {e}")
            last_error = str(e)

    # 6. 결과 반환
    if final_draft_dict:
        return update_state(state, draft=final_draft_dict, current_step="write")
    elif last_draft_dict:
        logger.warning("[Writer] ⚠️ 부분 결과 사용")
        return update_state(state, draft=last_draft_dict, current_step="write")
    else:
        return update_state(state, error=f"Writer 실패: {last_error}")


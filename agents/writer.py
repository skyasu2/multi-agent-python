"""
PlanCraft Agent - Writer Agent
"""
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import get_llm
from utils.schemas import DraftResult
from utils.time_context import get_time_context, get_time_instruction
from graph.state import PlanCraftState, update_state

# 프롬프트 임포트 (IT용 / 일반 사업용)
from prompts.writer_prompt import WRITER_SYSTEM_PROMPT, WRITER_USER_PROMPT
from prompts.business_plan_prompt import BUSINESS_PLAN_SYSTEM_PROMPT, BUSINESS_PLAN_USER_PROMPT

# LLM 초기화
writer_llm = get_llm().with_structured_output(DraftResult)


def _get_prompts_by_doc_type(state: PlanCraftState) -> tuple:
    """
    doc_type에 따라 적절한 프롬프트 반환
    - web_app_plan: IT/Tech 기획서 (기본값)
    - business_plan: 일반 사업 기획서
    """
    analysis = state.get("analysis")
    doc_type = "web_app_plan"  # 기본값
    
    if analysis:
        if isinstance(analysis, dict):
            doc_type = analysis.get("doc_type", "web_app_plan")
        else:
            doc_type = getattr(analysis, "doc_type", "web_app_plan")
    
    if doc_type == "business_plan":
        print(f"[Writer] 비IT 사업 기획서 모드로 작성합니다.")
        return BUSINESS_PLAN_SYSTEM_PROMPT, BUSINESS_PLAN_USER_PROMPT
    else:
        print(f"[Writer] IT/Tech 기획서 모드로 작성합니다.")
        return WRITER_SYSTEM_PROMPT, WRITER_USER_PROMPT


def run(state: PlanCraftState) -> PlanCraftState:
    """
    초안 작성 에이전트 실행
    """
    # 1. 입력 데이터 준비 (Dict Access)
    user_input = state.get("user_input", "")
    structure = state.get("structure")
    rag_context = state.get("rag_context", "")
    web_context = state.get("web_context", "")
    web_urls = state.get("web_urls", [])
    
    if not structure:
        return update_state(state, error="구조화 데이터가 없습니다.")
    
    # Refinement Context
    previous_plan_context = ""
    refine_count = state.get("refine_count", 0)
    previous_plan = state.get("previous_plan")
    
    if refine_count > 0 and previous_plan:
        previous_plan_context = f"\n<previous_version>\n{previous_plan}\n</previous_version>\n\n위 이전 버전을 참고하여 더 나은 내용으로 개선하세요.\n"

    # [NEW] doc_type에 따라 프롬프트 선택
    system_prompt, user_prompt_template = _get_prompts_by_doc_type(state)

    # =========================================================================
    # [NEW] 실시간 웹 검색 (수치 및 근거 보강)
    # =========================================================================
    try:
        from tools.web_search import should_search_web
        from tools.search_client import get_search_client
        
        # 1. 검색 여부 판단
        search_decision = should_search_web(user_input, rag_context)
        
        if search_decision.get("should_search") and search_decision.get("search_query"):
            query = search_decision["search_query"]
            print(f"[Writer] 실시간 웹 검색 수행: '{query}'")
            
            # 2. 검색 수행 (Tavily)
            search_client = get_search_client()
            search_result = search_client.search(query)
            
            # 3. Context 보강
            if "[Web Search Failed]" not in search_result:
                if not web_context:
                    web_context = ""
                web_context += f"\n\n[Writer Search Result]\nKeyword: {query}\n{search_result}"
                print("[Writer] 웹 데이터가 컨텍스트에 추가되었습니다.")
            else:
                 print(f"[Writer] 검색 실패 또는 스킵됨: {search_result}")

    except ImportError:
        print("[Writer] 검색 모듈 로드 실패 (tools.web_search or tools.search_client)")
    except Exception as e:
        print(f"[Writer] 웹 검색 중 오류 발생: {str(e)}")
    # =========================================================================


    # 2. 프롬프트 구성 (시간 컨텍스트 주입)
    structure_str = str(structure)
    
    # Web URLs 포맷팅
    web_urls_str = "없음"
    if web_urls:
        web_urls_str = "\n".join([f"- {url}" for url in web_urls])
        
    try:
        formatted_prompt = user_prompt_template.format(
            user_input=user_input,
            structure=structure_str,
            web_context=web_context if web_context else "없음",
            web_urls=web_urls_str,
            context=rag_context if rag_context else "없음"
        )
    except KeyError as e:
        print(f"[ERROR] Prompt Formatting Failed: {e}")
        return update_state(state, error=f"프롬프트 포맷 오류: {str(e)}")

    # 이전 버전 컨텍스트 추가
    if previous_plan_context:
        formatted_prompt = previous_plan_context + "\n" + formatted_prompt

    # 시간 지시 추가 (일정/로드맵 정확성)
    formatted_prompt += get_time_instruction()

    messages = [
        {"role": "system", "content": get_time_context() + system_prompt},
        {"role": "user", "content": formatted_prompt}
    ]

    
    # 3. LLM 호출
    try:
        draft_result = writer_llm.invoke(messages)
        
        # 4. 상태 업데이트
        if hasattr(draft_result, "model_dump"):
            draft_dict = draft_result.model_dump()
        else:
            draft_dict = draft_result
            
        return update_state(
            state,
            draft=draft_dict,
            current_step="write"
        )
        
    except Exception as e:
        print(f"[ERROR] Writer Failed: {e}")
        return update_state(state, error=str(e))

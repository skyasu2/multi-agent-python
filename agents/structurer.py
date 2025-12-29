"""
PlanCraft Agent - Structurer Agent
"""
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import get_llm
from utils.schemas import StructureResult
from utils.time_context import get_time_context
from graph.state import PlanCraftState, update_state
from prompts.structurer_prompt import STRUCTURER_SYSTEM_PROMPT, STRUCTURER_USER_PROMPT

# LLM 초기화
structurer_llm = get_llm().with_structured_output(StructureResult)

def run(state: PlanCraftState) -> PlanCraftState:
    """
    구조화 에이전트 실행
    """
    # 1. 입력 데이터 준비 (Dict Access)
    user_input = state.get("user_input", "")
    analysis = state.get("analysis")
    
    if not analysis:
        return update_state(state, error="분석 데이터가 없습니다.")
        
    rag_context = state.get("rag_context", "")
    web_context = state.get("web_context", "")
    context = f"{rag_context}\n{web_context}".strip()
    
    # Analysis 내용을 문자열로 변환
    analysis_str = str(analysis)
    
    # [NEW] 재설계 컨텍스트 확인 (Retry Logic)
    previous_structure = state.get("structure")
    feedback_msg = ""
    
    if previous_structure:
        # Pydantic 객체일 경우 dict 변환
        prev_str = str(previous_structure)
        print("[Structurer] 재설계 요청 감지 -> 개선된 목차 생성 시도")
        
        feedback_msg = f"""
        =====================================================================
        🚨 [RETRY CONTEXT] 사용자가 이전 목차 설계를 거절했습니다.
        이전 목차: 
        {prev_str}
        
        지시: 
        1. 위 이전 목차의 문제점(너무 단순함, 핵심 누락 등)을 스스로 진단하세요.
        2. 이전과는 **확실히 다른 구조** 또는 **훨씬 더 상세한 구조**를 제안하세요.
        3. 똑같은 결과를 내놓지 마세요.
        =====================================================================
        """

    # 2. 프롬프트 구성 (시간 컨텍스트 주입)
    user_msg_content = STRUCTURER_USER_PROMPT.format(
            analysis=analysis_str,
            context=context if context else "없음"
    )
    
    if feedback_msg:
        user_msg_content += feedback_msg

    messages = [
        {"role": "system", "content": get_time_context() + STRUCTURER_SYSTEM_PROMPT},
        {"role": "user", "content": user_msg_content}
    ]
    
    # 3. LLM 호출
    try:
        structure_result = structurer_llm.invoke(messages)
        
        # 4. 상태 업데이트
        if hasattr(structure_result, "model_dump"):
            structure_dict = structure_result.model_dump()
        else:
            structure_dict = structure_result
            
        return update_state(
            state,
            structure=structure_dict,
            current_step="structure"
        )
        
    except Exception as e:
        print(f"[ERROR] Structurer Failed: {e}")
        return update_state(state, error=str(e))

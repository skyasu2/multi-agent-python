"""
PlanCraft Agent - Structurer Agent
"""
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm import get_llm
from utils.schemas import StructureResult
from utils.time_context import get_time_context
from graph.state import PlanCraftState, update_state
from prompts.structurer_prompt import STRUCTURER_SYSTEM_PROMPT, STRUCTURER_USER_PROMPT

# LLM 초기화 (run 함수 내에서 동적으로 생성함)
# structurer_llm = get_llm().with_structured_output(StructureResult)

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
    
    # [Logic] LLM 초기화 (상황에 따른 Temperature 조절)
    # 기본은 정석적인(Conservative) 구조 설계를 위해 낮게 설정
    target_temp = 0.2
    
    if previous_structure:
        # 재설계 시에는 창의성(Diversity)을 위해 과감하게 높임
        target_temp = 0.85
        print(f"[Structurer] 재설계 모드: Temperature를 {target_temp}로 상향하여 다양성 확보")
        
        # Pydantic 객체일 경우 dict 변환
        prev_str = str(previous_structure)
        
        feedback_msg = f"""
        =====================================================================
        🚨 [CRITICAL FEEDBACK] 사용자가 귀하의 이전 설계를 거절했습니다.
        이전 설계는 "너무 뻔하거나", "차별점이 부족"했습니다.
        
        [이전 목차]:
        {prev_str}
        
        [강력 지시 사항]:
        1. **Self-Criticism**: 이전 목차의 가장 지루한 부분 3가지를 찾으세요.
        2. **Radical Change**: 이전 목차와 섹션 구성이 **최소 40% 이상** 달라져야 합니다.
        3. 단순한 단어 교체가 아니라, **접근 방식(Approach)** 자체를 비트세요. 
           (예: 기능 나열 -> 사용자 스토리 중심, 일반론 -> 틈새 시장 공략 전략)
        =====================================================================
        """
    else:
        # 기본 모드
        feedback_msg = ""
        
    # 동적 LLM 생성
    dynamic_llm = get_llm(temperature=target_temp).with_structured_output(StructureResult)

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
        structure_result = dynamic_llm.invoke(messages)
        
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

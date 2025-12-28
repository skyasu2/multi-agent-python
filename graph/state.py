"""
PlanCraft Agent - 상태 정의 모듈 (TypedDict 기반)

LangGraph 최신 Best Practice에 따라 Input/Output/Internal State를 명확히 분리합니다.
- API/UI는 PlanCraftInput/Output만 노출
- 내부 로직은 PlanCraftState(전체) 사용
- 문서화, 테스트, 자동화 이점 극대화
"""

from typing import Optional, List, Dict, Any, Literal
from typing_extensions import TypedDict, NotRequired

# =============================================================================
# Input Schema (External API/UI Interface)
# =============================================================================

class PlanCraftInput(TypedDict, total=False):
    """
    외부에서 유입되는 입력 데이터 스키마
    
    API/UI/테스트에서만 사용하며, 최소한의 필수 입력만 정의합니다.
    """
    user_input: str  # Required
    file_content: Optional[str]
    refine_count: int
    retry_count: int
    previous_plan: Optional[str]
    thread_id: str


# =============================================================================
# Output Schema (External API/UI Interface)
# =============================================================================

class PlanCraftOutput(TypedDict, total=False):
    """
    최종적으로 반환되는 출력 데이터 스키마
    
    API 응답, UI 렌더링, 테스트 검증에 사용됩니다.
    """
    final_output: Optional[str]
    step_history: List[dict]
    chat_history: List[dict]
    error: Optional[str]
    error_message: Optional[str]
    retry_count: int
    chat_summary: Optional[str]


# =============================================================================
# Interrupt Payload Schema (Human-in-the-loop Interface)
# =============================================================================

class InterruptOption(TypedDict):
    """인터럽트 선택지 스키마"""
    title: str
    description: str


class InterruptPayload(TypedDict):
    """휴먼 인터럽트 페이로드 스키마"""
    type: str  # "option", "form", "confirm"
    question: str
    options: List[InterruptOption]
    input_schema_name: Optional[str]
    data: Optional[dict]


# =============================================================================
# Internal State (Combines Input + Output + Internal Fields)
# =============================================================================

class PlanCraftState(TypedDict, total=False):
    """
    PlanCraft Agent 전체 내부 상태
    
    PlanCraftInput + PlanCraftOutput + 내부 처리용 필드를 모두 포함합니다.
    노드 함수들은 이 타입을 사용하되, 외부 인터페이스는 Input/Output만 노출합니다.
    
    ✅ Best Practice:
    - 외부 API/UI: PlanCraftInput/Output 사용
    - 내부 Agent/Node: PlanCraftState 사용
    - 문서화: Input/Output의 .json_schema() 활용
    """
    
    # ========== From PlanCraftInput ==========
    user_input: str
    file_content: Optional[str]
    refine_count: int
    retry_count: int
    previous_plan: Optional[str]
    thread_id: str
    
    # ========== From PlanCraftOutput ==========
    final_output: Optional[str]
    step_history: List[dict]
    chat_history: List[dict]
    error: Optional[str]
    error_message: Optional[str]
    chat_summary: Optional[str]
    
    # ========== Internal Fields (Not exposed to API/UI) ==========
    
    # Context
    rag_context: Optional[str]
    web_context: Optional[str]
    web_urls: Optional[List[str]]
    
    # Analysis (stored as dict to avoid Pydantic dependency)
    analysis: Optional[dict]
    input_schema_name: Optional[str]
    need_more_info: bool
    options: List[dict]
    option_question: Optional[str]
    selected_option: Optional[str]
    messages: List[Dict[str, str]]
    
    # Structure
    structure: Optional[dict]
    
    # Draft
    draft: Optional[dict]
    
    # Review & Refine
    review: Optional[dict]
    refined: bool
    
    # Metadata & Operations
    current_step: str
    step_status: Literal["RUNNING", "SUCCESS", "FAILED"]
    last_error: Optional[str]
    execution_time: Optional[str]


# =============================================================================
# Helper Functions (Replacing Pydantic methods)
# =============================================================================

def create_initial_state(
    user_input: str,
    file_content: str = None,
    previous_plan: str = None,
    thread_id: str = "default_thread"
) -> PlanCraftState:
    """
    초기 상태를 생성합니다.
    
    TypedDict 기반으로 변경되어 Pydantic 의존성이 없습니다.
    """
    from datetime import datetime
    
    return {
        # Input fields
        "user_input": user_input,
        "file_content": file_content,
        "refine_count": 0,
        "retry_count": 0,
        "previous_plan": previous_plan,
        "thread_id": thread_id,
        
        # Output fields
        "final_output": None,
        "step_history": [],
        "chat_history": [],
        "error": None,
        "error_message": None,
        "chat_summary": None,
        
        # Internal fields
        "rag_context": None,
        "web_context": None,
        "web_urls": None,
        "analysis": None,
        "input_schema_name": None,
        "need_more_info": False,
        "options": [],
        "option_question": None,
        "selected_option": None,
        "messages": [{"role": "user", "content": user_input}],
        "structure": None,
        "draft": None,
        "review": None,
        "refined": False,
        "current_step": "start",
        "step_status": "RUNNING",
        "last_error": None,
        "execution_time": datetime.now().isoformat()
    }


def update_state(base_state: PlanCraftState, **updates) -> PlanCraftState:
    """
    State 업데이트 헬퍼 (Pydantic의 model_copy 대체)
    
    Usage:
        new_state = update_state(state, current_step="analyze", error=None)
    """
    return {**base_state, **updates}

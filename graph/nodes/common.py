"""
공통 노드 유틸리티 함수
"""
import time
from datetime import datetime
from graph.state import PlanCraftState, update_state
from utils.file_logger import get_file_logger

def update_step_history(state: PlanCraftState, step_name: str, status: str, 
                       summary: str = "", error: str = None, event_type: str = "AI",
                       start_time: float = None) -> PlanCraftState:
    """
    Step 실행 결과를 state의 history에 추가하고 로깅합니다.
    (Refactored from workflow.py)
    """
    # 시간 측정
    if not start_time:
        start_time = time.time()
        
    execution_time = f"{time.time() - start_time:.2f}s"
    
    # 로그 기록
    logger = get_file_logger()
    log_msg = f"[{step_name.upper()}] {status} ({event_type})"
    if summary:
        log_msg += f" - {summary}"
    if error:
        log_msg += f" | Error: {error}"
    logger.info(log_msg)
    
    # History 항목 생성
    history_item = {
        "step": step_name,
        "status": status,
        "summary": summary,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "execution_time": execution_time,
        "event_type": event_type,
        "error": error
    }
    
    # State 업데이트 (불변성 유지)
    current_history = state.get("step_history", []) or []
    new_history = current_history + [history_item]
    
    return update_state(
        state, 
        current_step=step_name,
        step_status=status,
        step_history=new_history,
        last_error=error if error else (None if status == "SUCCESS" else state.get("last_error"))
    )

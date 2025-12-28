"""
Error Handler Utility

노드 실행 중 발생하는 예외를 일관되게 처리하기 위한 데코레이터 및 유틸리티를 제공합니다.
모든 노드 함수에 이 데코레이터를 적용하여 코드 중복을 줄이고 에러 추적성을 높입니다.
"""

import functools
import traceback
from datetime import datetime
from typing import Callable, Any
from graph.state import PlanCraftState

def handle_node_error(func: Callable) -> Callable:
    """
    [Decorator] 노드 함수 실행 중 예외 발생 시 에러 상태를 업데이트합니다.
    
    기능:
    1. 예외가 발생하면 에러 메시지와 트레이스백을 추출합니다.
    2. State 객체의 'error', 'error_message', 'step_status' 필드를 업데이트합니다.
    3. Graph 실행이 중단되지 않고 FAILED 상태로 다음 단계(또는 UI)로 넘어가도록 합니다.
    """
    @functools.wraps(func)
    def wrapper(state: PlanCraftState, *args, **kwargs) -> PlanCraftState:
        try:
            return func(state, *args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            tb = traceback.format_exc()
            print(f"[ERROR] Node '{func.__name__}' Failed: {error_msg}\n{tb}")
            
            # 실패 이력 생성 - TypedDict dict 접근
            current_history = state.get("step_history", []) or []
            fail_record = {
                "step": func.__name__,
                "status": "FAILED",
                "summary": f"Error: {error_msg[:50]}...",
                "error": error_msg,
                "timestamp": datetime.now().isoformat()
            }
            
            # TypedDict State 업데이트
            from graph.state import update_state
            
            return update_state(
                state,
                error=error_msg,
                error_message=error_msg,
                step_status="FAILED",
                last_error=error_msg,
                step_history=current_history + [fail_record]
            )
            
    return wrapper

"""
PlanCraft 유틸리티 데코레이터 모듈

주요 기능:
- 입력 상태(State) 검증 (필수 키 확인)
- 실행 전후 로깅 및 유효성 검사

사용법:
    @require_state_keys(["structure", "user_input"])
    def run_writer_node(state):
        ...
"""

import copy
import functools
from typing import List, Any, Callable, Dict
from utils.file_logger import get_file_logger
from graph.state import update_state

def require_state_keys(required_keys: List[str]):
    """
    [Decorator] State 딕셔너리에 필수 키가 존재하는지 검증합니다.
    
    누락된 키가 있으면:
    1. 에러 로그를 기록합니다.
    2. state에 error 메시지를 설정하여 반환합니다(Graceful Failure).
    
    Args:
        required_keys: 필수 키 목록 (예: ["structure", "analysis"])
        
    Usage:
        @require_state_keys(["structure"])
        def run(state: PlanCraftState) -> PlanCraftState:
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(state: Dict[str, Any], *args, **kwargs):
            logger = get_file_logger()
            missing_keys = []
            
            # Pydantic 모델 또는 Dict 처리
            state_dict = state
            if hasattr(state, "model_dump"):
                state_dict = state.model_dump()
            elif hasattr(state, "dict"):
                state_dict = state.dict()
            
            # 키 검사
            for key in required_keys:
                # 1. 키가 아예 없음
                # 2. 키는 있는데 값이 None 또는 빈 값 (False/0 은 제외하고 의미상 빈 것 체크가 필요하나, 
                #    여기서는 존재 여부와 None 여부만 체크)
                if key not in state_dict or state_dict.get(key) is None:
                    missing_keys.append(key)
            
            if missing_keys:
                error_msg = f"[{func.__name__}] 필수 입력 데이터 누락: {', '.join(missing_keys)}"
                logger.error(error_msg)

                # [FIX] 깊은 복사로 원본 상태 오염 방지
                # 얕은 복사(state.copy())는 중첩된 dict/list가 원본을 참조하여 부작용 발생
                if isinstance(state, dict):
                    new_state = copy.deepcopy(state)
                    new_state["error"] = error_msg
                    return new_state
                else:
                    # Pydantic 등인 경우 (여기선 주로 TypedDict/Dict가 옴)
                    return {"error": error_msg}
            
            # 검증 통과 시 원래 함수 실행
            return func(state, *args, **kwargs)
        return wrapper
    return decorator

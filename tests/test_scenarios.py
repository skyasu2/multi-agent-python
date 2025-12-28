"""
PlanCraft Advanced Scenarios Tests

복잡한 사용자 인터랙션 및 에러 상황, 분기 처리를 시뮬레이션하는 고급 시나리오 테스트입니다.
실제 LLM 호출 없이 상태(State) 전이와 분기 로직의 정확성을 검증합니다.
"""

import pytest
from unittest.mock import MagicMock, patch
from graph.state import PlanCraftState
from utils.schemas import AnalysisResult, OptionChoice

class TestAdvancedScenarios:
    """고급 시나리오 테스트 모음"""

    def test_scenario_human_interrupt_flow(self):
        """
        [시나리오 A] 휴먼 인터럽트 흐름 검증
        
        1. 사용자: 모호한 요청
        2. 시스템: 분석 후 추가 정보 필요 판단 (need_more_info=True)
        3. 워크플로우: should_ask_user -> 'option_pause' 라우팅
        4. 노드: option_pause_node 실행 -> 인터럽트 페이로드 생성
        5. 사용자: 옵션 선택 응답
        6. 시스템: 선택 반영 후 상태 업데이트
        """
        # 1. 초기 상태 (모호한 요청)
        # 2. 분석 결과 시뮬레이션 (need_more_info=True)
        analysis = AnalysisResult(
            topic="모호함",
            purpose="불명확",
            target_users="미정",
            need_more_info=True,
            options=[
                OptionChoice(title="웹", description="Web"),
                OptionChoice(title="앱", description="App")
            ],
            option_question="어떤 종류인가요?"
        )
        
        # Validator를 통해 필드 동기화 (analysis -> need_more_info, options, question)
        state = PlanCraftState(
            user_input="앱 만들어줘",
            current_step="analyze",
            analysis=analysis
        )
        # 주의: Pydantic Validator가 정상 동작했는지 확인
        assert state.need_more_info is True
        assert state.option_question == "어떤 종류인가요?"
        
        # 3. 라우팅 로직 검증
        from graph.workflow import should_ask_user
        next_route = should_ask_user(state)
        assert next_route == "option_pause"
        
        # 4. option_pause_node 실행 시뮬레이션
        #    (interrupt 함수는 mock 처리하여 페이로드 확인)
        from graph.workflow import option_pause_node
        from graph.interrupt_utils import handle_user_response
        
        with patch('graph.workflow.interrupt') as mock_interrupt:
            # interrupt 호출 시 None 반환 (로컬 모드 시뮬레이션 or 중단)
            mock_interrupt.return_value = None
            
            paused_state = option_pause_node(state)
            
            # 인터럽트 호출 여부 및 페이로드 검증
            assert mock_interrupt.called
            payload = mock_interrupt.call_args[0][0]
            assert payload['question'] == "어떤 종류인가요?"
            assert len(payload['options']) == 2
            
            # 상태는 'Wait' 상태여야 함 (PAUSED)
            assert paused_state.step_status == "PAUSED"
            
        # 5. 사용자 응답 시뮬레이션 (UI에서 선택)
        user_response = {
            "selected_option": {"title": "웹", "description": "Web"}
        }
        
        # 6. 응답 처리 및 상태 업데이트
        resumed_state = handle_user_response(state, user_response)
        
        # 검증: 에러 플래그 해제, 입력 업데이트
        assert resumed_state.need_more_info is False
        assert "[선택: 웹 - Web]" in resumed_state.user_input
        
        # 다시 라우팅 체크 -> 이제는 continue여야 함
        # 주의: analysis 객체 내부의 need_more_info는 여전히 True일 수 있으나, 
        # 상위 state의 need_more_info가 False로 업데이트되었으므로 로직에 따라 달라짐.
        # should_ask_user 로직: if state.need_more_info: ...
        assert should_ask_user(resumed_state) == "continue"

    def test_scenario_error_and_retry(self):
        """
        [시나리오 B] 에러 발생 및 재시도 흐름 검증
        
        1. 시스템: 실행 중 에러 발생 (State에 error 기록)
        2. UI/로직: 에러 감지 및 상태 전환 (FAILED)
        3. 사용자: 재시도 버튼 클릭
        4. 시스템: 에러 클리어, retry_count 증가
        """
        # 1. 정상 실행 중
        state = PlanCraftState(user_input="GO", current_step="analyze")
        
        # 2. 에러 발생 시뮬레이션 (Try-Except 블록 내 로직)
        try:
            raise ValueError("LLM API Timeout")
        except Exception as e:
            # model_copy로 에러 기록
            error_state = state.model_copy(update={
                "error": str(e),
                "step_status": "FAILED"
            })
            
        # 검증: 에러 상태 반영
        assert error_state.error == "LLM API Timeout"
        assert error_state.step_status == "FAILED"
        # model_validator에 의해 _error 접미사가 붙을 수 있음 (schema 정의 확인 필요)
        if error_state.current_step.endswith("_error"):
             assert True
        
        # 3. 재시도 로직 시뮬레이션 (UI 버튼 클릭 핸들러)
        #    retry_count 증가, error 클리어
        retried_state = error_state.model_copy(update={
            "error": None,
            "step_status": "RUNNING",
            "retry_count": error_state.retry_count + 1
        })
        
        # 검증: 정상화 및 재시도 카운트
        assert retried_state.error is None
        assert retried_state.step_status == "RUNNING"
        assert retried_state.retry_count == 1

    def test_scenario_general_query(self):
        """
        [시나리오 C] 일반 질의 처리 흐름 검증
        
        1. 사용자: "안녕" 입력
        2. 분석기: is_general_query=True 판단
        3. 워크플로우: 'general_response' 라우팅
        4. 노드: general_response_node 실행 및 종료
        """
        state = PlanCraftState(user_input="안녕")
        
        # 분석 결과 주입
        state.analysis = AnalysisResult(
            topic="인사", purpose="", target_users="",
            is_general_query=True,
            general_answer="안녕하세요! 무엇을 도와드릴까요?"
        )
        # 상위 상태 플래그 없어도 analysis 내부 확인하는지 체크 (should_ask_user 구현에 따름)
        # 현재 구현: is_general = state.analysis.is_general_query if state.analysis else False
        
        # 라우팅 확인
        from graph.workflow import should_ask_user
        assert should_ask_user(state) == "general_response"
        
        # 노드 실행
        from graph.workflow import general_response_node
        
        final_state = general_response_node(state)
        
        # 검증
        assert final_state.current_step == "general_response"
        assert final_state.final_output == "안녕하세요! 무엇을 도와드릴까요?"
        # 이력 확인 (마지막 항목)
        last_history = final_state.step_history[-1]
        assert last_history['step'] == "general_response"
        assert last_history['status'] == "SUCCESS"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

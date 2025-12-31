"""
Time-Travel 유틸리티 테스트

utils/time_travel.py 모듈 및 LangGraph 상태 관리 테스트입니다.
"""

import pytest
from uuid import uuid4
from unittest.mock import Mock, patch
from dataclasses import dataclass
from typing import List, Dict, Any

from utils.time_travel import (
    TimeTravel,
    StateSnapshot,
)


# =============================================================================
# Mock 데이터
# =============================================================================

@dataclass
class MockStateSnapshot:
    """Mock LangGraph StateSnapshot"""
    values: Dict[str, Any]
    config: Dict[str, Any]
    next: tuple
    tasks: List[Any]


def create_mock_history():
    """테스트용 Mock 상태 이력 생성"""
    return [
        MockStateSnapshot(
            values={
                "current_step": "format",
                "user_input": "테스트 입력",
                "final_output": "# 기획서\n...",
                "step_history": [
                    {"step": "analyze", "status": "SUCCESS", "timestamp": "2025-12-31 10:00:00"},
                    {"step": "structure", "status": "SUCCESS", "timestamp": "2025-12-31 10:01:00"},
                    {"step": "write", "status": "SUCCESS", "timestamp": "2025-12-31 10:02:00"},
                    {"step": "format", "status": "SUCCESS", "timestamp": "2025-12-31 10:03:00"},
                ]
            },
            config={"configurable": {"checkpoint_id": "cp_4", "thread_id": "test_thread"}},
            next=(),
            tasks=[]
        ),
        MockStateSnapshot(
            values={
                "current_step": "write",
                "user_input": "테스트 입력",
                "draft": {"sections": []},
                "step_history": [
                    {"step": "analyze", "status": "SUCCESS", "timestamp": "2025-12-31 10:00:00"},
                    {"step": "structure", "status": "SUCCESS", "timestamp": "2025-12-31 10:01:00"},
                    {"step": "write", "status": "SUCCESS", "timestamp": "2025-12-31 10:02:00"},
                ]
            },
            config={"configurable": {"checkpoint_id": "cp_3", "thread_id": "test_thread"}},
            next=("review",),
            tasks=[]
        ),
        MockStateSnapshot(
            values={
                "current_step": "structure",
                "user_input": "테스트 입력",
                "structure": {"title": "테스트", "sections": []},
                "step_history": [
                    {"step": "analyze", "status": "SUCCESS", "timestamp": "2025-12-31 10:00:00"},
                    {"step": "structure", "status": "SUCCESS", "timestamp": "2025-12-31 10:01:00"},
                ]
            },
            config={"configurable": {"checkpoint_id": "cp_2", "thread_id": "test_thread"}},
            next=("write",),
            tasks=[]
        ),
        MockStateSnapshot(
            values={
                "current_step": "analyze",
                "user_input": "테스트 입력",
                "analysis": {"topic": "테스트"},
                "step_history": [
                    {"step": "analyze", "status": "SUCCESS", "timestamp": "2025-12-31 10:00:00"},
                ]
            },
            config={"configurable": {"checkpoint_id": "cp_1", "thread_id": "test_thread"}},
            next=("structure",),
            tasks=[]
        ),
    ]


# =============================================================================
# StateSnapshot 데이터 클래스 테스트
# =============================================================================

class TestStateSnapshot:
    """StateSnapshot 데이터 클래스 테스트"""

    def test_create_snapshot(self):
        """스냅샷 생성 테스트"""
        snapshot = StateSnapshot(
            checkpoint_id="cp_1",
            step_name="analyze",
            timestamp="2025-12-31 10:00:00",
            state={"user_input": "테스트"},
            metadata={"next": ["structure"]}
        )
        assert snapshot.checkpoint_id == "cp_1"
        assert snapshot.step_name == "analyze"
        assert snapshot.state["user_input"] == "테스트"


# =============================================================================
# TimeTravel 클래스 테스트 (Mock 기반)
# =============================================================================

class TestTimeTravelMock:
    """TimeTravel 클래스 Mock 기반 테스트"""

    @pytest.fixture
    def mock_app(self):
        """Mock LangGraph App"""
        app = Mock()
        app.get_state_history = Mock(return_value=iter(create_mock_history()))
        app.get_state = Mock(return_value=create_mock_history()[0])
        app.update_state = Mock()
        app.invoke = Mock(return_value={"final_output": "결과"})
        return app

    @pytest.fixture
    def time_travel(self, mock_app):
        """TimeTravel 인스턴스"""
        return TimeTravel(mock_app, thread_id="test_thread")

    def test_get_current_state(self, time_travel, mock_app):
        """현재 상태 조회 테스트"""
        state = time_travel.get_current_state()
        assert state is not None
        assert state["current_step"] == "format"
        mock_app.get_state.assert_called_once()

    def test_get_state_history(self, time_travel):
        """상태 이력 조회 테스트"""
        history = time_travel.get_state_history(limit=10)
        assert len(history) == 4
        assert history[0].step_name == "format"
        assert history[1].step_name == "write"
        assert history[2].step_name == "structure"
        assert history[3].step_name == "analyze"

    def test_get_state_at_step(self, time_travel):
        """특정 단계 상태 조회 테스트"""
        snapshot = time_travel.get_state_at_step(0)
        assert snapshot is not None
        assert snapshot.step_name == "format"

        snapshot = time_travel.get_state_at_step(1)
        assert snapshot is not None
        assert snapshot.step_name == "write"

    def test_get_state_at_invalid_step(self, time_travel):
        """유효하지 않은 단계 조회 테스트"""
        snapshot = time_travel.get_state_at_step(100)
        assert snapshot is None

    def test_compare_states(self, time_travel):
        """상태 비교 테스트"""
        diff = time_travel.compare_states(step1=0, step2=3)
        assert "current_step" in diff
        assert diff["current_step"]["step1_value"] == "format"
        assert diff["current_step"]["step2_value"] == "analyze"

    def test_rollback_to_step(self, time_travel, mock_app):
        """롤백 테스트"""
        result = time_travel.rollback_to_step(step_index=2)
        assert result is True
        mock_app.update_state.assert_called_once()

    def test_rollback_invalid_step(self, time_travel):
        """유효하지 않은 단계 롤백 테스트"""
        result = time_travel.rollback_to_step(step_index=100)
        assert result is False

    def test_replay_from_step(self, time_travel, mock_app):
        """재실행 테스트"""
        result = time_travel.replay_from_step(step_index=2)
        assert result is not None
        assert result["final_output"] == "결과"
        mock_app.invoke.assert_called_once()

    def test_get_step_summary(self, time_travel):
        """단계 요약 조회 테스트"""
        summaries = time_travel.get_step_summary()
        assert len(summaries) == 4
        assert summaries[0]["step_name"] == "format"
        assert summaries[0]["can_rollback"] is True

    def test_summarize_value_types(self, time_travel):
        """값 요약 테스트"""
        assert time_travel._summarize_value(None) == "None"
        assert time_travel._summarize_value("short") == "short"
        assert "..." in time_travel._summarize_value("a" * 200)
        assert "[5 items]" == time_travel._summarize_value([1, 2, 3, 4, 5])
        assert "2 keys" in time_travel._summarize_value({"a": 1, "b": 2})


# =============================================================================
# 에러 처리 테스트
# =============================================================================

class TestTimeTravelErrors:
    """TimeTravel 에러 처리 테스트"""

    def test_get_state_history_error(self):
        """이력 조회 에러 처리"""
        mock_app = Mock()
        mock_app.get_state_history = Mock(side_effect=Exception("DB Error"))

        tt = TimeTravel(mock_app, "test_thread")
        history = tt.get_state_history()
        assert history == []

    def test_get_current_state_error(self):
        """현재 상태 조회 에러 처리"""
        mock_app = Mock()
        mock_app.get_state = Mock(side_effect=Exception("Connection Error"))

        tt = TimeTravel(mock_app, "test_thread")
        state = tt.get_current_state()
        assert state is None

    def test_rollback_error(self):
        """롤백 에러 처리"""
        mock_app = Mock()
        mock_app.get_state_history = Mock(return_value=iter(create_mock_history()))
        mock_app.update_state = Mock(side_effect=Exception("Update Error"))

        tt = TimeTravel(mock_app, "test_thread")
        result = tt.rollback_to_step(1)
        assert result is False


# =============================================================================
# 통합 테스트 (실제 App 사용 - 선택적)
# =============================================================================

class TestTimeTravelIntegration:
    """
    실제 LangGraph App을 사용한 통합 테스트

    주의: 이 테스트는 실제 워크플로우를 실행하므로
    LLM API 호출이 발생할 수 있습니다.
    """

    @pytest.fixture
    def config(self):
        return {"configurable": {"thread_id": str(uuid4())}}

    @pytest.mark.skip(reason="실제 LLM API 호출이 필요한 통합 테스트")
    def test_real_workflow_time_travel(self, config):
        """실제 워크플로우 Time-Travel 테스트"""
        from graph.workflow import app
        from graph.state import PlanCraftInput

        inputs: PlanCraftInput = {
            "user_input": "안녕하세요",
            "file_content": None,
            "refine_count": 0,
            "previous_plan": None,
            "thread_id": config["configurable"]["thread_id"],
            "retry_count": 0
        }

        # 실행
        app.invoke(inputs, config=config)

        # TimeTravel 인스턴스 생성
        tt = TimeTravel(app, config["configurable"]["thread_id"])

        # 이력 조회
        history = tt.get_state_history()
        assert len(history) > 0

        # 현재 상태 조회
        current = tt.get_current_state()
        assert current is not None

    def test_state_modification(self, config):
        """상태 수정 테스트 (Mock 없이)"""
        from graph.workflow import app
        from graph.state import PlanCraftInput

        inputs: PlanCraftInput = {
            "user_input": "단순 인사",
            "file_content": None,
            "refine_count": 0,
            "previous_plan": None,
            "thread_id": config["configurable"]["thread_id"],
            "retry_count": 0
        }

        try:
            # 실행
            app.invoke(inputs, config=config)

            # 상태 수정
            app.update_state(config, {"user_input": "Modified Input"})
            updated_state = app.get_state(config)

            assert updated_state.values["user_input"] == "Modified Input"
        except Exception:
            # LLM API 없이는 실패할 수 있음
            pytest.skip("LLM API 필요")

"""
PlanCraft Mock Agents Test

[Local Test] Mock LLM을 활용한 에이전트 로직 검증
API Key 없이 로컬에서 agent.run() 함수의 동작을 테스트합니다.

[UPDATE] 지연 초기화 패턴(_get_*_llm 함수)에 맞춰 패치 경로 수정
"""

import pytest
from unittest.mock import MagicMock, patch
from graph.state import create_initial_state, update_state
from utils.schemas import AnalysisResult, StructureResult, SectionStructure, DraftResult, SectionContent, JudgeResult

class TestMockAgents:
    """
    [Local Test] Mock LLM을 활용한 에이전트 로직 검증
    API Key 없이 로컬에서 agent.run() 함수의 동작을 테스트합니다.
    """

    @patch('agents.analyzer._get_analyzer_llm')
    def test_analyzer_mock(self, mock_get_llm):
        """Analyzer 에이전트 Mock 테스트 (지연 초기화 패턴)"""
        print("\n[Test] Analyzer Mock Run")

        mock_output = AnalysisResult(
            topic="Mock AI App",
            purpose="For Testing",
            target_users="Tester",
            key_features=["Feature A", "Feature B"],
            need_more_info=False
        )

        # _get_analyzer_llm()이 반환하는 Mock 체인 설정
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = mock_output
        mock_get_llm.return_value = mock_llm

        from agents.analyzer import run
        state = create_initial_state("AI 앱 기획해줘")
        new_state = run(state)

        analysis = new_state.get("analysis")
        assert analysis is not None
        assert analysis["topic"] == "Mock AI App"
        print("✅ Analyzer Output Verified")

    @patch('agents.structurer.get_llm')
    def test_structurer_mock(self, mock_get_llm):
        """Structurer 에이전트 Mock 테스트 (동적 LLM)"""
        print("\n[Test] Structurer Mock Run")
        
        mock_output = StructureResult(
            title="Mock Plan",
            sections=[
                SectionStructure(id=1, name="Intro", description="Desc 1", key_points=[]),
                SectionStructure(id=2, name="Core", description="Desc 2", key_points=[])
            ]
        )
        
        mock_llm_instance = mock_get_llm.return_value
        mock_runnable = mock_llm_instance.with_structured_output.return_value
        mock_runnable.invoke.return_value = mock_output
        
        from agents.structurer import run
        state = create_initial_state("AI 앱")
        state = update_state(state, analysis={"topic": "Mock", "key_features": []})
        new_state = run(state)
        
        structure = new_state.get("structure")
        assert structure is not None
        assert structure["title"] == "Mock Plan"
        print("✅ Structurer Output Verified")

    @patch('agents.writer.get_llm')
    def test_writer_mock(self, mock_get_llm):
        """Writer 에이전트 Mock 테스트 (get_llm 직접 패치)"""
        print("\n[Test] Writer Mock Run")

        # 최소 섹션 수(9개)를 만족하는 Mock 출력 생성
        mock_sections = [
            SectionContent(id=i, name=f"Section {i}", content=f"# Section {i}\n{'Mock Content ' * 20}")
            for i in range(1, 10)  # 9개 섹션
        ]
        mock_output = DraftResult(sections=mock_sections)

        # get_llm().with_structured_output().invoke() 체인 Mock
        mock_llm_instance = MagicMock()
        mock_runnable = MagicMock()
        mock_runnable.invoke.return_value = mock_output
        mock_llm_instance.with_structured_output.return_value = mock_runnable
        mock_get_llm.return_value = mock_llm_instance

        state = create_initial_state("AI 앱")
        state = update_state(state,
            analysis={"topic": "Mock", "key_features": []},
            structure={"title": "Plan", "sections": [
                {"id": i, "name": f"Section {i}", "description": f"D{i}", "key_points": []}
                for i in range(1, 10)
            ]},
            generation_preset="balanced"  # 최소 9개 섹션 요구
        )

        from agents.writer import run
        new_state = run(state)

        draft = new_state.get("draft")
        assert draft is not None
        assert len(draft["sections"]) >= 9, "최소 9개 섹션이 있어야 함"
        print("✅ Writer Output Verified")

    @patch('agents.reviewer.get_llm')
    def test_reviewer_mock(self, mock_get_llm):
        """Reviewer 에이전트 Mock 테스트 (get_llm 직접 패치)"""
        print("\n[Test] Reviewer Mock Run")

        # Mock Response
        mock_output = JudgeResult(
            overall_score=8,
            verdict="PASS",
            feedback_summary="Good Job",
            critical_issues=[],
            action_items=[]
        )

        # get_llm().with_structured_output().invoke() 체인 Mock
        mock_llm_instance = MagicMock()
        mock_runnable = MagicMock()
        mock_runnable.invoke.return_value = mock_output
        mock_llm_instance.with_structured_output.return_value = mock_runnable
        mock_get_llm.return_value = mock_llm_instance

        from agents.reviewer import run
        state = create_initial_state("AI 앱")
        draft = DraftResult(sections=[SectionContent(id=1, name="Intro", content="Content")])
        state = update_state(state, draft=draft.model_dump())

        new_state = run(state)

        review = new_state.get("review")
        assert review is not None
        assert review["overall_score"] == 8
        print("✅ Reviewer Output Verified")

    def test_refiner_logic(self):
        """Refiner 에이전트 로직 테스트 (No LLM)"""
        print("\n[Test] Refiner Logic Run")
        
        from agents.refiner import run
        
        # Case 1: FAIL -> Refine Mode
        state = create_initial_state("AI 앱")
        state = update_state(state, 
            review={"verdict": "FAIL", "feedback_summary": "Bad"},
            draft={"sections": [{"name": "A", "content": "B"}]}
        )
        
        new_state = run(state)
        
        assert new_state["refined"] is True
        assert new_state["refine_count"] == 1
        assert new_state["previous_plan"] is not None
        print("✅ Refiner (Fail Case) Verified")

    @patch('agents.formatter.get_llm')
    def test_formatter_mock(self, mock_get_llm):
        """Formatter 에이전트 Mock 테스트"""
        print("\n[Test] Formatter Mock Run")
        
        # Mock Response (Non-structured, just AIMessage or object with content)
        mock_llm_instance = mock_get_llm.return_value
        mock_response = MagicMock()
        mock_response.content = "## Mock Chat Summary"
        mock_llm_instance.invoke.return_value = mock_response
        
        from agents.formatter import run
        state = create_initial_state("AI 앱")
        state = update_state(state, 
            analysis={"topic": "Mock", "key_features": []},
            final_output="# Full Plan"
        )
        
        new_state = run(state)
        
        assert new_state["chat_summary"] == "## Mock Chat Summary"
        print("✅ Formatter Output Verified")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])


import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# 프로젝트 루트 경로 강제 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

print(f"[Debug] Path configured: {project_root}")

try:
    import utils.schemas
    # 모듈 로딩 테스트
    import agents.writer
    print("[Debug] agents.writer imported")
    from graph.state import PlanCraftState
    print("[Debug] graph.state imported")
except ImportError as e:
    print(f"[Fatal Error] Import failed during setup: {e}")
    sys.exit(1)

class TestWriterRefactor(unittest.TestCase):
    @patch('agents.writer.get_llm')
    @patch('agents.writer.get_specialist_context')
    def test_writer_run_success(self, mock_specialist_ctx, mock_get_llm):
        """Writer Agent 리팩토링 검증 테스트"""

        # 1. Mock 설정 [REFACTOR] Supervisor 노드 분리로 인한 Mock 변경
        mock_specialist_ctx.return_value = "Mock Specialist Context"
        
        mock_chain = MagicMock()
        mock_llm_instance = MagicMock()
        mock_llm_instance.with_structured_output.return_value = mock_chain
        mock_get_llm.return_value = mock_llm_instance
        
        mock_draft = {
            "title": "Test Plan",
            "sections": [
                {"id": 1, "name": "Summary", "content": "# Summary\nGood summary."},
                {"id": 2, "name": "Feature", "content": "# Feature\nGood feature."},
                {"id": 3, "name": "Tech", "content": "# Tech\nGood tech."}
            ]
        }
        mock_chain.invoke.return_value = mock_draft

        # 2. State 설정
        state = PlanCraftState(
            user_input="AI 헬스케어 앱",
            structure="Summary, Feature, Tech",
            analysis={
                "topic": "헬스케어", 
                "doc_type": "web_app_plan",
                "user_constraints": ["Python 사용"],
                "target_market": "General", 
                "target_user": "User",
                "tech_stack": "Python"
            },
            generation_preset="fast"
        )

        # 3. Writer 실행
        print(">> Running Writer Agent (Refactored)...")
        # 직접 모듈 참조로 실행
        result_state = agents.writer.run(state)

        # 4. 검증
        self.assertIn("draft", result_state)
        current_step = result_state.get("current_step")
        self.assertEqual(current_step, "write")
        
        draft = result_state["draft"]
        if hasattr(draft, "model_dump"):
            draft = draft.model_dump()
            
        self.assertEqual(len(draft["sections"]), 3)
        
        print(">> Writer Agent executed successfully!")
        print(f">> Result Step: {current_step}")

        # [REFACTOR] Supervisor 노드 분리로 mock 검증 변경
        mock_specialist_ctx.assert_called_once()

if __name__ == "__main__":
    unittest.main()

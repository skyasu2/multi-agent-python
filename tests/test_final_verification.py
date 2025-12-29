"""
PlanCraft Agent - 최종 검증 테스트 (Phase 1 & 2)

이 테스트는 최근 개선된 Multi-Agent 기능이 정상 동작하는지 검증합니다.
1. Phase 2: 병렬 컨텍스트 수집 (시간 측정)
2. Phase 1: 동적 라우팅 (Mocking을 통한 분기 확인)
"""

import time
import unittest
from unittest.mock import MagicMock, patch
from graph.state import PlanCraftState
from graph.subgraphs import run_context_subgraph
from graph.workflow import should_refine_or_restart

class TestFinalVerification(unittest.TestCase):
    
    def setUp(self):
        self.mock_state = {
            "user_input": "테스트 요청",
            "step_history": [],
            "restart_count": 0
        }

    @patch("graph.workflow.retrieve_context")
    @patch("graph.workflow.fetch_web_context")
    def test_phase2_parallel_execution(self, mock_web, mock_rag):
        """Phase 2: 병렬 실행으로 시간이 단축되는지 검증"""
        print("\n[TEST] Phase 2: 병렬 컨텍스트 수집 테스트")
        
        # 각 작업이 1초씩 걸리도록 설정
        def slow_rag(state):
            print("  [Mock] RAG Start")
            time.sleep(1.0)
            return {"rag_context": "RAG Done"}
            
        def slow_web(state):
            print("  [Mock] Web Start")
            time.sleep(1.0)
            return {"web_context": "Web Done"}
            
        mock_rag.side_effect = slow_rag
        mock_web.side_effect = slow_web
        
        start_time = time.time()
        result = run_context_subgraph(self.mock_state)
        elapsed = time.time() - start_time
        
        print(f"  - 실행 시간: {elapsed:.2f}초")
        
        # 순차 실행이면 2초+, 병렬이면 1초+ (오버헤드 포함 1.5초 이내)
        self.assertLess(elapsed, 1.8, "병렬 실행이 효과적이지 않음 (너무 오래 걸림)")
        self.assertEqual(result["rag_context"], "RAG Done")
        self.assertEqual(result["web_context"], "Web Done")
        print("  ✅ 병렬 실행 성공")

    def test_phase1_dynamic_routing(self):
        """Phase 1: Review 점수에 따른 동적 라우팅 검증"""
        print("\n[TEST] Phase 1: 동적 라우팅 테스트")
        
        # Case 1: 점수 낮음 -> Analyzer 복귀
        state_fail = {"review": {"overall_score": 4, "verdict": "FAIL"}, "restart_count": 0}
        route1 = should_refine_or_restart(state_fail)
        self.assertEqual(route1, "restart", "점수가 낮은데 restart로 가지 않음")
        print("  ✅ Case 1 (점수 낮음 -> 재분석): 통과")
        
        # Case 2: 점수 보통 -> Refiner
        state_revise = {"review": {"overall_score": 7, "verdict": "REVISE"}, "restart_count": 0}
        route2 = should_refine_or_restart(state_revise)
        self.assertEqual(route2, "refine", "점수가 보통인데 refine으로 가지 않음")
        print("  ✅ Case 2 (점수 보통 -> 개선): 통과")
        
        # Case 3: 점수 높음 -> 완료
        state_pass = {"review": {"overall_score": 9, "verdict": "PASS"}, "restart_count": 0}
        route3 = should_refine_or_restart(state_pass)
        self.assertEqual(route3, "complete", "점수가 높은데 complete로 가지 않음")
        print("  ✅ Case 3 (점수 높음 -> 완료): 통과")
        
        # Case 4: 무한 루프 방지 (restart_count >= 2)
        state_loop = {"review": {"overall_score": 2, "verdict": "FAIL"}, "restart_count": 2}
        route4 = should_refine_or_restart(state_loop)
        self.assertEqual(route4, "refine", "최대 복귀 횟수 초과 시 refine으로 강제 진행해야 함")
        print("  ✅ Case 4 (무한 루프 방지): 통과")

if __name__ == "__main__":
    unittest.main()

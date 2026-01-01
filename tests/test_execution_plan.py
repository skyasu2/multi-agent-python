import sys
import os
import unittest

# 프로젝트 루트 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.agent_config import resolve_execution_plan_dag, AGENT_REGISTRY

class TestExecutionPlan(unittest.TestCase):
    
    def test_full_plan(self):
        """전체(4개) 요청 시 올바른 DAG 계획 생성 확인"""
        required = ["market", "bm", "financial", "risk"]
        plan = resolve_execution_plan_dag(required, "Test Full")
        
        print("\n--- [Test] Full Plan ---")
        for step in plan.steps:
            print(f"Step {step.step_id}: {step.agent_ids}")
            
        # 예상:
        # Step 1: market (depends: none)
        # Step 2: bm (depends: market [optional], in practice market -> bm)
        # Step 3: financial, risk (depends: bm)
        
        # 1. market은 항상 첫 번째여야 함 (권장 의존성)
        self.assertIn("market", plan.steps[0].agent_ids)
        
        # 2. bm은 market 다음에 실행
        bm_step = next(s.step_id for s in plan.steps if "bm" in s.agent_ids)
        market_step = next(s.step_id for s in plan.steps if "market" in s.agent_ids)
        self.assertGreater(bm_step, market_step)
        
        # 3. financial과 risk는 bm 다음에 실행
        fin_step = next(s.step_id for s in plan.steps if "financial" in s.agent_ids)
        risk_step = next(s.step_id for s in plan.steps if "risk" in s.agent_ids)
        self.assertGreater(fin_step, bm_step)
        self.assertGreater(risk_step, bm_step)
        
        # 4. financial과 risk는 병렬 실행 가능 (같은 레이어 또는 독립)
        # 여기서는 financial, risk가 같은 단계에 있거나 순서 상관 없음
        # 현재 로직상 bm 완료 후 financial, risk는 모두 의존성 충족
        # 따라서 같은 스텝에 있어야 함
        self.assertEqual(fin_step, risk_step)
        
    def test_single_agent(self):
        """단일 에이전트 요청 시 의존성 자동 추가 확인"""
        required = ["financial"]
        plan = resolve_execution_plan_dag(required, "Test Single")
        
        print("\n--- [Test] Single (Financial) -> Auto Dependency ---")
        agents = plan.get_all_agents()
        print(f"All Agents: {agents}")
        
        self.assertIn("bm", agents, "BM이 자동으로 추가되어야 합니다")
        self.assertIn("financial", agents)
        
        # BM이 Financial보다 먼저 실행되어야 함
        bm_step = next(s.step_id for s in plan.steps if "bm" in s.agent_ids)
        fin_step = next(s.step_id for s in plan.steps if "financial" in s.agent_ids)
        self.assertGreater(fin_step, bm_step)

if __name__ == "__main__":
    unittest.main()

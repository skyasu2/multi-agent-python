
import pytest
from unittest.mock import MagicMock, patch
from agents.supervisor import NativeSupervisor, RoutingDecision
from agents.agent_config import ExecutionPlan

class TestDynamicAgents:
    
    @pytest.fixture
    def supervisor(self):
        """Supervisor 인스턴스 생성 (LLM 없이)"""
        # LLM 객체 Mocking
        mock_llm = MagicMock()
        return NativeSupervisor(llm=mock_llm)

    def test_agent_loading(self, supervisor):
        """신규 에이전트(Tech, Content)가 정상 로딩되었는지 확인"""
        assert "tech" in supervisor.agents
        assert "content" in supervisor.agents
        print("\n✅ New Agents Loaded: Tech, Content")

    def test_execution_plan_logic(self, supervisor):
        """Tech/Content 포함 시 실행 계획(DAG) 검증"""
        
        # 가상 시나리오: 마켓, BM, 기술, 콘텐츠 모두 필요
        required_agents = ["market", "bm", "tech", "content"]
        reasoning = "테스트 시나리오: 앱 개발 및 마케팅 전략 필요"
        
        # 실제 DAG 로직 호출 (config import)
        from agents.agent_config import resolve_execution_plan_dag
        
        plan = resolve_execution_plan_dag(required_agents, reasoning)
        
        print(f"\n📋 Execution Plan for {required_agents}:")
        for step in plan.steps:
            print(f"  Stage {step.step_id}: {step.agent_ids} ({step.description})")
            
        # 검증 로직
        # 1. Market은 최우선이어야 함 (Stage 1)
        assert "market" in plan.steps[0].agent_ids
        
        # 2. Tech는 의존성 없으므로 Market과 같거나 그 다음이어야 함.
        #    (현재 로직상 Market -> (Tech, BM, ...) 일 수 있음. 확인 필요)
        #    agent_config.py 로직에 따르면:
        #    - Market(deps=[]) -> Layer 1
        #    - Tech(deps=[]) -> Layer 1 (동시 실행 가능!)
        #    - BM(deps=[market]) -> Layer 2
        #    - Content(deps=[market]) -> Layer 2
        
        # Layer 1 검증: Market, Tech
        layer1 = plan.steps[0].agent_ids
        assert "market" in layer1
        assert "tech" in layer1
        
        # Layer 2 검증: BM, Content
        layer2 = plan.steps[1].agent_ids
        assert "bm" in layer2
        assert "content" in layer2
        
        print("\n✅ DAG Logic Verified: [Market, Tech] -> [BM, Content] 병렬 실행 구조 확인")

if __name__ == "__main__":
    # 간단 실행
    t = TestDynamicAgents()
    sup = t.supervisor(None) # fixture manually
    t.test_agent_loading(sup)
    t.test_execution_plan_logic(sup)

"""
PlanCraft - Plan Supervisor (오케스트레이터)

Multi-Agent 아키텍처의 핵심 컴포넌트입니다.
전문 에이전트들의 실행을 조율하고 결과를 통합합니다.

워크플로우:
    1. 사용자 요청 분석
    2. 필요한 전문 에이전트 결정
    3. 전문 에이전트 병렬/순차 실행
    4. 결과 통합 및 Writer에게 전달
"""

from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from pydantic import BaseModel, Field
from utils.llm import get_llm
from utils.file_logger import FileLogger

# 전문 에이전트 임포트
from agents.specialists.market_agent import MarketAgent
from agents.specialists.bm_agent import BMAgent
from agents.specialists.financial_agent import FinancialAgent
from agents.specialists.risk_agent import RiskAgent

logger = FileLogger()


# =============================================================================
# Supervisor State
# =============================================================================

class SupervisorState(BaseModel):
    """Supervisor 상태"""
    service_overview: str = Field(description="서비스 개요")
    target_market: str = Field(default="", description="타겟 시장")
    target_users: str = Field(default="", description="타겟 사용자")
    tech_stack: str = Field(default="", description="기술 스택")
    development_scope: str = Field(default="MVP 3개월", description="개발 범위")
    web_search_results: List[Dict[str, Any]] = Field(default_factory=list)
    
    # 에이전트 출력
    market_analysis: Optional[Dict[str, Any]] = None
    business_model: Optional[Dict[str, Any]] = None
    financial_plan: Optional[Dict[str, Any]] = None
    risk_analysis: Optional[Dict[str, Any]] = None
    
    # 통합 결과
    integrated_context: Optional[str] = None


# =============================================================================
# Plan Supervisor
# =============================================================================

class PlanSupervisor:
    """
    기획서 생성 오케스트레이터
    
    전문 에이전트들을 조율하여 고품질 기획서 컨텍스트를 생성합니다.
    """
    
    def __init__(self, llm=None, parallel: bool = True):
        """
        Args:
            llm: LLM 인스턴스 (선택)
            parallel: 에이전트 병렬 실행 여부 (기본 True)
        """
        self.llm = llm or get_llm()
        self.parallel = parallel
        
        # 전문 에이전트 초기화
        self.market_agent = MarketAgent(llm=self.llm)
        self.bm_agent = BMAgent(llm=self.llm)
        self.financial_agent = FinancialAgent(llm=self.llm)
        self.risk_agent = RiskAgent(llm=self.llm)
        
        logger.info("[Supervisor] 초기화 완료")
    
    def run(
        self,
        service_overview: str,
        target_market: str = "",
        target_users: str = "",
        tech_stack: str = "React Native + Node.js + PostgreSQL",
        development_scope: str = "MVP 3개월",
        web_search_results: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        전문 에이전트들을 실행하고 결과를 통합합니다.
        
        Args:
            service_overview: 서비스 개요
            target_market: 타겟 시장
            target_users: 타겟 사용자
            tech_stack: 기술 스택
            development_scope: 개발 범위
            web_search_results: 웹 검색 결과
            
        Returns:
            통합된 전문 분석 결과
        """
        logger.info("=" * 60)
        logger.info("[Supervisor] 전문 에이전트 오케스트레이션 시작")
        logger.info(f"  서비스: {service_overview[:50]}...")
        logger.info(f"  병렬 실행: {self.parallel}")
        logger.info("=" * 60)
        
        results = {}
        
        if self.parallel:
            results = self._run_parallel(
                service_overview, target_market, target_users,
                tech_stack, development_scope, web_search_results
            )
        else:
            results = self._run_sequential(
                service_overview, target_market, target_users,
                tech_stack, development_scope, web_search_results
            )
        
        # 결과 통합
        integrated = self._integrate_results(results)
        results["integrated_context"] = integrated
        
        logger.info("[Supervisor] 오케스트레이션 완료")
        return results
    
    def _run_parallel(
        self,
        service_overview: str,
        target_market: str,
        target_users: str,
        tech_stack: str,
        development_scope: str,
        web_search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """에이전트 병렬 실행"""
        results = {}
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            # 1단계: Market + BM 먼저 (Financial, Risk에 필요)
            futures["market"] = executor.submit(
                self.market_agent.run,
                service_overview,
                target_market,
                web_search_results
            )
            
            # Market 결과 대기 후 나머지 실행
            market_result = futures["market"].result()
            results["market_analysis"] = market_result
            logger.info("[Supervisor] ✓ Market Agent 완료")
            
            # 2단계: BM, Financial, Risk 병렬
            competitors = market_result.get("competitors", [])
            
            futures["bm"] = executor.submit(
                self.bm_agent.run,
                service_overview,
                target_users,
                competitors
            )
            
            # BM 결과 대기
            bm_result = futures["bm"].result()
            results["business_model"] = bm_result
            logger.info("[Supervisor] ✓ BM Agent 완료")
            
            # Financial과 Risk는 BM 결과 필요
            futures["financial"] = executor.submit(
                self.financial_agent.run,
                service_overview,
                bm_result,
                market_result,
                development_scope
            )
            
            futures["risk"] = executor.submit(
                self.risk_agent.run,
                service_overview,
                bm_result,
                tech_stack
            )
            
            # 결과 수집
            results["financial_plan"] = futures["financial"].result()
            logger.info("[Supervisor] ✓ Financial Agent 완료")
            
            results["risk_analysis"] = futures["risk"].result()
            logger.info("[Supervisor] ✓ Risk Agent 완료")
        
        return results
    
    def _run_sequential(
        self,
        service_overview: str,
        target_market: str,
        target_users: str,
        tech_stack: str,
        development_scope: str,
        web_search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """에이전트 순차 실행 (디버깅용)"""
        results = {}
        
        # 1. Market Agent
        logger.info("[Supervisor] Market Agent 실행...")
        results["market_analysis"] = self.market_agent.run(
            service_overview, target_market, web_search_results
        )
        logger.info("[Supervisor] ✓ Market Agent 완료")
        
        # 2. BM Agent
        logger.info("[Supervisor] BM Agent 실행...")
        competitors = results["market_analysis"].get("competitors", [])
        results["business_model"] = self.bm_agent.run(
            service_overview, target_users, competitors
        )
        logger.info("[Supervisor] ✓ BM Agent 완료")
        
        # 3. Financial Agent
        logger.info("[Supervisor] Financial Agent 실행...")
        results["financial_plan"] = self.financial_agent.run(
            service_overview,
            results["business_model"],
            results["market_analysis"],
            development_scope
        )
        logger.info("[Supervisor] ✓ Financial Agent 완료")
        
        # 4. Risk Agent
        logger.info("[Supervisor] Risk Agent 실행...")
        results["risk_analysis"] = self.risk_agent.run(
            service_overview,
            results["business_model"],
            tech_stack
        )
        logger.info("[Supervisor] ✓ Risk Agent 완료")
        
        return results
    
    def _integrate_results(self, results: Dict[str, Any]) -> str:
        """
        전문 에이전트 결과를 통합하여 Writer용 컨텍스트 생성
        """
        integrated = "## 전문 에이전트 분석 결과\n\n"
        
        # Market Analysis
        if results.get("market_analysis"):
            integrated += "### 📊 시장 분석 (Market Agent)\n\n"
            integrated += self.market_agent.format_as_markdown(results["market_analysis"])
            integrated += "\n"
        
        # Business Model
        if results.get("business_model"):
            integrated += "### 💰 비즈니스 모델 (BM Agent)\n\n"
            integrated += self.bm_agent.format_as_markdown(results["business_model"])
            integrated += "\n"
        
        # Financial Plan
        if results.get("financial_plan"):
            integrated += "### 📈 재무 계획 (Financial Agent)\n\n"
            integrated += self.financial_agent.format_as_markdown(results["financial_plan"])
            integrated += "\n"
        
        # Risk Analysis
        if results.get("risk_analysis"):
            integrated += "### ⚠️ 리스크 분석 (Risk Agent)\n\n"
            integrated += self.risk_agent.format_as_markdown(results["risk_analysis"])
            integrated += "\n"
        
        return integrated
    
    def get_agent_markdown(self, agent_name: str, results: Dict[str, Any]) -> str:
        """특정 에이전트 결과를 마크다운으로 반환"""
        if agent_name == "market" and results.get("market_analysis"):
            return self.market_agent.format_as_markdown(results["market_analysis"])
        elif agent_name == "bm" and results.get("business_model"):
            return self.bm_agent.format_as_markdown(results["business_model"])
        elif agent_name == "financial" and results.get("financial_plan"):
            return self.financial_agent.format_as_markdown(results["financial_plan"])
        elif agent_name == "risk" and results.get("risk_analysis"):
            return self.risk_agent.format_as_markdown(results["risk_analysis"])
        return ""


# =============================================================================
# 단독 실행 테스트
# =============================================================================

if __name__ == "__main__":
    supervisor = PlanSupervisor(parallel=False)
    
    results = supervisor.run(
        service_overview="위치 기반 소셜 러닝 앱. 가까운 러닝 크루를 검색하고 함께 달릴 수 있는 서비스.",
        target_market="피트니스 앱 시장",
        target_users="20-40대 도시 거주 러닝 애호가",
        tech_stack="React Native + Node.js + PostgreSQL + AWS",
        development_scope="MVP 3개월"
    )
    
    print("\n" + "=" * 60)
    print("통합 결과:")
    print("=" * 60)
    print(results.get("integrated_context", ""))

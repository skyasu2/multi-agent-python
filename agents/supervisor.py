"""
PlanCraft - LangGraph 네이티브 Supervisor (개선된 버전)

베스트 프랙티스 적용:
1. Tool 기반 Handoff 패턴
2. 동적 라우팅 (LLM이 필요한 에이전트 결정)
3. create_react_agent 활용
4. 명시적 상태 관리

아키텍처:
    User Input
        ↓
    Supervisor (Router)
        ↓ (동적 결정)
    ┌───┴───┬───────┬───────┐
    ↓       ↓       ↓       ↓
  Market   BM   Financial  Risk
    ↓       ↓       ↓       ↓
    └───────┴───┬───┴───────┘
                ↓
    Result Integration
        ↓
    Writer Context
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.llm import get_llm
from utils.file_logger import FileLogger
from agents.specialist_tools import (
    get_specialist_tools,
    get_tool_descriptions_for_llm,
    analyze_market,
    analyze_business_model,
    analyze_financials,
    analyze_risks,
)

logger = FileLogger()


# =============================================================================
# Router Decision Schema
# =============================================================================

class RoutingDecision(BaseModel):
    """Supervisor 라우팅 결정"""
    required_analyses: List[Literal["market", "bm", "financial", "risk"]] = Field(
        description="필요한 분석 유형 목록"
    )
    reasoning: str = Field(
        description="라우팅 결정 이유"
    )
    priority_order: List[str] = Field(
        default_factory=list,
        description="실행 우선순위 (의존성 고려)"
    )


# =============================================================================
# LangGraph Native Supervisor
# =============================================================================

class NativeSupervisor:
    """
    LangGraph 네이티브 Supervisor
    
    Tool 기반 Handoff + 동적 라우팅 구현
    """
    
    ROUTER_SYSTEM_PROMPT = """당신은 기획서 분석 작업을 조율하는 Supervisor입니다.

사용자의 서비스 아이디어를 분석하여, 어떤 전문 분석이 필요한지 결정하세요.

## 사용 가능한 분석 유형

1. **market**: 시장 규모 분석 (TAM/SAM/SOM, 경쟁사)
   - 필요 시점: 시장 규모 언급, 경쟁사 분석 요청, 트렌드 분석 필요

2. **bm**: 비즈니스 모델 분석 (수익 모델, 가격 전략)
   - 필요 시점: 수익화 방법, 가격 정책, B2B/B2C 구분 필요

3. **financial**: 재무 계획 (투자비, BEP, 손익)
   - 필요 시점: 비용 추정, 매출 예측, 손익분기점 계산 필요

4. **risk**: 리스크 분석 (8가지 카테고리)
   - 필요 시점: 위험 요소 식별, 대응 전략 수립 필요

## 의존성 규칙

- `bm`은 `market` 결과를 참조할 수 있음 (경쟁사 정보)
- `financial`은 `bm` 결과를 참조함 (수익 모델)
- `risk`는 `bm` 결과를 참조함 (비즈니스 리스크)

## 판단 기준

1. **최소 분석 원칙**: 필요한 것만 선택 (불필요한 분석 배제)
2. **의존성 고려**: 선행 분석이 필요하면 함께 선택
3. **완전성**: 기획서에 필수인 항목은 반드시 포함

## 기본 규칙

- 기획서 작성이 목적이면: 보통 4개 모두 필요
- 간단한 아이디어 검증이면: market + bm만 필요
- 투자 유치용이면: 4개 모두 + financial 강조
"""

    def __init__(self, llm=None):
        self.llm = llm or get_llm(temperature=0.3)
        self.router_llm = self.llm.with_structured_output(RoutingDecision)
        
        # [NEW] Config 기반 에이전트 로드
        from agents.agent_config import (
            AGENT_REGISTRY,
            get_routing_prompt,
            resolve_execution_order,
        )
        self.agent_registry = AGENT_REGISTRY
        self.routing_prompt = get_routing_prompt()
        
        # 전문 에이전트 동적 초기화
        self.agents = {}
        self._init_agents()
        
        logger.info(f"[NativeSupervisor] 초기화 완료 (에이전트 {len(self.agents)}개)")
    
    def _init_agents(self):
        """Config 기반 에이전트 초기화"""
        # 에이전트 클래스 매핑
        agent_classes = {
            "market": "agents.specialists.market_agent.MarketAgent",
            "bm": "agents.specialists.bm_agent.BMAgent",
            "financial": "agents.specialists.financial_agent.FinancialAgent",
            "risk": "agents.specialists.risk_agent.RiskAgent",
        }
        
        for agent_id, spec in self.agent_registry.items():
            if agent_id in agent_classes:
                try:
                    # 동적 임포트
                    module_path, class_name = agent_classes[agent_id].rsplit(".", 1)
                    import importlib
                    module = importlib.import_module(module_path)
                    agent_class = getattr(module, class_name)
                    self.agents[agent_id] = agent_class(llm=self.llm)
                    logger.info(f"  - {spec.icon} {spec.name} 초기화 완료")
                except Exception as e:
                    logger.error(f"  - {agent_id} 초기화 실패: {e}")

    
    def decide_required_agents(
        self,
        service_overview: str,
        purpose: str = "기획서 작성"
    ) -> RoutingDecision:
        """
        동적 라우팅: 필요한 에이전트 결정
        
        Args:
            service_overview: 서비스 개요
            purpose: 분석 목적
            
        Returns:
            RoutingDecision: 필요한 분석 목록
        """
        logger.info("[NativeSupervisor] 🧭 라우팅 결정 시작...")
        
        messages = [
            SystemMessage(content=self.ROUTER_SYSTEM_PROMPT),
            HumanMessage(content=f"""## 서비스 개요
{service_overview}

## 분석 목적
{purpose}

위 내용을 바탕으로 어떤 분석이 필요한지 결정하세요.
""")
        ]
        
        try:
            decision = self.router_llm.invoke(messages)
            logger.info(f"[NativeSupervisor] 라우팅 결정: {decision.required_analyses}")
            logger.info(f"[NativeSupervisor] 결정 이유: {decision.reasoning}")
            return decision
        except Exception as e:
            logger.error(f"[NativeSupervisor] 라우팅 실패, 전체 분석 수행: {e}")
            return RoutingDecision(
                required_analyses=["market", "bm", "financial", "risk"],
                reasoning="라우팅 실패로 전체 분석 수행",
                priority_order=["market", "bm", "financial", "risk"]
            )
    
    def run(
        self,
        service_overview: str,
        target_market: str = "",
        target_users: str = "",
        tech_stack: str = "React Native + Node.js",
        development_scope: str = "MVP 3개월",
        web_search_results: List[Dict[str, Any]] = None,
        purpose: str = "기획서 작성",
        force_all: bool = False
    ) -> Dict[str, Any]:
        """
        전문 에이전트 실행 (동적 라우팅)
        
        Args:
            force_all: True면 모든 에이전트 강제 실행
        """
        logger.info("=" * 60)
        logger.info("[NativeSupervisor] 전문 에이전트 오케스트레이션 시작")
        logger.info(f"  서비스: {service_overview[:50]}...")
        logger.info("=" * 60)
        
        results = {}
        
        # 1. 동적 라우팅 (필요한 에이전트 결정)
        if force_all:
            required = ["market", "bm", "financial", "risk"]
            reasoning = "강제 전체 분석"
        else:
            decision = self.decide_required_agents(service_overview, purpose)
            required = decision.required_analyses
            reasoning = decision.reasoning
        
        results["_routing"] = {
            "required_analyses": required,
            "reasoning": reasoning
        }
        
        # 2. 의존성 기반 실행 순서 결정
        execution_order = self._resolve_dependencies(required)
        logger.info(f"[NativeSupervisor] 실행 순서: {execution_order}")
        
        # 3. 순차 실행 (의존성 있는 경우)
        for agent_type in execution_order:
            if agent_type == "market":
                logger.info("[NativeSupervisor] 📊 Market Agent 실행...")
                results["market_analysis"] = self.agents["market"].run(
                    service_overview=service_overview,
                    target_market=target_market,
                    web_search_results=web_search_results
                )
                logger.info("[NativeSupervisor] ✓ Market Agent 완료")
                
            elif agent_type == "bm":
                logger.info("[NativeSupervisor] 💰 BM Agent 실행...")
                competitors = results.get("market_analysis", {}).get("competitors", [])
                results["business_model"] = self.agents["bm"].run(
                    service_overview=service_overview,
                    target_users=target_users,
                    competitors=competitors
                )
                logger.info("[NativeSupervisor] ✓ BM Agent 완료")
                
            elif agent_type == "financial":
                logger.info("[NativeSupervisor] 📈 Financial Agent 실행...")
                bm = results.get("business_model", {})
                market = results.get("market_analysis", {})
                results["financial_plan"] = self.agents["financial"].run(
                    service_overview=service_overview,
                    business_model=bm,
                    market_analysis=market,
                    development_scope=development_scope
                )
                logger.info("[NativeSupervisor] ✓ Financial Agent 완료")
                
            elif agent_type == "risk":
                logger.info("[NativeSupervisor] ⚠️ Risk Agent 실행...")
                bm = results.get("business_model", {})
                results["risk_analysis"] = self.agents["risk"].run(
                    service_overview=service_overview,
                    business_model=bm,
                    tech_stack=tech_stack
                )
                logger.info("[NativeSupervisor] ✓ Risk Agent 완료")
        
        # 4. 결과 통합
        results["integrated_context"] = self._integrate_results(results)
        
        logger.info("[NativeSupervisor] 오케스트레이션 완료")
        return results
    
    def _resolve_dependencies(self, required: List[str]) -> List[str]:
        """의존성 기반 실행 순서 결정 (Config 기반)"""
        from agents.agent_config import resolve_execution_order
        return resolve_execution_order(required)
    
    def _integrate_results(self, results: Dict[str, Any]) -> str:
        """전문 에이전트 결과를 마크다운으로 통합"""
        integrated = "## 전문 에이전트 분석 결과\n\n"
        
        routing = results.get("_routing", {})
        if routing:
            integrated += f"**분석 범위**: {', '.join(routing.get('required_analyses', []))}\n"
            integrated += f"**결정 근거**: {routing.get('reasoning', '')}\n\n"
        
        if results.get("market_analysis"):
            integrated += "### 📊 시장 분석 (Market Agent)\n\n"
            integrated += self.agents["market"].format_as_markdown(results["market_analysis"])
            integrated += "\n"
        
        if results.get("business_model"):
            integrated += "### 💰 비즈니스 모델 (BM Agent)\n\n"
            integrated += self.agents["bm"].format_as_markdown(results["business_model"])
            integrated += "\n"
        
        if results.get("financial_plan"):
            integrated += "### 📈 재무 계획 (Financial Agent)\n\n"
            integrated += self.agents["financial"].format_as_markdown(results["financial_plan"])
            integrated += "\n"
        
        if results.get("risk_analysis"):
            integrated += "### ⚠️ 리스크 분석 (Risk Agent)\n\n"
            integrated += self.agents["risk"].format_as_markdown(results["risk_analysis"])
            integrated += "\n"
        
        return integrated


# =============================================================================
# 기존 PlanSupervisor 대체
# =============================================================================

# 하위 호환성을 위해 alias 제공
PlanSupervisor = NativeSupervisor


# =============================================================================
# 단독 실행 테스트
# =============================================================================

if __name__ == "__main__":
    supervisor = NativeSupervisor()
    
    # 동적 라우팅 테스트
    decision = supervisor.decide_required_agents(
        service_overview="위치 기반 소셜 러닝 앱",
        purpose="투자 유치용 기획서"
    )
    print(f"필요한 분석: {decision.required_analyses}")
    print(f"이유: {decision.reasoning}")

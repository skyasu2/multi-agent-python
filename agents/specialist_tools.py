"""
PlanCraft - LangGraph 네이티브 전문 에이전트 Tool 정의

각 전문 에이전트를 Tool로 정의하여 Supervisor가 호출할 수 있도록 합니다.
Tool 기반 Handoff 패턴을 구현합니다.
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool
from pydantic import BaseModel, Field


# =============================================================================
# Tool Input Schemas
# =============================================================================

class MarketAnalysisInput(BaseModel):
    """시장 분석 Tool 입력"""
    service_overview: str = Field(description="서비스 개요 및 핵심 가치")
    target_market: str = Field(description="타겟 시장 (예: 피트니스 앱)")
    region: str = Field(default="국내", description="분석 지역 (국내/글로벌)")


class BMAnalysisInput(BaseModel):
    """비즈니스 모델 분석 Tool 입력"""
    service_overview: str = Field(description="서비스 개요")
    target_users: str = Field(description="타겟 사용자 (예: 20-30대 직장인)")
    competitors: Optional[List[str]] = Field(default=None, description="경쟁사 목록")


class FinancialAnalysisInput(BaseModel):
    """재무 분석 Tool 입력"""
    service_overview: str = Field(description="서비스 개요")
    revenue_model: str = Field(description="수익 모델 (예: 구독, 광고)")
    development_period: str = Field(default="3개월", description="개발 기간")
    team_size: int = Field(default=3, description="팀 규모")


class RiskAnalysisInput(BaseModel):
    """리스크 분석 Tool 입력"""
    service_overview: str = Field(description="서비스 개요")
    tech_stack: str = Field(default="", description="기술 스택")
    business_model: str = Field(default="", description="비즈니스 모델")


# =============================================================================
# 전문 에이전트 Tools
# =============================================================================

@tool(args_schema=MarketAnalysisInput)
def analyze_market(
    service_overview: str,
    target_market: str,
    region: str = "국내"
) -> Dict[str, Any]:
    """
    시장 분석을 수행합니다.
    TAM/SAM/SOM 3단계 분석과 경쟁사 분석을 제공합니다.
    시장 규모, 성장률, 트렌드 정보가 필요할 때 사용하세요.
    """
    from agents.specialists.market_agent import MarketAgent
    
    agent = MarketAgent()
    result = agent.run(
        service_overview=service_overview,
        target_market=target_market,
        web_search_results=None
    )
    return {
        "tool": "market_analysis",
        "status": "success",
        "data": result
    }


@tool(args_schema=BMAnalysisInput)
def analyze_business_model(
    service_overview: str,
    target_users: str,
    competitors: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    비즈니스 모델을 분석합니다.
    수익 모델 다각화, 가격 전략, B2B/B2C 계층을 설계합니다.
    수익 창출 방법이나 가격 정책이 필요할 때 사용하세요.
    """
    from agents.specialists.bm_agent import BMAgent
    
    agent = BMAgent()
    competitors_data = [{"name": c} for c in competitors] if competitors else None
    result = agent.run(
        service_overview=service_overview,
        target_users=target_users,
        competitors=competitors_data
    )
    return {
        "tool": "business_model",
        "status": "success",
        "data": result
    }


@tool(args_schema=FinancialAnalysisInput)
def analyze_financials(
    service_overview: str,
    revenue_model: str,
    development_period: str = "3개월",
    team_size: int = 3
) -> Dict[str, Any]:
    """
    재무 계획을 수립합니다.
    초기 투자비, 월별 손익, BEP(손익분기점)를 계산합니다.
    비용 추정이나 수익 예측이 필요할 때 사용하세요.
    """
    from agents.specialists.financial_agent import FinancialAgent
    
    agent = FinancialAgent()
    result = agent.run(
        service_overview=service_overview,
        business_model={"primary_model": {"name": revenue_model}},
        market_analysis={},
        development_scope=f"MVP {development_period}"
    )
    return {
        "tool": "financial_plan",
        "status": "success",
        "data": result
    }


@tool(args_schema=RiskAnalysisInput)
def analyze_risks(
    service_overview: str,
    tech_stack: str = "",
    business_model: str = ""
) -> Dict[str, Any]:
    """
    리스크를 분석합니다.
    기술/비즈니스/운영/규제/경쟁/재무/인력/외부 8가지 카테고리로 분석합니다.
    위험 요소나 대응 전략이 필요할 때 사용하세요.
    """
    from agents.specialists.risk_agent import RiskAgent
    
    agent = RiskAgent()
    result = agent.run(
        service_overview=service_overview,
        business_model={"type": business_model},
        tech_stack=tech_stack
    )
    return {
        "tool": "risk_analysis",
        "status": "success",
        "data": result
    }


# =============================================================================
# Tool 목록
# =============================================================================

SPECIALIST_TOOLS = [
    analyze_market,
    analyze_business_model,
    analyze_financials,
    analyze_risks,
]


def get_specialist_tools():
    """전문 에이전트 Tool 목록 반환"""
    return SPECIALIST_TOOLS


# =============================================================================
# Tool 설명 (Supervisor용)
# =============================================================================

TOOL_DESCRIPTIONS = {
    "analyze_market": "시장 규모(TAM/SAM/SOM), 경쟁사 분석, 트렌드가 필요할 때",
    "analyze_business_model": "수익 모델, 가격 전략, B2B/B2C 계층이 필요할 때",
    "analyze_financials": "초기 투자비, 월별 손익, BEP 계산이 필요할 때",
    "analyze_risks": "리스크 분석, 대응 전략이 필요할 때",
}


def get_tool_descriptions_for_llm() -> str:
    """LLM에게 제공할 Tool 설명 문자열"""
    lines = ["사용 가능한 전문 분석 도구:"]
    for name, desc in TOOL_DESCRIPTIONS.items():
        lines.append(f"- {name}: {desc}")
    return "\n".join(lines)

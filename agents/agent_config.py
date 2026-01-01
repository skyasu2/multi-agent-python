"""
PlanCraft - Multi-Agent 설정 모듈

에이전트 스펙, 의존성 그래프, 실행 정책을 코드에서 분리하여
유지보수성과 확장성을 향상시킵니다.

사용법:
    from agents.agent_config import AGENT_REGISTRY, get_dependency_graph
    
    for agent in AGENT_REGISTRY.values():
        print(f"{agent.name}: {agent.description}")
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


# =============================================================================
# 에이전트 실행 정책
# =============================================================================

class ExecutionMode(str, Enum):
    """에이전트 실행 모드"""
    REQUIRED = "required"      # 항상 실행
    CONDITIONAL = "conditional"  # LLM 결정에 따라
    OPTIONAL = "optional"      # 사용자가 명시적으로 요청 시만


class ApprovalMode(str, Enum):
    """결과 승인 모드"""
    AUTO = "auto"              # 자동 진행 (승인 불필요)
    REVIEW = "review"          # 사용자 검토 후 진행
    APPROVAL = "approval"      # 명시적 승인 필요


# =============================================================================
# 에이전트 스펙 정의
# =============================================================================

@dataclass
class AgentSpec:
    """에이전트 명세"""
    id: str                     # 고유 ID (market, bm, financial, risk)
    name: str                   # UI 표시명
    icon: str                   # 이모지 아이콘
    description: str            # 설명
    
    # 실행 정책
    execution_mode: ExecutionMode = ExecutionMode.CONDITIONAL
    approval_mode: ApprovalMode = ApprovalMode.AUTO
    
    # 의존성
    depends_on: List[str] = field(default_factory=list)
    provides: List[str] = field(default_factory=list)  # 다른 에이전트에게 제공하는 데이터
    
    # 라우팅 키워드 (LLM 라우팅 시 참조)
    routing_keywords: List[str] = field(default_factory=list)
    
    # 추가 메타데이터
    timeout_seconds: int = 60
    retry_count: int = 2
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "description": self.description,
            "execution_mode": self.execution_mode.value,
            "approval_mode": self.approval_mode.value,
            "depends_on": self.depends_on,
            "provides": self.provides,
            "routing_keywords": self.routing_keywords,
        }


# =============================================================================
# 에이전트 레지스트리 (핵심 설정)
# =============================================================================

AGENT_REGISTRY: Dict[str, AgentSpec] = {
    "market": AgentSpec(
        id="market",
        name="시장 분석",
        icon="📊",
        description="TAM/SAM/SOM 3단계 시장 규모 분석, 경쟁사 실명 분석, 트렌드 파악",
        execution_mode=ExecutionMode.CONDITIONAL,
        approval_mode=ApprovalMode.AUTO,
        depends_on=[],
        provides=["tam", "sam", "som", "competitors", "trends"],
        routing_keywords=["시장", "규모", "경쟁사", "트렌드", "TAM", "SAM", "SOM", "분석"],
        timeout_seconds=90,
    ),
    
    "bm": AgentSpec(
        id="bm",
        name="비즈니스 모델",
        icon="💰",
        description="수익 모델 다각화, 가격 전략 수립, B2B/B2C 계층 설계",
        execution_mode=ExecutionMode.CONDITIONAL,
        approval_mode=ApprovalMode.AUTO,
        depends_on=[],  # market 참조 가능하지만 필수 아님
        provides=["revenue_model", "pricing", "moat"],
        routing_keywords=["수익", "가격", "BM", "비즈니스", "모델", "구독", "광고", "B2B", "B2C"],
        timeout_seconds=60,
    ),
    
    "financial": AgentSpec(
        id="financial",
        name="재무 계획",
        icon="📈",
        description="초기 투자비 산출, 월별 손익 시뮬레이션, BEP 계산, 3시나리오 분석",
        execution_mode=ExecutionMode.CONDITIONAL,
        approval_mode=ApprovalMode.AUTO,
        depends_on=["bm"],  # BM 결과 필수
        provides=["investment", "monthly_pl", "bep", "scenarios"],
        routing_keywords=["재무", "투자", "비용", "매출", "BEP", "손익", "예산", "자금"],
        timeout_seconds=90,
    ),
    
    "risk": AgentSpec(
        id="risk",
        name="리스크 분석",
        icon="⚠️",
        description="8가지 리스크 카테고리 분석, 위험 점수 정량화, 대응 전략 수립",
        execution_mode=ExecutionMode.CONDITIONAL,
        approval_mode=ApprovalMode.AUTO,
        depends_on=["bm"],  # BM 결과 참조
        provides=["risks", "mitigation", "kri"],
        routing_keywords=["리스크", "위험", "대응", "문제", "장애", "규제"],
        timeout_seconds=60,
    ),
}


# =============================================================================
# 의존성 그래프 유틸리티
# =============================================================================

def get_dependency_graph() -> Dict[str, List[str]]:
    """의존성 그래프 반환 (에이전트ID -> 의존하는 에이전트ID 목록)"""
    return {
        agent_id: spec.depends_on
        for agent_id, spec in AGENT_REGISTRY.items()
    }


def resolve_execution_order(required_agents: List[str]) -> List[str]:
    """
    의존성 기반 실행 순서 결정 (위상 정렬)
    
    Args:
        required_agents: 실행이 필요한 에이전트 ID 목록
        
    Returns:
        실행 순서대로 정렬된 에이전트 ID 목록
    """
    if not required_agents:
        return []
    
    graph = get_dependency_graph()
    
    # 의존성 충족 여부 확인 및 누락된 의존성 추가
    all_required = set(required_agents)
    for agent_id in list(all_required):
        for dep in graph.get(agent_id, []):
            if dep not in all_required:
                all_required.add(dep)
    
    # 위상 정렬
    in_degree = {agent: 0 for agent in all_required}
    for agent in all_required:
        for dep in graph.get(agent, []):
            if dep in all_required:
                in_degree[agent] += 1
    
    # 진입 차수 0인 노드부터 시작
    queue = [agent for agent, degree in in_degree.items() if degree == 0]
    result = []
    
    while queue:
        # 우선순위: market > bm > financial > risk
        priority = ["market", "bm", "financial", "risk"]
        queue.sort(key=lambda x: priority.index(x) if x in priority else 99)
        
        current = queue.pop(0)
        result.append(current)
        
        # 진입 차수 감소
        for agent in all_required:
            if current in graph.get(agent, []):
                in_degree[agent] -= 1
                if in_degree[agent] == 0:
                    queue.append(agent)
    
    return result


def get_agents_for_purpose(purpose: str) -> List[str]:
    """
    목적에 따른 권장 에이전트 목록 반환
    
    Args:
        purpose: 분석 목적 (기획서/투자유치/아이디어검증 등)
    """
    purpose_lower = purpose.lower()
    
    if "투자" in purpose_lower:
        return ["market", "bm", "financial", "risk"]
    elif "아이디어" in purpose_lower or "검증" in purpose_lower:
        return ["market", "bm"]
    elif "기획서" in purpose_lower:
        return ["market", "bm", "financial", "risk"]
    else:
        # 기본값: 모두
        return list(AGENT_REGISTRY.keys())


def get_routing_prompt() -> str:
    """LLM 라우팅용 에이전트 설명 프롬프트 생성"""
    lines = ["## 사용 가능한 전문 에이전트", ""]
    
    for agent_id, spec in AGENT_REGISTRY.items():
        lines.append(f"### {spec.icon} {spec.name} (`{agent_id}`)")
        lines.append(f"- **설명**: {spec.description}")
        lines.append(f"- **키워드**: {', '.join(spec.routing_keywords)}")
        if spec.depends_on:
            lines.append(f"- **의존성**: {', '.join(spec.depends_on)}")
        lines.append("")
    
    return "\n".join(lines)


# =============================================================================
# 에이전트 등록 API (런타임 확장용)
# =============================================================================

def register_agent(spec: AgentSpec) -> None:
    """새 에이전트 등록 (런타임)"""
    AGENT_REGISTRY[spec.id] = spec


def unregister_agent(agent_id: str) -> bool:
    """에이전트 등록 해제"""
    if agent_id in AGENT_REGISTRY:
        del AGENT_REGISTRY[agent_id]
        return True
    return False


def get_agent_spec(agent_id: str) -> Optional[AgentSpec]:
    """에이전트 스펙 조회"""
    return AGENT_REGISTRY.get(agent_id)


# =============================================================================
# 승인 정책 유틸리티
# =============================================================================

def requires_approval(agent_id: str) -> bool:
    """에이전트 결과가 사용자 승인을 필요로 하는지 확인"""
    spec = AGENT_REGISTRY.get(agent_id)
    if not spec:
        return False
    return spec.approval_mode in [ApprovalMode.APPROVAL, ApprovalMode.REVIEW]


def set_approval_mode(agent_id: str, mode: ApprovalMode) -> bool:
    """에이전트 승인 모드 변경"""
    spec = AGENT_REGISTRY.get(agent_id)
    if spec:
        spec.approval_mode = mode
        return True
    return False


# =============================================================================
# 디버깅/관리 유틸리티
# =============================================================================

def print_agent_summary():
    """에이전트 요약 출력 (디버깅용)"""
    print("=" * 60)
    print("PlanCraft Agent Registry")
    print("=" * 60)
    
    for agent_id, spec in AGENT_REGISTRY.items():
        deps = f" (deps: {spec.depends_on})" if spec.depends_on else ""
        print(f"{spec.icon} {spec.name} [{agent_id}]{deps}")
    
    print("=" * 60)
    print(f"Execution Order (all): {resolve_execution_order(list(AGENT_REGISTRY.keys()))}")


if __name__ == "__main__":
    print_agent_summary()
    print("\n" + get_routing_prompt())

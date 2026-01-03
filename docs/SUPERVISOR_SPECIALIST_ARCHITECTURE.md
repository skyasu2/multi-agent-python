# Supervisor vs Specialist Agent 아키텍처

> **문서 버전**: 1.0
> **최종 업데이트**: 2026-01-03
> **목적**: PlanCraft의 Multi-Agent 아키텍처 설명

---

## 1. Supervisor의 역할

```
┌─────────────────────────────────────────────────────────────┐
│                     SUPERVISOR (총괄 지휘관)                  │
├─────────────────────────────────────────────────────────────┤
│  1. 라우팅 결정    - 어떤 에이전트를 실행할지 결정            │
│  2. 병렬 실행      - 의존성 없는 에이전트는 동시 실행          │
│  3. 결과 통합      - 각 에이전트 결과를 하나로 합침            │
│  4. 실행 통계      - retry/fail 카운터, 소요시간 추적          │
└─────────────────────────────────────────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         ↓                    ↓                    ↓
    ┌─────────┐          ┌─────────┐          ┌─────────┐
    │ Market  │          │   BM    │          │  Tech   │
    │ Agent   │          │  Agent  │          │  Agent  │
    └─────────┘          └─────────┘          └─────────┘
```

### Supervisor 핵심 기능

| 기능 | 설명 |
|:---|:---|
| **결정론적 라우팅** | 키워드 기반으로 필요한 에이전트 결정 (LLM 호출 최소화) |
| **DAG 기반 실행** | 의존성 그래프에 따라 실행 순서 결정 |
| **병렬 실행** | `ThreadPoolExecutor`로 독립적인 에이전트 동시 실행 |
| **Fallback 처리** | 에이전트 실패 시 기본값으로 대체 |

### 결정론적 라우팅 코드 예시

```python
# agents/supervisor.py
TECH_KEYWORDS = frozenset(["앱", "웹", "플랫폼", "ai", "클라우드", ...])
CONTENT_KEYWORDS = frozenset(["마케팅", "sns", "브랜드", "유튜브", ...])

def detect_required_agents(service_overview: str, purpose: str):
    agents = ["market", "bm", "financial", "risk"]  # 기본 4개

    if any(kw in service_overview.lower() for kw in TECH_KEYWORDS):
        agents.append("tech")       # 기술 키워드 → Tech Agent 추가

    if any(kw in service_overview.lower() for kw in CONTENT_KEYWORDS):
        agents.append("content")    # 콘텐츠 키워드 → Content Agent 추가

    return agents
```

---

## 2. Specialist Agent의 역할

```
┌──────────────────────────────────────────────────────────────┐
│                    SPECIALIST AGENTS (전문가)                 │
├──────────────────────────────────────────────────────────────┤
│  각 도메인의 "딥 다이브" 분석을 수행하는 전문 에이전트         │
│  독립적으로 동작하며, 자신만의 출력 스키마를 가짐              │
└──────────────────────────────────────────────────────────────┘
```

### Specialist Agent 목록

| Agent | 전문 영역 | 출력 스키마 |
|:---|:---|:---|
| **MarketAgent** | TAM/SAM/SOM, 경쟁사 분석 | `MarketAnalysis` |
| **BMAgent** | 수익 모델, 가격 정책 | `BusinessModel` |
| **FinancialAgent** | 재무 예측, 투자 계획 | `FinancialPlan` |
| **RiskAgent** | 리스크 분석, 대응 방안 | `RiskAnalysis` |
| **TechAgent** | 기술 스택, 아키텍처 | `TechArchitecture` |
| **ContentAgent** | 콘텐츠/마케팅 전략 | `ContentStrategy` |

### 출력 스키마 예시 (MarketAgent)

```python
# agents/specialists/market_agent.py
class MarketAnalysis(BaseModel):
    tam: MarketSize           # 전체 시장
    sam: MarketSize           # 접근 가능 시장
    som: MarketSize           # 획득 가능 시장
    competitors: List[Competitor]  # 경쟁사 (최소 3개)
    trends: List[str]         # 시장 트렌드
    opportunities: List[str]  # 시장 기회
```

---

## 3. 일반 Agent vs Specialist Agent 차이

| 구분 | 일반 Agent | Specialist Agent |
|:---|:---|:---|
| **역할** | 워크플로우 진행 (분석→구조→작성) | 특정 도메인 심층 분석 |
| **실행 시점** | 항상 순차적으로 실행 | 조건부 병렬 실행 |
| **출력** | State에 직접 업데이트 | 구조화된 분석 결과 반환 |
| **의존성** | 이전 단계에 의존 | 서로 독립적 |
| **LLM 프롬프트** | 범용적 | 도메인 특화 (전문 용어, 포맷) |

### 워크플로우 비교

```
[일반 Agent 흐름] - 순차적
Analyzer → Structurer → Writer → Reviewer → Formatter
   ↓           ↓          ↓         ↓           ↓
 분석 →      구조 →     작성 →    검토 →      포맷

[Specialist Agent 흐름] - 병렬적
                    ┌── MarketAgent ──┐
                    ├── BMAgent ──────┤
Supervisor 라우팅 → ├── FinancialAgent ┼→ 결과 통합 → Writer
                    ├── RiskAgent ────┤
                    ├── TechAgent ────┤
                    └── ContentAgent ─┘
```

---

## 4. Specialist Agent의 장점

### 4.1 성능 향상 (병렬 실행)

```python
# agents/supervisor.py - 병렬 실행
def execute_in_parallel(agents: List[str], context: Dict) -> Dict:
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = {
            executor.submit(run_agent, agent_id, context): agent_id
            for agent_id in agents
        }
        results = {}
        for future in as_completed(futures):
            agent_id = futures[future]
            results[agent_id] = future.result()
    return results
```

**효과**: 6개 에이전트를 순차 실행하면 6분 → 병렬 실행하면 **1분**

### 4.2 전문성 (도메인 특화 프롬프트)

```python
# MarketAgent 프롬프트 (일부)
"""
당신은 시장 분석 전문가입니다.

## 필수 분석 항목
1. TAM (Total Addressable Market)
   - 전체 시장 규모 (USD + KRW)
   - 신뢰할 수 있는 출처 명시

2. SAM (Serviceable Addressable Market)
   - 실제 접근 가능한 시장

3. 경쟁사 분석
   - 실제 기업명 사용 (가명 금지)
   - 강점/약점/차별화 포인트
"""
```

### 4.3 확장성 (OCP 원칙)

```python
# agents/agent_config.py - 새 에이전트 추가가 쉬움
AGENT_REGISTRY = {
    "market": AgentSpec(
        id="market",
        name="시장 분석",
        class_path="agents.specialists.market_agent.MarketAgent",
        routing_keywords=["시장", "tam", "경쟁사"],
    ),
    # 새 에이전트 추가: ESG Agent
    "esg": AgentSpec(
        id="esg",
        name="ESG 분석",
        class_path="agents.specialists.esg_agent.ESGAgent",
        routing_keywords=["esg", "탄소", "지속가능"],
    ),
}
```

### 4.4 품질 보장 (Pydantic 스키마)

```python
# 타입 안전한 출력
class Competitor(BaseModel):
    name: str                    # 필수: 경쟁사명
    strengths: List[str]         # 필수: 강점
    weaknesses: List[str]        # 필수: 약점
    our_differentiation: str     # 필수: 차별점

# LLM이 스키마에 맞지 않는 응답을 하면 자동 검증 실패
```

### 4.5 독립적 테스트/유지보수

```python
# 각 Specialist는 독립적으로 테스트 가능
def test_market_agent():
    agent = MarketAgent()
    result = agent.run(
        service_overview="AI 헬스케어 앱",
        target_market="한국 20-40대"
    )
    assert "tam" in result
    assert "competitors" in result
    assert len(result["competitors"]) >= 3
```

---

## 5. 요약 비교표

| 특성 | 일반 Agent | Specialist Agent |
|:---:|:---:|:---:|
| 실행 방식 | 순차 | **병렬** |
| 의존성 | 있음 | **없음** |
| 프롬프트 | 범용 | **도메인 특화** |
| 출력 | 자유 형식 | **Pydantic 스키마** |
| 확장성 | 어려움 | **Registry 추가만** |
| 테스트 | 통합 테스트 필요 | **단위 테스트 가능** |
| 재사용 | 어려움 | **독립 모듈** |

---

## 6. 핵심 메시지

> **"Specialist Agent는 마이크로서비스 아키텍처의 AI 버전"**

- 각 에이전트가 **단일 책임**을 가짐 (SRP)
- **병렬 실행**으로 성능 향상
- **스키마 검증**으로 품질 보장
- **독립적 확장/테스트** 가능

---

## 7. 관련 파일

| 파일 | 설명 |
|:---|:---|
| `agents/supervisor.py` | Supervisor 구현 (라우팅, 병렬 실행) |
| `agents/agent_config.py` | Agent Registry, DAG 설정 |
| `agents/specialists/*.py` | 6개 Specialist Agent 구현 |
| `graph/workflow.py` | LangGraph 워크플로우 정의 |

---

## 8. 참고 자료

- [LangGraph Multi-Agent 공식 문서](https://langchain-ai.github.io/langgraph/concepts/multi_agent/)
- [Supervisor 패턴](https://langchain-ai.github.io/langgraph/tutorials/multi_agent/agent_supervisor/)
- [Tool-based Handoff 패턴](https://langchain-ai.github.io/langgraph/concepts/multi_agent/#handoffs)

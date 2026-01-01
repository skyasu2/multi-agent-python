# PlanCraft Multi-Agent Supervisor 아키텍처
# =========================================

## 개요

기존 단일 파이프라인 구조를 **전문 에이전트 협업** 구조로 재설계합니다.
각 전문 에이전트는 자신의 영역에 집중하고, Supervisor가 협업을 조율합니다.

## 아키텍처 다이어그램

```
                      ┌────────────────────────┐
                      │   Plan Supervisor      │
                      │  (오케스트레이터)       │
                      └───────────┬────────────┘
                                  │
        ┌───────────┬─────────────┼─────────────┬───────────┐
        ▼           ▼             ▼             ▼           ▼
┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
│  Market   │ │  BizModel │ │ Financial │ │   Risk    │ │  Writer   │
│  Agent    │ │   Agent   │ │   Agent   │ │   Agent   │ │   Agent   │
│           │ │           │ │           │ │           │ │           │
│ TAM/SAM   │ │ 수익모델  │ │ 재무계획  │ │ 리스크    │ │ 기획서    │
│ 경쟁사    │ │ 가격전략  │ │ BEP계산   │ │ 검증      │ │ 작성      │
│ 트렌드    │ │ B2B/B2C   │ │ 시나리오  │ │           │ │ 최종통합  │
└───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘
```

## 에이전트 역할 정의

### 1. Plan Supervisor (오케스트레이터)
- 사용자 요청 분석
- 필요한 전문 에이전트 호출 결정
- 에이전트 결과 통합 조율
- 최종 품질 검증

### 2. Market Analysis Agent (시장 분석)
- **입력**: 사용자 아이디어, 웹 검색 결과
- **출력**: 
  - TAM/SAM/SOM 3단계 분석
  - 경쟁사 상세 분석 (실명, 특징, 차별점)
  - 시장 트렌드 및 기회

### 3. Business Model Agent (비즈니스 모델)
- **입력**: 서비스 개요, 타겟 사용자
- **출력**:
  - 수익 모델 5개 후보 + 적합성 분석
  - 가격 전략 (경쟁사 벤치마킹 기반)
  - B2B/B2C 계층 구조

### 4. Financial Agent (재무 시뮬레이션)
- **입력**: BM, TAM/SAM/SOM, 개발 규모
- **출력**:
  - 초기 투자 비용 상세 분해
  - 월별 매출/비용 시뮬레이션
  - BEP 계산 (공식 포함)
  - 낙관/기본/보수 3시나리오

### 5. Risk Agent (리스크 검증)
- **입력**: 기획서 전체 내용
- **출력**:
  - 8가지 리스크 카테고리 분석
  - 발생확률 × 영향도 정량화
  - 구체적 대응 Action Items

### 6. Writer Agent (통합 작성)
- **입력**: 모든 에이전트의 분석 결과
- **출력**:
  - 10개 섹션 구조화된 기획서
  - 표/차트 포함 완성본

## 워크플로우 시퀀스

```
[START]
    ↓
[Analyzer] → 요구사항 분석 + 질문 생성 (기존)
    ↓
[HITL: 옵션 선택]
    ↓
[Supervisor] → 전문 에이전트 호출 결정
    ↓
┌───────────────────────────────────────┐
│ [Market Agent]  → TAM/SAM/SOM        │
│ [BizModel Agent] → 수익 모델          │  (병렬 실행)
│ [Financial Agent] → 재무 계획        │
│ [Risk Agent] → 리스크 분석            │
└───────────────────────────────────────┘
    ↓
[Writer Agent] → 전체 통합 작성
    ↓
[Reviewer] → 품질 검증 (기존)
    ↓
[Refiner] → 개선 (필요시)
    ↓
[Formatter] → 최종 출력
    ↓
[END]
```

## 상태(State) 확장

```python
class MultiAgentState(TypedDict):
    # 기존 필드 유지
    user_input: str
    analysis: dict
    structure: dict
    draft: str
    final_output: str
    
    # 새 필드: 전문 에이전트 결과
    market_analysis: dict      # 시장 분석 결과
    business_model: dict       # BM 분석 결과
    financial_plan: dict       # 재무 계획 결과
    risk_analysis: dict        # 리스크 분석 결과
    
    # Supervisor 상태
    agent_sequence: List[str]  # 호출할 에이전트 순서
    current_agent: str         # 현재 실행 중인 에이전트
    agent_outputs: dict        # 각 에이전트 출력 모음
```

## 파일 구조

```
agents/
├── __init__.py
├── analyzer.py          # (기존)
├── structurer.py        # (기존 - 역할 축소)
├── writer.py            # (기존 - 통합 역할 강화)
├── reviewer.py          # (기존)
├── refiner.py           # (기존)
├── formatter.py         # (기존)
│
├── specialists/         # 신규: 전문 에이전트
│   ├── __init__.py
│   ├── market_agent.py      # 시장 분석
│   ├── bm_agent.py          # 비즈니스 모델
│   ├── financial_agent.py   # 재무 시뮬레이션
│   └── risk_agent.py        # 리스크 검증
│
└── supervisor.py        # 신규: 오케스트레이터

prompts/
├── specialist_prompts/  # 신규: 전문 에이전트 프롬프트
│   ├── market_prompt.py
│   ├── bm_prompt.py
│   ├── financial_prompt.py
│   └── risk_prompt.py
```

## 구현 우선순위

1. **Phase 1**: 상태(State) 확장 + Supervisor 기본 구조
2. **Phase 2**: Financial Agent (가장 약한 부분)
3. **Phase 3**: Market Agent (TAM/SAM/SOM)
4. **Phase 4**: Risk Agent
5. **Phase 5**: BM Agent
6. **Phase 6**: Writer 통합 로직 강화

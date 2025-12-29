# Multi-Agent 개선 계획서

> 📅 작성일: 2025-12-29
> 🎯 목표: "파이프라인"에서 "진짜 Multi-Agent"로 업그레이드

---

## 📊 현재 상태 vs 목표

| 항목 | 현재 | 목표 | 개선 효과 |
|------|------|------|-----------|
| 동적 라우팅 | 제한적 | 확장 | Agent 자율성 ↑ |
| 병렬 실행 | 순차 | 병렬 | 성능 ↑ (30%+) |
| 피드백 루프 | 단방향 | 양방향 | 품질 ↑ |
| Supervisor | 없음 | 도입 | 유연성 ↑ |

---

## 🔧 개선 항목

### Phase 1: 동적 라우팅 확장 (⭐ 우선순위 1)

**목표**: Reviewer 결과에 따라 Analyzer로 복귀 가능

**현재 흐름**:
```
Analyzer → Structurer → Writer → Reviewer → Refiner → Formatter
                                     ↓
                              (점수 무관하게 Refiner로)
```

**개선 후 흐름**:
```
Analyzer → Structurer → Writer → Reviewer ─┬─ score < 5 → Analyzer (재분석)
                                           ├─ score 5~8 → Refiner (개선)
                                           └─ score ≥ 9 → Formatter (완료)
```

**수정 파일**:
- `graph/workflow.py`: `should_refine_or_restart()` 함수 추가
- `graph/state.py`: (필요시) `restart_count` 필드 추가

**예상 코드**:
```python
def should_refine_or_restart(state: PlanCraftState) -> str:
    review = state.get("review", {})
    score = review.get("overall_score", 0)
    verdict = review.get("verdict", "")
    restart_count = state.get("restart_count", 0)
    
    # 무한 루프 방지
    if restart_count >= 2:
        return "refine"
    
    if score < 5 or verdict == "FAIL":
        return "restart"  # Analyzer로 복귀
    elif score < 9:
        return "refine"   # Refiner로
    else:
        return "complete" # Formatter로

workflow.add_conditional_edges(
    "review",
    should_refine_or_restart,
    {
        "restart": "analyze",
        "refine": "refine",
        "complete": "format"
    }
)
```

**예상 소요 시간**: 30분

---

### Phase 2: 병렬 컨텍스트 수집 (⭐ 우선순위 2)

**목표**: RAG 검색과 웹 검색 동시 실행

**현재 흐름**:
```
rag_retrieve → web_fetch → analyze (순차: ~5초)
```

**개선 후 흐름**:
```
        ┌─ rag_retrieve ─┐
START ──┤                ├──→ merge → analyze (병렬: ~3초)
        └─ web_fetch ────┘
```

**수정 파일**:
- `graph/subgraphs.py`: `create_parallel_context_subgraph()` 함수 추가
- `graph/workflow.py`: 기존 순차 실행을 병렬 서브그래프로 교체

**예상 코드**:
```python
def create_parallel_context_subgraph():
    subgraph = StateGraph(PlanCraftState)
    
    subgraph.add_node("rag", retrieve_context)
    subgraph.add_node("web", fetch_web_context)
    subgraph.add_node("merge", merge_context)
    
    # 병렬 분기
    subgraph.add_edge(START, "rag")
    subgraph.add_edge(START, "web")
    
    # 결과 합치기
    subgraph.add_edge("rag", "merge")
    subgraph.add_edge("web", "merge")
    subgraph.add_edge("merge", END)
    
    return subgraph

def merge_context(state: PlanCraftState) -> PlanCraftState:
    """RAG와 웹 결과를 합침 (이미 State에 있음)"""
    return state
```

**예상 소요 시간**: 20분

---

### Phase 3: Agent 피드백 루프 (💡 선택)

**목표**: Reviewer 피드백을 Writer에게 직접 전달

**현재 흐름**:
```
Writer → Reviewer → Refiner (Refiner가 전체 수정)
```

**개선 후 흐름**:
```
Writer → Reviewer ─┬─ 특정 섹션만 수정 필요 → Writer (해당 섹션만)
                   └─ 전체 수정 필요 → Refiner
```

**수정 파일**:
- `utils/schemas.py`: `ReviewResult`에 `sections_to_revise` 필드 추가
- `prompts/reviewer_prompt.py`: 섹션별 피드백 요청 추가
- `graph/workflow.py`: Writer 재호출 분기 추가

**예상 소요 시간**: 45분

---

### Phase 4: Supervisor 패턴 도입 (💡 선택)

**목표**: 중앙 Supervisor가 다음 Agent 결정

**현재**:
```
고정된 순서 (하드코딩된 edge)
```

**개선**:
```
Supervisor → (상태 분석) → 다음 Agent 결정
```

**수정 파일**:
- `agents/supervisor.py`: 신규 생성
- `prompts/supervisor_prompt.py`: 신규 생성
- `graph/workflow.py`: Supervisor 노드 추가

**예상 소요 시간**: 1시간

---

## 📋 구현 우선순위

| 순위 | 항목 | 난이도 | 시간 | 효과 | 추천 |
|------|------|--------|------|------|------|
| 1 | 동적 라우팅 확장 | 🟢 쉬움 | 30분 | ⭐⭐⭐ | **필수** |
| 2 | 병렬 컨텍스트 | 🟢 쉬움 | 20분 | ⭐⭐ | **권장** |
| 3 | 피드백 루프 | 🟡 중간 | 45분 | ⭐⭐ | 선택 |
| 4 | Supervisor | 🟡 중간 | 1시간 | ⭐⭐⭐ | 선택 |

---

## ⏱️ 예상 일정

| Phase | 작업 | 시간 |
|-------|------|------|
| Phase 1 | 동적 라우팅 | 30분 |
| Phase 2 | 병렬 실행 | 20분 |
| 테스트 | 통합 테스트 | 20분 |
| **총계** | | **~1시간 10분** |

(Phase 3, 4는 선택사항)

---

## ✅ 완료 기준

### Phase 1 완료 조건:
- [ ] Reviewer 점수 < 5일 때 Analyzer로 복귀
- [ ] 복귀 횟수 2회 제한 (무한루프 방지)
- [ ] 로그에 "재분석 시작" 메시지 출력

### Phase 2 완료 조건:
- [ ] RAG와 웹검색이 동시 시작
- [ ] 실행 시간 20% 이상 단축
- [ ] 결과 정상 병합

---

## 📊 개선 전후 비교

### 변경 전:
```
┌───────────────────────────────────────────────────────┐
│     Analyzer → Structurer → Writer → Reviewer        │
│                                          ↓            │
│                               Refiner → Formatter     │
│                                                       │
│  (단순 파이프라인, 고정 흐름)                         │
└───────────────────────────────────────────────────────┘
```

### 변경 후:
```
┌───────────────────────────────────────────────────────┐
│  ┌─ RAG ────┐                                         │
│  │          ├──→ Analyzer → Structurer → Writer      │
│  └─ Web ────┘         ↑                    ↓          │
│                       │              ┌── Reviewer     │
│                       │              │     │          │
│                       └── score<5 ──┤  score≥9       │
│                                      │     │          │
│                              Refiner ←┘    ↓          │
│                                 │     Formatter       │
│                                 └────────→            │
│                                                       │
│  (동적 라우팅, 병렬 실행, 피드백 루프)               │
└───────────────────────────────────────────────────────┘
```

---

## 🚀 실행 명령

**계획서 승인 후 다음 명령으로 개선 시작:**

```
"Phase 1 동적 라우팅 확장 진행"
```

또는

```
"Phase 1 + Phase 2 진행"
```

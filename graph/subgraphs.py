"""
PlanCraft Agent - Sub-graph 정의 모듈

LangGraph 베스트 프랙티스에 따라 관련 노드들을 Sub-graph로 그룹화합니다.
각 Sub-graph는 명확한 책임을 가지며, 독립적으로 테스트/재사용 가능합니다.

Sub-graph 구조:
    1. Context Sub-graph: 정보 수집 (RAG + 웹 검색)
    2. Generation Sub-graph: 콘텐츠 생성 (분석 → 구조 → 작성)
    3. QA Sub-graph: 품질 관리 (검토 → 개선 → 포맷)

Best Practice:
    - 각 Sub-graph는 독립적으로 컴파일 가능
    - 메인 Graph에서 Sub-graph를 노드로 추가
    - 명확한 책임 분리로 유지보수성 향상
"""

from langgraph.graph import StateGraph, END
from graph.state import PlanCraftState
from agents import analyzer, structurer, writer, reviewer, refiner, formatter


# =============================================================================
# Context Sub-graph: 정보 수집 단계
# =============================================================================

def create_context_subgraph() -> StateGraph:
    """
    Context Sub-graph 생성
    
    책임: RAG 검색 + 조건부 웹 검색
    입력: user_input, file_content
    출력: rag_context, web_context
    """
    from graph.workflow import retrieve_context, fetch_web_context
    
    subgraph = StateGraph(PlanCraftState)
    
    # 노드 등록
    subgraph.add_node("rag_retrieve", retrieve_context)
    subgraph.add_node("web_fetch", fetch_web_context)
    
    # 흐름 정의: RAG → 웹 검색 (순차)
    subgraph.set_entry_point("rag_retrieve")
    subgraph.add_edge("rag_retrieve", "web_fetch")
    subgraph.add_edge("web_fetch", END)
    
    return subgraph


# =============================================================================
# Generation Sub-graph: 콘텐츠 생성 단계
# =============================================================================

def create_generation_subgraph() -> StateGraph:
    """
    Generation Sub-graph 생성
    
    책임: 분석 → 구조 설계 → 초안 작성
    입력: rag_context, web_context, user_input
    출력: analysis, structure, draft
    """
    subgraph = StateGraph(PlanCraftState)
    
    # 노드 등록
    subgraph.add_node("analyze", analyzer.run)
    subgraph.add_node("structure", structurer.run)
    subgraph.add_node("write", writer.run)
    
    # 흐름 정의
    subgraph.set_entry_point("analyze")
    subgraph.add_edge("analyze", "structure")
    subgraph.add_edge("structure", "write")
    subgraph.add_edge("write", END)
    
    return subgraph


# =============================================================================
# QA Sub-graph: 품질 관리 단계
# =============================================================================

def create_qa_subgraph() -> StateGraph:
    """
    QA (Quality Assurance) Sub-graph 생성
    
    책임: 검토 → 개선 → 최종 포맷팅
    입력: draft
    출력: review, final_output, chat_summary
    """
    subgraph = StateGraph(PlanCraftState)
    
    # 노드 등록
    subgraph.add_node("review", reviewer.run)
    subgraph.add_node("refine", refiner.run)
    subgraph.add_node("format", formatter.run)
    
    # 흐름 정의
    subgraph.set_entry_point("review")
    subgraph.add_edge("review", "refine")
    subgraph.add_edge("refine", "format")
    subgraph.add_edge("format", END)
    
    return subgraph


# =============================================================================
# Sub-graph 컴파일 (독립 테스트용)
# =============================================================================

def get_context_app():
    """Context Sub-graph 컴파일된 앱 반환"""
    return create_context_subgraph().compile()


def get_generation_app():
    """Generation Sub-graph 컴파일된 앱 반환"""
    return create_generation_subgraph().compile()


def get_qa_app():
    """QA Sub-graph 컴파일된 앱 반환"""
    return create_qa_subgraph().compile()


# =============================================================================
# Sub-graph 실행 래퍼 (메인 Graph에서 노드로 사용)
# =============================================================================

def run_context_subgraph(state: PlanCraftState) -> PlanCraftState:
    """
    컨텍스트 수집 서브그래프 (Context Sub-graph)
    
    [PHASE 2] RAG 검색과 웹 검색을 병렬로 수행하여 성능 향상
    
    변경 전: RAG → Web (순차, ~5초)
    변경 후: RAG + Web (병렬, ~3초)
    """
    from graph.workflow import retrieve_context, fetch_web_context
    from graph.state import update_state
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time
    
    # 1. 초기 상태 로깅
    current_history = state.get("step_history", []) or []
    print(f"[Subgraph] 병렬 Context Gathering Started")
    start_time = time.time()
    
    # =========================================================================
    # [PHASE 2] 병렬 실행: RAG + 웹검색 동시 수행
    # =========================================================================
    rag_result = None
    web_result = None
    
    def run_rag():
        return retrieve_context(state)
    
    def run_web():
        return fetch_web_context(state)
    
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            rag_future = executor.submit(run_rag)
            web_future = executor.submit(run_web)
            
            # 결과 수집
            rag_result = rag_future.result(timeout=30)
            web_result = web_future.result(timeout=30)
            
    except Exception as e:
        print(f"[Subgraph] 병렬 실행 실패, 순차 실행으로 전환: {e}")
        # Fallback: 순차 실행
        rag_result = retrieve_context(state)
        web_result = fetch_web_context(rag_result)
    
    elapsed = time.time() - start_time
    print(f"[Subgraph] Context Gathering 완료 ({elapsed:.2f}초)")
    
    # 3. 결과 병합
    updates = {
        "rag_context": rag_result.get("rag_context") if rag_result else None,
        "web_context": web_result.get("web_context") if web_result else None,
        "web_urls": web_result.get("web_urls") if web_result else None,
        "current_step": "context_gathering",
        # History 병합 (둘 다 합침)
        "step_history": (rag_result.get("step_history") or []) + 
                       [h for h in (web_result.get("step_history") or []) 
                        if h not in (rag_result.get("step_history") or [])]
    }
    
    return update_state(state, **updates)


def run_generation_subgraph(state: PlanCraftState) -> PlanCraftState:
    """생성 서브그래프 (분석 -> 구조화 -> 작성)"""
    from graph.workflow import run_analyzer_node, run_structurer_node, run_writer_node
    from graph.state import update_state
    
    s1 = run_analyzer_node(state)
    
    # 분기 로직 처리 (Interrupt 등)은 Main Graph에서 담당하므로
    # 여기서는 순차적으로 Happy Path만 시뮬레이션하거나, 
    # 실제로는 Graph를 리턴해야 함. (구조 변경 필요)
    
    # 현재 구조상 함수 직접 호출로 진행
    if s1.get("need_more_info"):
        return s1 # 인터럽트 필요 시 바로 반환
        
    s2 = run_structurer_node(s1)
    s3 = run_writer_node(s2)
    
    return s3


def run_qa_subgraph(state: PlanCraftState) -> PlanCraftState:
    """QA 서브그래프 (검토 -> 개선 -> 포맷)"""
    from graph.workflow import run_reviewer_node, run_refiner_node, run_formatter_node
    
    s1 = run_reviewer_node(state)
    s2 = run_refiner_node(s1)
    s3 = run_formatter_node(s2)
    
    return s3

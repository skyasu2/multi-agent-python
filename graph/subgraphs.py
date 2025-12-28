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
    
    RAG 검색과 웹 검색을 병렬(또는 순차)로 수행하여 컨텍스트를 풍부하게 만듭니다.
    LangGraph에서는 같은 State를 공유하는 노드들을 묶어 Sub-graph로 구성할 수 있습니다.
    """
    from graph.workflow import retrieve_context, fetch_web_context
    from graph.state import update_state
    
    # 1. 초기 상태 로깅
    current_history = state.get("step_history", []) or []
    base_len = len(current_history)
    print(f"[Subgraph] Context Gathering Started (History: {base_len} steps)")
    
    # 2. 노드 실행 (순차 실행 예시)
    
    # Retrieve 수행
    state_after_rag = retrieve_context(state)
    
    # Web Fetch 수행
    state_after_web = fetch_web_context(state_after_rag)
    
    # 3. 결과 집계 및 반환
    
    # 업데이트할 필드 추출
    updates = {
        "rag_context": state_after_web.get("rag_context"),
        "web_context": state_after_web.get("web_context"),
        "web_urls": state_after_web.get("web_urls"),
        "current_step": "context_gathering",
        # History 병합
        "step_history": state_after_web.get("step_history")
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
